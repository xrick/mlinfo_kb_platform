"""
PromptRenderer - 提示渲染器
安全且高效的提示模板渲染，支援動態變數替換和模板片段組合

主要功能：
1. 安全的變數替換（防止注入攻擊）
2. 多層變數解析（全域 + 上下文變數）
3. 條件渲染和邏輯處理
4. 提示片段組合
5. 格式化和清理
6. 渲染緩存和性能優化
"""

import re
import json
import logging
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from string import Template
import html
import urllib.parse

logger = logging.getLogger(__name__)


@dataclass
class RenderContext:
    """渲染上下文"""
    variables: Dict[str, Any]              # 渲染變數
    global_variables: Dict[str, Any]       # 全域變數
    user_profile: Dict[str, Any]           # 用戶資料
    conversation_context: Dict[str, Any]   # 對話上下文
    system_info: Dict[str, Any]            # 系統信息
    render_options: Dict[str, Any]         # 渲染選項


@dataclass
class RenderResult:
    """渲染結果"""
    success: bool                          # 渲染是否成功
    rendered_content: Optional[str]        # 渲染後的內容
    original_template: str                 # 原始模板
    variables_used: List[str]              # 使用的變數列表
    missing_variables: List[str]           # 缺失的變數列表
    render_time_ms: float                  # 渲染耗時（毫秒）
    error_message: Optional[str]           # 錯誤信息
    cache_hit: bool = False                # 是否命中緩存
    template_hash: str = ""                # 模板雜湊值


class PromptRendererError(Exception):
    """提示渲染器相關錯誤"""
    pass


