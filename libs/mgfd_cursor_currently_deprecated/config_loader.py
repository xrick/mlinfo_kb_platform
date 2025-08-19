"""
配置載入器模組
負責載入和管理所有配置檔案
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional


class ConfigLoader:
    """
    配置載入器
    負責載入和管理所有配置檔案
    """
    
    def __init__(self, config_path: str = "libs/mgfd_cursor/humandata/"):
        """
        初始化配置載入器
        
        Args:
            config_path: 配置檔案路徑
        """
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        self._cache = {}
        
        # 確保配置路徑存在
        if not os.path.exists(config_path):
            self.logger.warning(f"配置路徑不存在: {config_path}")
            os.makedirs(config_path, exist_ok=True)
    
    def load_slot_schema(self) -> Dict[str, Any]:
        """
        載入槽位模式配置
        
        Returns:
            槽位模式字典
        """
        cache_key = "slot_schema"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # 載入槽位同義詞
            slot_synonyms = self.load_slot_synonyms()
            
            # 構建槽位模式
            slot_schema = {
                "usage_purpose": {
                    "description": "使用目的",
                    "type": "string",
                    "required": True,
                    "options": ["gaming", "business", "study", "entertainment", "other"],
                    "synonyms": slot_synonyms.get("usage_purpose", [])
                },
                "budget_range": {
                    "description": "預算範圍",
                    "type": "string", 
                    "required": True,
                    "options": ["low", "medium", "high", "premium"],
                    "synonyms": slot_synonyms.get("budget_range", [])
                },
                "performance_features": {
                    "description": "性能需求",
                    "type": "list",
                    "required": False,
                    "options": ["cpu", "gpu", "memory", "storage", "display"],
                    "synonyms": slot_synonyms.get("performance_features", [])
                },
                "brand_preference": {
                    "description": "品牌偏好",
                    "type": "string",
                    "required": False,
                    "options": ["asus", "acer", "lenovo", "hp", "dell", "apple", "other"],
                    "synonyms": slot_synonyms.get("brand_preference", [])
                },
                "size_preference": {
                    "description": "尺寸偏好",
                    "type": "string",
                    "required": False,
                    "options": ["13", "14", "15", "16", "17"],
                    "synonyms": slot_synonyms.get("size_preference", [])
                }
            }
            
            self._cache[cache_key] = slot_schema
            self.logger.info("槽位模式載入成功")
            return slot_schema
            
        except Exception as e:
            self.logger.error(f"載入槽位模式失敗: {e}", exc_info=True)
            # 返回默認槽位模式
            return {
                "usage_purpose": {
                    "description": "使用目的",
                    "type": "string",
                    "required": True,
                    "options": ["gaming", "business", "study", "entertainment", "other"],
                    "synonyms": []
                },
                "budget_range": {
                    "description": "預算範圍", 
                    "type": "string",
                    "required": True,
                    "options": ["low", "medium", "high", "premium"],
                    "synonyms": []
                }
            }
    
    def load_slot_synonyms(self) -> Dict[str, List[str]]:
        """
        載入槽位同義詞配置
        
        Returns:
            槽位同義詞字典
        """
        cache_key = "slot_synonyms"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            file_path = os.path.join(self.config_path, "slot_synonyms.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._cache[cache_key] = data
                    self.logger.info("槽位同義詞載入成功")
                    return data
            else:
                self.logger.warning(f"槽位同義詞檔案不存在: {file_path}")
                return {}
                
        except Exception as e:
            self.logger.error(f"載入槽位同義詞失敗: {e}", exc_info=True)
            return {}
    
    def load_personality_profiles(self) -> Dict[str, Any]:
        """
        載入個性配置檔案
        
        Returns:
            個性配置字典
        """
        cache_key = "personality_profiles"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            file_path = os.path.join(self.config_path, "personality_profiles.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._cache[cache_key] = data
                    self.logger.info("個性配置載入成功")
                    return data
            else:
                self.logger.warning(f"個性配置檔案不存在: {file_path}")
                return {}
                
        except Exception as e:
            self.logger.error(f"載入個性配置失敗: {e}", exc_info=True)
            return {}
    
    def load_response_templates(self) -> Dict[str, Any]:
        """
        載入回應模板配置
        
        Returns:
            回應模板字典
        """
        cache_key = "response_templates"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            file_path = os.path.join(self.config_path, "response_templates.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._cache[cache_key] = data
                    self.logger.info("回應模板載入成功")
                    return data
            else:
                self.logger.warning(f"回應模板檔案不存在: {file_path}")
                return {}
                
        except Exception as e:
            self.logger.error(f"載入回應模板失敗: {e}", exc_info=True)
            return {}
    
    def load_conversation_styles(self) -> Dict[str, Any]:
        """
        載入對話風格配置
        
        Returns:
            對話風格字典
        """
        cache_key = "conversation_styles"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            file_path = os.path.join(self.config_path, "conversation_styles.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._cache[cache_key] = data
                    self.logger.info("對話風格載入成功")
                    return data
            else:
                self.logger.warning(f"對話風格檔案不存在: {file_path}")
                return {}
                
        except Exception as e:
            self.logger.error(f"載入對話風格失敗: {e}", exc_info=True)
            return {}
    
    def load_error_handling(self) -> Dict[str, Any]:
        """
        載入錯誤處理配置
        
        Returns:
            錯誤處理字典
        """
        cache_key = "error_handling"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            file_path = os.path.join(self.config_path, "error_handling.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._cache[cache_key] = data
                    self.logger.info("錯誤處理配置載入成功")
                    return data
            else:
                self.logger.warning(f"錯誤處理配置檔案不存在: {file_path}")
                return {}
                
        except Exception as e:
            self.logger.error(f"載入錯誤處理配置失敗: {e}", exc_info=True)
            return {}
    
    def load_think_prompts(self) -> Dict[str, Any]:
        """
        載入Think階段提示詞配置
        
        Returns:
            Think提示詞字典
        """
        cache_key = "think_prompts"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            file_path = os.path.join(self.config_path, "think_prompts.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._cache[cache_key] = data
                    self.logger.info("Think提示詞載入成功")
                    return data
            else:
                self.logger.warning(f"Think提示詞檔案不存在: {file_path}")
                return {}
                
        except Exception as e:
            self.logger.error(f"載入Think提示詞失敗: {e}", exc_info=True)
            return {}
    
    def load_act_prompts(self) -> Dict[str, Any]:
        """
        載入Act階段提示詞配置
        
        Returns:
            Act提示詞字典
        """
        cache_key = "act_prompts"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            file_path = os.path.join(self.config_path, "act_prompts.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._cache[cache_key] = data
                    self.logger.info("Act提示詞載入成功")
                    return data
            else:
                self.logger.warning(f"Act提示詞檔案不存在: {file_path}")
                return {}
                
        except Exception as e:
            self.logger.error(f"載入Act提示詞失敗: {e}", exc_info=True)
            return {}
    
    def get_personality_profile(self, profile_name: str = "professional") -> Dict[str, Any]:
        """
        獲取指定的個性配置
        
        Args:
            profile_name: 個性配置名稱
            
        Returns:
            個性配置字典
        """
        profiles = self.load_personality_profiles()
        return profiles.get("profiles", {}).get(profile_name, {})
    
    def get_response_template(self, template_type: str, context: Dict[str, Any] = None) -> str:
        """
        獲取回應模板
        
        Args:
            template_type: 模板類型
            context: 上下文信息
            
        Returns:
            模板字符串
        """
        templates = self.load_response_templates()
        template = templates.get("templates", {}).get(template_type, "")
        
        if context and template:
            # 簡單的變數替換
            for key, value in context.items():
                template = template.replace(f"{{{key}}}", str(value))
        
        return template
    
    def get_conversation_style(self, style_name: str = "formal") -> Dict[str, Any]:
        """
        獲取對話風格配置
        
        Args:
            style_name: 風格名稱
            
        Returns:
            對話風格字典
        """
        styles = self.load_conversation_styles()
        return styles.get("styles", {}).get(style_name, {})
    
    def get_error_message(self, error_type: str) -> str:
        """
        獲取錯誤消息
        
        Args:
            error_type: 錯誤類型
            
        Returns:
            錯誤消息
        """
        error_config = self.load_error_handling()
        return error_config.get("messages", {}).get(error_type, "發生未知錯誤")
    
    def clear_cache(self) -> None:
        """
        清除配置緩存
        """
        self._cache.clear()
        self.logger.info("配置緩存已清除")
    
    def reload_config(self) -> None:
        """
        重新載入所有配置
        """
        self.clear_cache()
        self.load_slot_schema()
        self.load_slot_synonyms()
        self.load_personality_profiles()
        self.load_response_templates()
        self.load_conversation_styles()
        self.load_error_handling()
        self.load_think_prompts()
        self.load_act_prompts()
        self.logger.info("所有配置重新載入完成")
