"""
回應模板管理器
提供動態模板載入和渲染功能
"""

import logging
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime


class ResponseTemplateManager:
    """回應模板管理器"""
    
    def __init__(self, template_dir: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.template_dir = Path(template_dir) if template_dir else Path(__file__).parent / "templates"
        self.templates = self._load_templates()
        self.template_engine = self._initialize_template_engine()
    
    def _load_templates(self) -> Dict[str, str]:
        """載入模板文件"""
        templates = {}
        
        try:
            # 確保模板目錄存在
            self.template_dir.mkdir(parents=True, exist_ok=True)
            
            # 載入預設模板
            templates.update(self._load_default_templates())
            
            # 載入文件模板
            templates.update(self._load_file_templates())
            
            self.logger.info(f"成功載入 {len(templates)} 個模板")
            
        except Exception as e:
            self.logger.error(f"載入模板時發生錯誤: {e}")
            # 使用基本模板作為備選
            templates.update(self._load_fallback_templates())
        
        return templates
    
    def _load_default_templates(self) -> Dict[str, str]:
        """載入預設模板"""
        return {
            "funnel_intro": "歡迎使用筆電購物助手！讓我幫您找到最適合的筆電。",
            "funnel_question": "請問您{question}？",
            "funnel_completion": "太好了！我已經收集到足夠的信息。讓我為您推薦最適合的筆電。",
            "recommendation_intro": "根據您的需求，我為您推薦以下幾款筆電：",
            "recommendation_single": "基於您的需求，我特別推薦這款筆電：",
            "recommendation_comparison": "讓我為您比較這幾款筆電的差異：",
            "elicitation_general": "請您提供更多細節，這樣我才能給您更準確的建議。",
            "elicitation_usage": "請問您具體會用這台電腦做什麼呢？例如：文書處理、影片剪輯、遊戲等。",
            "elicitation_budget": "您的預算大概是多少呢？這樣我可以推薦最適合的選擇。",
            "elicitation_preference": "您對品牌、重量、螢幕大小有什麼特別的偏好嗎？",
            "general_greeting": "您好！我是您的筆電購物助手，有什麼可以幫您的嗎？",
            "general_goodbye": "謝謝您的使用！如果還有任何問題，隨時歡迎詢問。",
            "general_thanks": "不客氣！很高興能幫助您。",
            "general_confirmation": "好的，我明白了。",
            "general_clarification": "請您再說清楚一點，這樣我才能給您更準確的建議。",
            "general_help": "我可以幫您：\n1. 推薦適合的筆電\n2. 比較不同型號\n3. 回答產品相關問題\n請告訴我您需要什麼幫助。",
            "error_general": "抱歉，我遇到了一些問題。請稍後再試。",
            "error_unknown": "抱歉，我不太理解您的意思。請您重新描述一下您的需求。"
        }
    
    def _load_file_templates(self) -> Dict[str, str]:
        """載入文件模板"""
        templates = {}
        
        try:
            # 查找 .json 模板文件
            for template_file in self.template_dir.glob("*.json"):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        file_templates = json.load(f)
                        templates.update(file_templates)
                    self.logger.info(f"載入模板文件: {template_file.name}")
                except Exception as e:
                    self.logger.warning(f"載入模板文件失敗 {template_file.name}: {e}")
            
            # 查找 .txt 模板文件
            for template_file in self.template_dir.glob("*.txt"):
                try:
                    template_name = template_file.stem
                    with open(template_file, 'r', encoding='utf-8') as f:
                        templates[template_name] = f.read().strip()
                    self.logger.info(f"載入文本模板: {template_name}")
                except Exception as e:
                    self.logger.warning(f"載入文本模板失敗 {template_file.name}: {e}")
                    
        except Exception as e:
            self.logger.error(f"載入文件模板時發生錯誤: {e}")
        
        return templates
    
    def _load_fallback_templates(self) -> Dict[str, str]:
        """載入備選模板"""
        return {
            "fallback": "抱歉，模板載入失敗。請稍後再試。"
        }
    
    def _initialize_template_engine(self) -> Dict[str, Any]:
        """初始化模板引擎"""
        return {
            "variables": {},
            "functions": {
                "format_date": lambda fmt: datetime.now().strftime(fmt),
                "capitalize": lambda text: text.capitalize(),
                "lower": lambda text: text.lower(),
                "upper": lambda text: text.upper()
            }
        }
    
    def get_template(self, template_name: str) -> str:
        """
        獲取模板內容
        
        Args:
            template_name: 模板名稱
        
        Returns:
            模板內容
        """
        return self.templates.get(template_name, self.templates.get("fallback", "模板不存在"))
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        渲染模板
        
        Args:
            template_name: 模板名稱
            context: 渲染上下文
        
        Returns:
            渲染後的內容
        """
        try:
            template_content = self.get_template(template_name)
            if not template_content:
                return f"模板不存在: {template_name}"
            
            # 簡單的變數替換
            rendered_content = template_content
            
            # 替換變數
            for key, value in context.items():
                placeholder = f"{{{key}}}"
                if placeholder in rendered_content:
                    rendered_content = rendered_content.replace(placeholder, str(value))
            
            # 處理條件邏輯
            rendered_content = self._process_conditionals(rendered_content, context)
            
            # 處理函數調用
            rendered_content = self._process_functions(rendered_content, context)
            
            return rendered_content
            
        except Exception as e:
            self.logger.error(f"渲染模板時發生錯誤: {e}")
            return f"模板渲染失敗: {template_name}"
    
    def _process_conditionals(self, content: str, context: Dict[str, Any]) -> str:
        """
        處理條件邏輯
        
        Args:
            content: 模板內容
            context: 上下文
        
        Returns:
            處理後的內容
        """
        # 簡單的條件處理：{if condition}content{endif}
        import re
        
        def replace_conditional(match):
            condition = match.group(1).strip()
            content = match.group(2).strip()
            
            # 檢查條件
            if self._evaluate_condition(condition, context):
                return content
            else:
                return ""
        
        # 匹配 {if condition}content{endif} 模式
        pattern = r'\{if\s+([^}]+)\}(.*?)\{endif\}'
        return re.sub(pattern, replace_conditional, content, flags=re.DOTALL)
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        評估條件
        
        Args:
            condition: 條件表達式
            context: 上下文
        
        Returns:
            條件是否為真
        """
        try:
            # 簡單的條件評估
            if "==" in condition:
                left, right = condition.split("==", 1)
                return context.get(left.strip()) == right.strip()
            elif "!=" in condition:
                left, right = condition.split("!=", 1)
                return context.get(left.strip()) != right.strip()
            elif "in" in condition:
                left, right = condition.split(" in ", 1)
                return left.strip() in context.get(right.strip(), "")
            else:
                # 簡單的存在性檢查
                return bool(context.get(condition.strip()))
        except Exception:
            return False
    
    def _process_functions(self, content: str, context: Dict[str, Any]) -> str:
        """
        處理函數調用
        
        Args:
            content: 模板內容
            context: 上下文
        
        Returns:
            處理後的內容
        """
        import re
        
        def replace_function(match):
            func_name = match.group(1)
            args = match.group(2).split(",") if match.group(2) else []
            args = [arg.strip() for arg in args]
            
            if func_name in self.template_engine["functions"]:
                try:
                    func = self.template_engine["functions"][func_name]
                    if args:
                        return func(*args)
                    else:
                        return func()
                except Exception:
                    return match.group(0)
            else:
                return match.group(0)
        
        # 匹配 {function_name(arg1, arg2)} 模式
        pattern = r'\{(\w+)\(([^)]*)\)\}'
        return re.sub(pattern, replace_function, content)
    
    def add_template(self, template_name: str, template_content: str) -> bool:
        """
        添加新模板
        
        Args:
            template_name: 模板名稱
            template_content: 模板內容
        
        Returns:
            是否成功添加
        """
        try:
            self.templates[template_name] = template_content
            self.logger.info(f"添加新模板: {template_name}")
            return True
        except Exception as e:
            self.logger.error(f"添加模板時發生錯誤: {e}")
            return False
    
    def remove_template(self, template_name: str) -> bool:
        """
        移除模板
        
        Args:
            template_name: 模板名稱
        
        Returns:
            是否成功移除
        """
        try:
            if template_name in self.templates:
                del self.templates[template_name]
                self.logger.info(f"移除模板: {template_name}")
                return True
            else:
                self.logger.warning(f"模板不存在: {template_name}")
                return False
        except Exception as e:
            self.logger.error(f"移除模板時發生錯誤: {e}")
            return False
    
    def save_template_to_file(self, template_name: str, filename: str) -> bool:
        """
        保存模板到文件
        
        Args:
            template_name: 模板名稱
            filename: 文件名
        
        Returns:
            是否成功保存
        """
        try:
            template_content = self.get_template(template_name)
            if not template_content:
                return False
            
            file_path = self.template_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            self.logger.info(f"保存模板到文件: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存模板到文件時發生錯誤: {e}")
            return False
    
    def get_available_templates(self) -> List[str]:
        """
        獲取可用模板列表
        
        Returns:
            模板名稱列表
        """
        return list(self.templates.keys())
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """
        獲取模板信息
        
        Args:
            template_name: 模板名稱
        
        Returns:
            模板信息字典
        """
        template_content = self.get_template(template_name)
        
        return {
            "name": template_name,
            "content": template_content,
            "length": len(template_content) if template_content else 0,
            "has_variables": "{" in template_content if template_content else False,
            "has_conditionals": "{if" in template_content if template_content else False,
            "has_functions": "(" in template_content and ")" in template_content if template_content else False
        }