class PromptRenderer:
    """
    提示渲染器
    
    提供安全、高效的提示模板渲染功能
    """
    
    def __init__(self, 
                 enable_cache: bool = True,
                 cache_max_size: int = 1000,
                 strict_mode: bool = True):
        """
        初始化提示渲染器
        
        Args:
            enable_cache: 是否啟用渲染緩存
            cache_max_size: 緩存最大條目數
            strict_mode: 嚴格模式，缺失變數時是否報錯
        """
        self.enable_cache = enable_cache
        self.cache_max_size = cache_max_size
        self.strict_mode = strict_mode
        
        # 渲染緩存
        self.render_cache: Dict[str, RenderResult] = {}
        self.cache_access_times: Dict[str, datetime] = {}
        
        # 全域變數
        self.global_variables = self._initialize_global_variables()
        
        # 安全設定
        self.allowed_functions = {
            'len', 'str', 'int', 'float', 'bool',
            'upper', 'lower', 'title', 'strip',
            'replace', 'format'
        }
        
        # 變數模式
        self.variable_patterns = {
            'curly': re.compile(r'\{([^}]+)\}'),           # {variable}
            'dollar': re.compile(r'\$\{([^}]+)\}'),       # ${variable}
            'percent': re.compile(r'%\{([^}]+)\}'),       # %{variable}
            'double_curly': re.compile(r'\{\{([^}]+)\}\}') # {{variable}}
        }
        
        # 條件渲染模式
        self.condition_pattern = re.compile(
            r'\{%\s*if\s+([^%]+)\s*%\}(.*?)\{%\s*endif\s*%\}',
            re.DOTALL
        )
        
        # 循環渲染模式
        self.loop_pattern = re.compile(
            r'\{%\s*for\s+(\w+)\s+in\s+([^%]+)\s*%\}(.*?)\{%\s*endfor\s*%\}',
            re.DOTALL
        )
        
        # 統計信息
        self.stats = {
            "total_renders": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "render_errors": 0,
            "average_render_time": 0.0,
            "variables_resolved": 0,
            "variables_missing": 0
        }
        
        logger.info("PromptRenderer 初始化完成")
    
    async def render(
        self, 
        template: str, 
        context: RenderContext
    ) -> RenderResult:
        """
        渲染提示模板
        
        Args:
            template: 提示模板
            context: 渲染上下文
            
        Returns:
            渲染結果
        """
        start_time = datetime.now()
        
        try:
            # 生成模板雜湊（用於緩存）
            template_hash = self._generate_template_hash(template, context)
            
            # 檢查緩存
            if self.enable_cache and template_hash in self.render_cache:
                cached_result = self.render_cache[template_hash].copy()
                cached_result.cache_hit = True
                self.stats["cache_hits"] += 1
                self.stats["total_renders"] += 1
                self._update_cache_access_time(template_hash)
                return cached_result
            
            # 執行渲染
            render_result = await self._execute_render(template, context, template_hash)
            
            # 計算渲染時間
            end_time = datetime.now()
            render_result.render_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # 更新統計
            await self._update_render_stats(render_result)
            
            # 存入緩存
            if self.enable_cache and render_result.success:
                await self._cache_render_result(template_hash, render_result)
            
            return render_result
            
        except Exception as e:
            logger.error(f"渲染提示失敗: {e}", exc_info=True)
            
            end_time = datetime.now()
            return RenderResult(
                success=False,
                rendered_content=None,
                original_template=template,
                variables_used=[],
                missing_variables=[],
                render_time_ms=(end_time - start_time).total_seconds() * 1000,
                error_message=str(e),
                cache_hit=False,
                template_hash=""
            )
    
    async def _execute_render(
        self, 
        template: str, 
        context: RenderContext,
        template_hash: str
    ) -> RenderResult:
        """
        執行實際的渲染過程
        """
        # 準備所有變數
        all_variables = self._prepare_all_variables(context)
        
        # 追蹤使用的和缺失的變數
        variables_used = []
        missing_variables = []
        
        # 執行渲染步驟
        rendered_content = template
        
        # 1. 處理條件渲染
        rendered_content = await self._process_conditions(
            rendered_content, 
            all_variables,
            variables_used,
            missing_variables
        )
        
        # 2. 處理循環渲染
        rendered_content = await self._process_loops(
            rendered_content,
            all_variables,
            variables_used,
            missing_variables
        )
        
        # 3. 處理基本變數替換
        rendered_content = await self._process_variables(
            rendered_content,
            all_variables,
            variables_used,
            missing_variables
        )
        
        # 4. 後處理清理
        rendered_content = self._post_process_content(rendered_content)
        
        # 檢查嚴格模式
        if self.strict_mode and missing_variables:
            return RenderResult(
                success=False,
                rendered_content=None,
                original_template=template,
                variables_used=variables_used,
                missing_variables=missing_variables,
                render_time_ms=0.0,
                error_message=f"嚴格模式下發現缺失變數: {missing_variables}",
                cache_hit=False,
                template_hash=template_hash
            )
        
        return RenderResult(
            success=True,
            rendered_content=rendered_content,
            original_template=template,
            variables_used=variables_used,
            missing_variables=missing_variables,
            render_time_ms=0.0,  # 會在外層設定
            error_message=None,
            cache_hit=False,
            template_hash=template_hash
        )
    
    def _prepare_all_variables(self, context: RenderContext) -> Dict[str, Any]:
        """準備所有可用的變數"""
        all_variables = {}
        
        # 按優先級順序合併變數
        all_variables.update(self.global_variables)
        all_variables.update(context.system_info or {})
        all_variables.update(context.user_profile or {})
        all_variables.update(context.conversation_context or {})
        all_variables.update(context.global_variables or {})
        all_variables.update(context.variables or {})
        
        # 添加一些計算變數
        all_variables.update({
            'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current_date': datetime.now().strftime('%Y-%m-%d'),
            'timestamp': datetime.now().isoformat()
        })
        
        return all_variables
    
    async def _process_conditions(
        self,
        content: str,
        variables: Dict[str, Any],
        variables_used: List[str],
        missing_variables: List[str]
    ) -> str:
        """
        處理條件渲染
        
        支援語法: {% if condition %}content{% endif %}
        """
        def replace_condition(match):
            condition_expr = match.group(1).strip()
            condition_content = match.group(2)
            
            try:
                # 安全評估條件表達式
                if self._evaluate_condition(condition_expr, variables, variables_used, missing_variables):
                    return condition_content
                else:
                    return ""
            except Exception as e:
                logger.warning(f"條件評估失敗: {condition_expr} - {e}")
                return ""
        
        return self.condition_pattern.sub(replace_condition, content)
    
    async def _process_loops(
        self,
        content: str,
        variables: Dict[str, Any],
        variables_used: List[str],
        missing_variables: List[str]
    ) -> str:
        """
        處理循環渲染
        
        支援語法: {% for item in items %}{{ item }}{% endfor %}
        """
        def replace_loop(match):
            item_var = match.group(1)
            items_expr = match.group(2).strip()
            loop_content = match.group(3)
            
            try:
                # 獲取要循環的項目
                items = self._resolve_variable(items_expr, variables, variables_used, missing_variables)
                
                if not isinstance(items, (list, tuple)):
                    return ""
                
                # 渲染每個項目
                rendered_parts = []
                for item in items:
                    # 創建循環上下文
                    loop_variables = variables.copy()
                    loop_variables[item_var] = item
                    
                    # 渲染循環內容
                    rendered_part = self._replace_simple_variables(loop_content, loop_variables, variables_used, missing_variables)
                    rendered_parts.append(rendered_part)
                
                return "".join(rendered_parts)
                
            except Exception as e:
                logger.warning(f"循環渲染失敗: {items_expr} - {e}")
                return ""
        
        return self.loop_pattern.sub(replace_loop, content)
    
    async def _process_variables(
        self,
        content: str,
        variables: Dict[str, Any],
        variables_used: List[str],
        missing_variables: List[str]
    ) -> str:
        """處理基本變數替換"""
        # 處理各種變數格式
        for pattern_name, pattern in self.variable_patterns.items():
            content = self._replace_variables_by_pattern(
                content, 
                pattern, 
                variables, 
                variables_used, 
                missing_variables
            )
        
        return content
    
    def _replace_variables_by_pattern(
        self,
        content: str,
        pattern: re.Pattern,
        variables: Dict[str, Any],
        variables_used: List[str],
        missing_variables: List[str]
    ) -> str:
        """根據指定模式替換變數"""
        def replace_variable(match):
            var_expr = match.group(1).strip()
            
            try:
                value = self._resolve_variable(var_expr, variables, variables_used, missing_variables)
                return self._format_value(value)
            except KeyError:
                if var_expr not in missing_variables:
                    missing_variables.append(var_expr)
                # 在非嚴格模式下，保留原始占位符
                return match.group(0) if not self.strict_mode else ""
            except Exception as e:
                logger.warning(f"變數解析失敗: {var_expr} - {e}")
                return match.group(0) if not self.strict_mode else ""
        
        return pattern.sub(replace_variable, content)
    
    def _replace_simple_variables(
        self,
        content: str,
        variables: Dict[str, Any],
        variables_used: List[str],
        missing_variables: List[str]
    ) -> str:
        """簡單變數替換（用於循環內容）"""
        # 只處理雙大括號格式
        pattern = self.variable_patterns['double_curly']
        return self._replace_variables_by_pattern(content, pattern, variables, variables_used, missing_variables)
    
    def _resolve_variable(
        self,
        var_expr: str,
        variables: Dict[str, Any],
        variables_used: List[str],
        missing_variables: List[str]
    ) -> Any:
        """
        解析變數表達式
        
        支援：
        - 簡單變數: user_name
        - 嵌套屬性: user.profile.name
        - 字典鍵: user['name']
        - 列表索引: items[0]
        """
        # 記錄變數使用
        if var_expr not in variables_used:
            variables_used.append(var_expr)
        
        # 處理簡單變數
        if var_expr in variables:
            return variables[var_expr]
        
        # 處理點號分隔的嵌套屬性
        if '.' in var_expr and '[' not in var_expr:
            parts = var_expr.split('.')
            value = variables
            
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                elif hasattr(value, part):
                    value = getattr(value, part)
                else:
                    raise KeyError(f"找不到變數: {var_expr}")
            
            return value
        
        # 處理方括號索引
        if '[' in var_expr and ']' in var_expr:
            # 簡單處理，只支援一層索引
            base_var = var_expr.split('[')[0]
            index_part = var_expr[var_expr.index('[') + 1:var_expr.rindex(']')]
            
            if base_var not in variables:
                raise KeyError(f"找不到基礎變數: {base_var}")
            
            base_value = variables[base_var]
            
            # 嘗試作為字符串鍵
            if isinstance(base_value, dict):
                index_key = index_part.strip('\'"')
                if index_key in base_value:
                    return base_value[index_key]
            
            # 嘗試作為數字索引
            try:
                index = int(index_part)
                if isinstance(base_value, (list, tuple)) and 0 <= index < len(base_value):
                    return base_value[index]
            except ValueError:
                pass
            
            raise KeyError(f"無效的索引: {var_expr}")
        
        # 變數不存在
        raise KeyError(f"找不到變數: {var_expr}")
    
    def _evaluate_condition(
        self,
        condition_expr: str,
        variables: Dict[str, Any],
        variables_used: List[str],
        missing_variables: List[str]
    ) -> bool:
        """
        安全評估條件表達式
        
        支援的操作：
        - 存在性檢查: var_name
        - 相等比較: var_name == 'value'
        - 不等比較: var_name != 'value'
        - 包含檢查: 'value' in var_name
        """
        condition_expr = condition_expr.strip()
        
        # 簡單的存在性檢查
        if condition_expr in variables:
            if condition_expr not in variables_used:
                variables_used.append(condition_expr)
            value = variables[condition_expr]
            return bool(value) and value != "" and value is not None
        
        # 相等比較
        if '==' in condition_expr:
            left, right = condition_expr.split('==', 1)
            left = left.strip()
            right = right.strip().strip('\'"')
            
            try:
                left_value = self._resolve_variable(left, variables, variables_used, missing_variables)
                return str(left_value) == right
            except KeyError:
                return False
        
        # 不等比較
        if '!=' in condition_expr:
            left, right = condition_expr.split('!=', 1)
            left = left.strip()
            right = right.strip().strip('\'"')
            
            try:
                left_value = self._resolve_variable(left, variables, variables_used, missing_variables)
                return str(left_value) != right
            except KeyError:
                return True  # 不存在的變數視為不等於任何值
        
        # 包含檢查
        if ' in ' in condition_expr:
            parts = condition_expr.split(' in ')
            if len(parts) == 2:
                value = parts[0].strip().strip('\'"')
                container_var = parts[1].strip()
                
                try:
                    container = self._resolve_variable(container_var, variables, variables_used, missing_variables)
                    if isinstance(container, str):
                        return value in container
                    elif isinstance(container, (list, tuple)):
                        return value in [str(item) for item in container]
                    elif isinstance(container, dict):
                        return value in container
                except KeyError:
                    return False
        
        # 默認為 False
        return False
    
    def _format_value(self, value: Any) -> str:
        """格式化變數值為字符串"""
        if value is None:
            return ""
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        else:
            return str(value)
    
    def _post_process_content(self, content: str) -> str:
        """後處理清理渲染內容"""
        # 移除多餘的空行
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # 清理行首尾空白
        lines = content.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]
        content = '\n'.join(cleaned_lines)
        
        # 移除開頭和結尾的空行
        content = content.strip()
        
        return content
    
    def _generate_template_hash(self, template: str, context: RenderContext) -> str:
        """生成模板雜湊值（用於緩存鍵）"""
        # 包含模板內容和關鍵變數
        hash_content = template
        
        # 添加影響渲染結果的關鍵變數
        if context.variables:
            hash_content += json.dumps(context.variables, sort_keys=True)
        
        if context.global_variables:
            hash_content += json.dumps(context.global_variables, sort_keys=True)
        
        return hashlib.md5(hash_content.encode('utf-8')).hexdigest()
    
    async def _cache_render_result(self, template_hash: str, result: RenderResult):
        """緩存渲染結果"""
        # 檢查緩存大小限制
        if len(self.render_cache) >= self.cache_max_size:
            await self._evict_old_cache_entries()
        
        # 存儲結果
        self.render_cache[template_hash] = result
        self.cache_access_times[template_hash] = datetime.now()
    
    async def _evict_old_cache_entries(self):
        """清理舊的緩存條目"""
        # 按訪問時間排序，移除最舊的 20%
        sorted_entries = sorted(
            self.cache_access_times.items(),
            key=lambda x: x[1]
        )
        
        evict_count = max(1, len(sorted_entries) // 5)  # 移除 20%
        
        for i in range(evict_count):
            template_hash = sorted_entries[i][0]
            if template_hash in self.render_cache:
                del self.render_cache[template_hash]
            if template_hash in self.cache_access_times:
                del self.cache_access_times[template_hash]
        
        logger.debug(f"清理了 {evict_count} 個舊緩存條目")
    
    def _update_cache_access_time(self, template_hash: str):
        """更新緩存訪問時間"""
        self.cache_access_times[template_hash] = datetime.now()
    
    async def _update_render_stats(self, result: RenderResult):
        """更新渲染統計"""
        self.stats["total_renders"] += 1
        
        if not result.success:
            self.stats["render_errors"] += 1
        
        if result.cache_hit:
            self.stats["cache_hits"] += 1
        else:
            self.stats["cache_misses"] += 1
        
        # 更新平均渲染時間
        total_time = (
            self.stats["average_render_time"] * (self.stats["total_renders"] - 1) +
            result.render_time_ms
        )
        self.stats["average_render_time"] = total_time / self.stats["total_renders"]
        
        # 更新變數統計
        self.stats["variables_resolved"] += len(result.variables_used)
        self.stats["variables_missing"] += len(result.missing_variables)
    
    def _initialize_global_variables(self) -> Dict[str, Any]:
        """初始化全域變數"""
        return {
            # 系統信息
            "system_name": "MGFD Sales Assistant",
            "system_version": "2.0.0",
            "company_name": "Your Company",
            
            # 時間相關
            "current_year": datetime.now().year,
            "current_month": datetime.now().month,
            "current_day": datetime.now().day,
            
            # 常用常量
            "empty_string": "",
            "line_break": "\n",
            "tab": "\t",
            
            # 預設回應
            "default_greeting": "您好！歡迎使用我們的筆電選購助手。",
            "default_apology": "抱歉，我現在無法處理您的請求。",
            "contact_info": "如需進一步協助，請聯繫客服。"
        }
    
    async def render_with_fallback(
        self,
        primary_template: str,
        fallback_template: str,
        context: RenderContext
    ) -> RenderResult:
        """
        帶回退的渲染
        
        如果主模板渲染失敗，自動使用回退模板
        """
        # 嘗試渲染主模板
        primary_result = await self.render(primary_template, context)
        
        if primary_result.success:
            return primary_result
        
        # 主模板失敗，使用回退模板
        logger.info(f"主模板渲染失敗，使用回退模板: {primary_result.error_message}")
        
        fallback_result = await self.render(fallback_template, context)
        
        # 標記為回退結果
        if fallback_result.success:
            fallback_result.rendered_content = (
                f"<!-- 回退模板 -->\n{fallback_result.rendered_content}"
            )
        
        return fallback_result
    
    async def validate_template(self, template: str) -> Dict[str, Any]:
        """
        驗證模板語法
        
        Args:
            template: 要驗證的模板
            
        Returns:
            驗證結果
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "variables_found": [],
            "conditions_found": [],
            "loops_found": []
        }
        
        try:
            # 檢查變數語法
            for pattern_name, pattern in self.variable_patterns.items():
                matches = pattern.findall(template)
                for match in matches:
                    validation_result["variables_found"].append({
                        "variable": match,
                        "pattern": pattern_name
                    })
            
            # 檢查條件語法
            condition_matches = self.condition_pattern.findall(template)
            for match in condition_matches:
                validation_result["conditions_found"].append({
                    "condition": match[0],
                    "content_length": len(match[1])
                })
            
            # 檢查循環語法
            loop_matches = self.loop_pattern.findall(template)
            for match in loop_matches:
                validation_result["loops_found"].append({
                    "item_var": match[0],
                    "items_expr": match[1],
                    "content_length": len(match[2])
                })
            
            # 檢查語法錯誤
            # 不匹配的條件標籤
            if_count = len(re.findall(r'\{%\s*if\s+', template))
            endif_count = len(re.findall(r'\{%\s*endif\s*%\}', template))
            if if_count != endif_count:
                validation_result["valid"] = False
                validation_result["errors"].append(
                    f"條件標籤不匹配: {if_count} if, {endif_count} endif"
                )
            
            # 不匹配的循環標籤
            for_count = len(re.findall(r'\{%\s*for\s+', template))
            endfor_count = len(re.findall(r'\{%\s*endfor\s*%\}', template))
            if for_count != endfor_count:
                validation_result["valid"] = False
                validation_result["errors"].append(
                    f"循環標籤不匹配: {for_count} for, {endfor_count} endfor"
                )
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"驗證過程發生錯誤: {str(e)}")
        
        return validation_result
    
    def clear_cache(self):
        """清空渲染緩存"""
        self.render_cache.clear()
        self.cache_access_times.clear()
        logger.info("渲染緩存已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取渲染器統計信息"""
        stats = self.stats.copy()
        
        # 添加緩存統計
        stats["cache_size"] = len(self.render_cache)
        stats["cache_max_size"] = self.cache_max_size
        
        if stats["total_renders"] > 0:
            stats["cache_hit_rate"] = stats["cache_hits"] / stats["total_renders"]
            stats["error_rate"] = stats["render_errors"] / stats["total_renders"]
        else:
            stats["cache_hit_rate"] = 0.0
            stats["error_rate"] = 0.0
        
        stats["timestamp"] = datetime.now().isoformat()
        
        return stats
    
    async def preload_templates(self, templates: Dict[str, str], base_context: RenderContext):
        """
        預載入模板到緩存
        
        Args:
            templates: 模板字典 {template_id: template_content}
            base_context: 基礎渲染上下文
        """
        preloaded = 0
        errors = 0
        
        for template_id, template_content in templates.items():
            try:
                result = await self.render(template_content, base_context)
                if result.success:
                    preloaded += 1
                else:
                    errors += 1
                    logger.warning(f"預載入模板失敗: {template_id} - {result.error_message}")
            except Exception as e:
                errors += 1
                logger.error(f"預載入模板錯誤: {template_id} - {e}")
        
        logger.info(f"模板預載入完成: 成功 {preloaded}, 失敗 {errors}")
        
        return {
            "preloaded": preloaded,
            "errors": errors,
            "total": len(templates)
        }