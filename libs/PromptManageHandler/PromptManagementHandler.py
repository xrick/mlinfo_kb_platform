"""
PromptManagementHandler - 提示管理主處理器
統一的提示工程管理入口，整合提示註冊、選擇和渲染功能

主要功能：
1. 統一的提示管理接口
2. 智能提示選擇和渲染
3. 與狀態機深度整合
4. 性能監控和統計
5. 標準動作合約支援
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import asyncio

from .PromptRegistry import PromptRegistry, PromptMetadata
from .PromptSelector import PromptSelector, SelectionCriteria, SelectionStrategy, SelectionResult
from .PromptRenderer import PromptRenderer, RenderContext, RenderResult

logger = logging.getLogger(__name__)


class PromptManagementHandler:
    """
    提示管理主處理器
    
    統一管理提示的整個生命週期：註冊 -> 選擇 -> 渲染 -> 回應
    與 MGFD 狀態機系統深度整合
    """
    
    def __init__(self, 
                 prompts_base_dir: str = None,
                 enable_cache: bool = True,
                 auto_reload: bool = True):
        """
        初始化提示管理處理器
        
        Args:
            prompts_base_dir: 提示基礎目錄
            enable_cache: 是否啟用緩存
            auto_reload: 是否自動重載提示
        """
        # 初始化各個組件
        self.registry = PromptRegistry(
            prompts_base_dir=prompts_base_dir,
            auto_reload=auto_reload
        )
        self.selector = PromptSelector(self.registry)
        self.renderer = PromptRenderer(enable_cache=enable_cache)
        
        # 系統狀態
        self.is_initialized = False
        self.initialization_error = None
        
        # 統計信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "state_usage": {},
            "intent_usage": {},
            "prompt_usage": {},
            "error_types": {}
        }
        
        logger.info("PromptManagementHandler 初始化完成")
    
    async def initialize(self) -> Dict[str, Any]:
        """
        初始化提示管理系統
        
        Returns:
            初始化結果
        """
        try:
            logger.info("開始初始化提示管理系統...")
            
            # 初始化提示註冊中心
            registry_result = await self.registry.initialize()
            
            if not registry_result["success"]:
                self.initialization_error = f"註冊中心初始化失敗: {registry_result.get('error', 'Unknown error')}"
                logger.error(self.initialization_error)
                return {
                    "success": False,
                    "error": self.initialization_error,
                    "component": "registry"
                }
            
            # 預載入常用模板到渲染器緩存
            await self._preload_common_templates()
            
            self.is_initialized = True
            
            result = {
                "success": True,
                "prompts_loaded": registry_result["prompts_loaded"],
                "active_prompts": registry_result["active_prompts"],
                "categories": registry_result["categories"],
                "message": "提示管理系統初始化成功"
            }
            
            logger.info(f"提示管理系統初始化成功，載入 {result['prompts_loaded']} 個提示")
            return result
            
        except Exception as e:
            self.initialization_error = str(e)
            logger.error(f"初始化提示管理系統失敗: {e}", exc_info=True)
            return {
                "success": False,
                "error": self.initialization_error,
                "component": "system"
            }
    
    async def process_prompt_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理提示請求 - 標準動作合約
        
        這是與狀態管理系統集成的主要接口
        
        Args:
            context: 請求上下文，包含狀態、意圖、用戶信息等
            
        Returns:
            處理結果，包含選擇的提示和渲染內容
        """
        start_time = datetime.now()
        
        try:
            # 檢查初始化狀態
            if not self.is_initialized:
                return {
                    "success": False,
                    "error": "提示管理系統未初始化",
                    "initialization_error": self.initialization_error
                }
            
            # 解析請求上下文
            selection_criteria = self._parse_selection_criteria(context)
            render_context = self._parse_render_context(context)
            
            # 選擇提示
            selection_result = await self.selector.select_prompt(selection_criteria)
            
            if not selection_result.success:
                return await self._handle_selection_failure(selection_result, context)
            
            # 渲染提示
            render_result = await self.renderer.render(
                selection_result.prompt_content,
                render_context
            )
            
            if not render_result.success:
                return await self._handle_render_failure(render_result, selection_result, context)
            
            # 計算響應時間
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            # 更新統計
            await self._update_request_stats(context, selection_result, render_result, response_time)
            
            # 構建成功響應
            return {
                "success": True,
                "selected_prompt_id": selection_result.selected_prompt_id,
                "prompt_title": selection_result.metadata.title if selection_result.metadata else "",
                "rendered_prompt": render_result.rendered_content,
                "selection_reason": selection_result.selection_reason,
                "confidence_score": selection_result.confidence_score,
                "alternatives": selection_result.alternatives,
                "variables_used": render_result.variables_used,
                "missing_variables": render_result.missing_variables,
                "response_time_ms": response_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"處理提示請求失敗: {e}", exc_info=True)
            
            # 更新錯誤統計
            await self._update_error_stats(str(e))
            
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }
    
    async def select_prompt_for_state(
        self, 
        state: str, 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        為指定狀態選擇提示
        
        Args:
            state: 對話狀態
            context: 附加上下文
            
        Returns:
            選擇結果
        """
        try:
            # 構建選擇條件
            criteria = SelectionCriteria(
                state=state,
                intent=context.get("intent") if context else None,
                language=context.get("language", "zh-TW") if context else "zh-TW",
                user_profile=context.get("user_profile", {}) if context else {}
            )
            
            # 選擇提示
            result = await self.selector.select_prompt(criteria, SelectionStrategy.STATE_FIRST)
            
            if result.success:
                return {
                    "success": True,
                    "prompt_id": result.selected_prompt_id,
                    "prompt_content": result.prompt_content,
                    "metadata": asdict(result.metadata) if result.metadata else None,
                    "confidence": result.confidence_score,
                    "reason": result.selection_reason
                }
            else:
                return {
                    "success": False,
                    "error": "無法為指定狀態找到合適的提示",
                    "state": state
                }
                
        except Exception as e:
            logger.error(f"為狀態選擇提示失敗: {state} - {e}")
            return {
                "success": False,
                "error": str(e),
                "state": state
            }
    
    async def render_prompt_with_variables(
        self,
        prompt_id: str,
        variables: Dict[str, Any],
        global_vars: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        使用指定變數渲染提示
        
        Args:
            prompt_id: 提示ID
            variables: 渲染變數
            global_vars: 全域變數
            
        Returns:
            渲染結果
        """
        try:
            # 獲取提示內容
            prompt_content = await self.registry.get_prompt(prompt_id)
            if not prompt_content:
                return {
                    "success": False,
                    "error": f"找不到提示: {prompt_id}"
                }
            
            # 構建渲染上下文
            render_context = RenderContext(
                variables=variables,
                global_variables=global_vars or {},
                user_profile={},
                conversation_context={},
                system_info={},
                render_options={}
            )
            
            # 執行渲染
            result = await self.renderer.render(prompt_content, render_context)
            
            if result.success:
                return {
                    "success": True,
                    "rendered_content": result.rendered_content,
                    "variables_used": result.variables_used,
                    "missing_variables": result.missing_variables,
                    "render_time_ms": result.render_time_ms
                }
            else:
                return {
                    "success": False,
                    "error": result.error_message,
                    "missing_variables": result.missing_variables
                }
                
        except Exception as e:
            logger.error(f"渲染提示失敗: {prompt_id} - {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_prompt_recommendations(
        self,
        context: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        獲取提示推薦列表
        
        Args:
            context: 上下文信息
            limit: 推薦數量限制
            
        Returns:
            推薦提示列表
        """
        try:
            criteria = self._parse_selection_criteria(context)
            recommendations = await self.selector.recommend_prompts(criteria, limit)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"獲取提示推薦失敗: {e}")
            return []
    
    async def reload_prompts(self) -> Dict[str, Any]:
        """
        重載所有提示
        
        Returns:
            重載結果
        """
        try:
            result = await self.registry.reload_prompts()
            
            if result["success"]:
                # 重新預載入常用模板
                await self._preload_common_templates()
            
            return result
            
        except Exception as e:
            logger.error(f"重載提示失敗: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def register_dynamic_prompt(
        self,
        prompt_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        動態註冊新提示
        
        Args:
            prompt_id: 提示ID
            content: 提示內容
            metadata: 元數據
            
        Returns:
            註冊結果
        """
        try:
            result = await self.registry.register_prompt(prompt_id, content, metadata)
            return result
            
        except Exception as e:
            logger.error(f"動態註冊提示失敗: {prompt_id} - {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_selection_criteria(self, context: Dict[str, Any]) -> SelectionCriteria:
        """解析選擇條件"""
        return SelectionCriteria(
            state=context.get("stage") or context.get("state"),
            intent=context.get("intent"),
            category=context.get("prompt_category"),
            language=context.get("language", "zh-TW"),
            context_keywords=self._extract_keywords(context),
            user_profile=context.get("user_profile", {}),
            conversation_history=context.get("history", []),
            exclude_prompt_ids=context.get("exclude_prompts", [])
        )
    
    def _parse_render_context(self, context: Dict[str, Any]) -> RenderContext:
        """解析渲染上下文"""
        return RenderContext(
            variables=context.get("variables", {}),
            global_variables=context.get("global_variables", {}),
            user_profile=context.get("user_profile", {}),
            conversation_context={
                "session_id": context.get("session_id"),
                "stage": context.get("stage"),
                "intent": context.get("intent"),
                "confidence": context.get("confidence", 0.0),
                "user_message": context.get("user_message", ""),
                "slots": context.get("slots", {}),
                "history": context.get("history", [])
            },
            system_info={
                "timestamp": datetime.now().isoformat(),
                "system_version": "2.0.0"
            },
            render_options=context.get("render_options", {})
        )
    
    def _extract_keywords(self, context: Dict[str, Any]) -> List[str]:
        """從上下文提取關鍵詞"""
        keywords = []
        
        # 從用戶訊息提取
        user_message = context.get("user_message", "")
        if user_message:
            # 簡單的關鍵詞提取
            words = user_message.split()
            keywords.extend([word.strip('.,!?') for word in words if len(word) > 2])
        
        # 從槽位提取
        slots = context.get("slots", {})
        for slot_value in slots.values():
            if isinstance(slot_value, str) and len(slot_value) > 1:
                keywords.append(slot_value)
        
        return keywords[:10]  # 限制關鍵詞數量
    
    async def _handle_selection_failure(
        self,
        selection_result: SelectionResult,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """處理選擇失敗"""
        logger.warning(f"提示選擇失敗: {selection_result.selection_reason}")
        
        # 嘗試使用回退策略
        fallback_criteria = SelectionCriteria(
            state="DEFAULT",
            language="zh-TW"
        )
        
        fallback_result = await self.selector.select_prompt(
            fallback_criteria, 
            SelectionStrategy.STATE_FIRST
        )
        
        if fallback_result.success:
            return {
                "success": True,
                "selected_prompt_id": fallback_result.selected_prompt_id,
                "rendered_prompt": fallback_result.prompt_content,
                "is_fallback": True,
                "fallback_reason": selection_result.selection_reason,
                "confidence_score": 0.3  # 低置信度
            }
        
        return {
            "success": False,
            "error": "提示選擇失敗且回退策略無效",
            "selection_reason": selection_result.selection_reason
        }
    
    async def _handle_render_failure(
        self,
        render_result: RenderResult,
        selection_result: SelectionResult,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """處理渲染失敗"""
        logger.warning(f"提示渲染失敗: {render_result.error_message}")
        
        # 返回未渲染的原始提示
        return {
            "success": True,
            "selected_prompt_id": selection_result.selected_prompt_id,
            "rendered_prompt": selection_result.prompt_content,
            "render_error": render_result.error_message,
            "missing_variables": render_result.missing_variables,
            "is_raw_template": True,
            "confidence_score": selection_result.confidence_score * 0.5
        }
    
    async def _preload_common_templates(self):
        """預載入常用模板"""
        try:
            # 獲取高優先級的提示
            common_templates = {}
            
            for prompt_id, metadata in self.registry.metadata_cache.items():
                if metadata.priority >= 8 and metadata.is_active:
                    prompt_content = await self.registry.get_prompt(prompt_id)
                    if prompt_content:
                        common_templates[prompt_id] = prompt_content
            
            if common_templates:
                # 使用基礎上下文預載入
                base_context = RenderContext(
                    variables={},
                    global_variables={},
                    user_profile={},
                    conversation_context={},
                    system_info={},
                    render_options={}
                )
                
                result = await self.renderer.preload_templates(common_templates, base_context)
                logger.info(f"預載入常用模板: {result}")
                
        except Exception as e:
            logger.warning(f"預載入常用模板失敗: {e}")
    
    async def _update_request_stats(
        self,
        context: Dict[str, Any],
        selection_result: SelectionResult,
        render_result: RenderResult,
        response_time: float
    ):
        """更新請求統計"""
        self.stats["total_requests"] += 1
        self.stats["successful_requests"] += 1
        
        # 更新平均響應時間
        total_time = (
            self.stats["average_response_time"] * (self.stats["total_requests"] - 1) +
            response_time
        )
        self.stats["average_response_time"] = total_time / self.stats["total_requests"]
        
        # 更新狀態使用統計
        state = context.get("stage") or context.get("state")
        if state:
            if state not in self.stats["state_usage"]:
                self.stats["state_usage"][state] = 0
            self.stats["state_usage"][state] += 1
        
        # 更新意圖使用統計
        intent = context.get("intent")
        if intent:
            if intent not in self.stats["intent_usage"]:
                self.stats["intent_usage"][intent] = 0
            self.stats["intent_usage"][intent] += 1
        
        # 更新提示使用統計
        prompt_id = selection_result.selected_prompt_id
        if prompt_id:
            if prompt_id not in self.stats["prompt_usage"]:
                self.stats["prompt_usage"][prompt_id] = 0
            self.stats["prompt_usage"][prompt_id] += 1
    
    async def _update_error_stats(self, error_message: str):
        """更新錯誤統計"""
        self.stats["total_requests"] += 1
        self.stats["failed_requests"] += 1
        
        # 分類錯誤類型
        error_type = "unknown"
        if "初始化" in error_message:
            error_type = "initialization"
        elif "選擇" in error_message:
            error_type = "selection"
        elif "渲染" in error_message:
            error_type = "rendering"
        elif "找不到" in error_message:
            error_type = "not_found"
        
        if error_type not in self.stats["error_types"]:
            self.stats["error_types"][error_type] = 0
        self.stats["error_types"][error_type] += 1
    
    async def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        try:
            # 獲取各組件狀態
            registry_health = await self.registry.health_check()
            registry_stats = self.registry.get_stats()
            selector_stats = self.selector.get_selection_stats()
            renderer_stats = self.renderer.get_stats()
            
            return {
                "system_healthy": self.is_initialized and registry_health["healthy"],
                "initialization_error": self.initialization_error,
                "components": {
                    "registry": {
                        "healthy": registry_health["healthy"],
                        "stats": registry_stats
                    },
                    "selector": {
                        "healthy": True,
                        "stats": selector_stats
                    },
                    "renderer": {
                        "healthy": True,
                        "stats": renderer_stats
                    }
                },
                "overall_stats": self.stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"獲取系統狀態失敗: {e}")
            return {
                "system_healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查 - 簡化版本"""
        try:
            is_healthy = (
                self.is_initialized and 
                len(self.registry.prompts_cache) > 0
            )
            
            return {
                "healthy": is_healthy,
                "initialized": self.is_initialized,
                "prompts_loaded": len(self.registry.prompts_cache),
                "error": self.initialization_error if not is_healthy else None
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def clear_all_caches(self):
        """清空所有緩存"""
        self.renderer.clear_cache()
        logger.info("已清空所有緩存")
    
    async def validate_prompt_template(self, template: str) -> Dict[str, Any]:
        """驗證提示模板"""
        return await self.renderer.validate_template(template)