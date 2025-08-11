#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD 配置檔案載入器
負責載入和管理所有 JSON 配置檔案
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

class MGFDConfigLoader:
    """MGFD 配置檔案載入器"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置載入器
        
        Args:
            config_dir: 配置檔案目錄路徑
        """
        if config_dir is None:
            # 預設使用 humandata 目錄
            current_dir = Path(__file__).parent
            self.config_dir = current_dir / "humandata"
        else:
            self.config_dir = Path(config_dir)
        
        self.logger = logging.getLogger(__name__)
        self._config_cache: Dict[str, Any] = {}
        self._last_modified: Dict[str, float] = {}
        
        # 確保配置目錄存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 載入所有配置檔案
        self._load_all_configs()
    
    def _load_all_configs(self):
        """載入所有配置檔案"""
        config_files = [
            "personality_profiles.json",
            "conversation_styles.json", 
            "response_templates.json",
            "error_handling.json",
            "think_prompts.json",
            "act_prompts.json"
        ]
        
        for config_file in config_files:
            try:
                self._load_config(config_file)
            except Exception as e:
                self.logger.error(f"載入配置檔案 {config_file} 失敗: {e}")
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """
        載入單個配置檔案
        
        Args:
            config_file: 配置檔案名稱
            
        Returns:
            配置內容
        """
        config_path = self.config_dir / config_file
        
        # 檢查檔案是否存在
        if not config_path.exists():
            self.logger.warning(f"配置檔案不存在: {config_path}")
            return {}
        
        # 檢查檔案是否已修改
        current_mtime = config_path.stat().st_mtime
        if (config_file in self._last_modified and 
            self._last_modified[config_file] >= current_mtime):
            return self._config_cache.get(config_file, {})
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self._config_cache[config_file] = config_data
            self._last_modified[config_file] = current_mtime
            
            self.logger.info(f"成功載入配置檔案: {config_file}")
            return config_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 解析錯誤 {config_file}: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"載入配置檔案失敗 {config_file}: {e}")
            return {}
    
    def get_config(self, config_name: str) -> Dict[str, Any]:
        """
        獲取配置內容
        
        Args:
            config_name: 配置名稱 (不含 .json 副檔名)
            
        Returns:
            配置內容
        """
        config_file = f"{config_name}.json"
        
        # 重新載入以檢查更新
        return self._load_config(config_file)
    
    def get_personality_profiles(self) -> Dict[str, Any]:
        """獲取個性化配置"""
        return self.get_config("personality_profiles")
    
    def get_conversation_styles(self) -> Dict[str, Any]:
        """獲取對話風格配置"""
        return self.get_config("conversation_styles")
    
    def get_response_templates(self) -> Dict[str, Any]:
        """獲取回應模板配置"""
        return self.get_config("response_templates")
    
    def get_error_handling(self) -> Dict[str, Any]:
        """獲取錯誤處理配置"""
        return self.get_config("error_handling")
    
    def get_think_prompts(self) -> Dict[str, Any]:
        """獲取 Think 階段提示詞配置"""
        return self.get_config("think_prompts")
    
    def get_act_prompts(self) -> Dict[str, Any]:
        """獲取 Act 階段提示詞配置"""
        return self.get_config("act_prompts")
    
    def reload_config(self, config_name: str) -> bool:
        """
        重新載入指定配置檔案
        
        Args:
            config_name: 配置名稱
            
        Returns:
            是否成功重新載入
        """
        try:
            config_file = f"{config_name}.json"
            self._load_config(config_file)
            return True
        except Exception as e:
            self.logger.error(f"重新載入配置失敗 {config_name}: {e}")
            return False
    
    def reload_all_configs(self) -> bool:
        """
        重新載入所有配置檔案
        
        Returns:
            是否成功重新載入
        """
        try:
            self._load_all_configs()
            return True
        except Exception as e:
            self.logger.error(f"重新載入所有配置失敗: {e}")
            return False
    
    def validate_config(self, config_name: str) -> Dict[str, Any]:
        """
        驗證配置檔案的有效性
        
        Args:
            config_name: 配置名稱
            
        Returns:
            驗證結果
        """
        config_data = self.get_config(config_name)
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        if not config_data:
            validation_result["valid"] = False
            validation_result["errors"].append("配置檔案為空或載入失敗")
            return validation_result
        
        # 根據配置類型進行特定驗證
        if config_name == "personality_profiles":
            validation_result = self._validate_personality_profiles(config_data)
        elif config_name == "conversation_styles":
            validation_result = self._validate_conversation_styles(config_data)
        elif config_name == "response_templates":
            validation_result = self._validate_response_templates(config_data)
        elif config_name == "error_handling":
            validation_result = self._validate_error_handling(config_data)
        elif config_name == "think_prompts":
            validation_result = self._validate_think_prompts(config_data)
        elif config_name == "act_prompts":
            validation_result = self._validate_act_prompts(config_data)
        
        return validation_result
    
    def _validate_personality_profiles(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """驗證個性化配置"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        if "personalities" not in config:
            result["valid"] = False
            result["errors"].append("缺少 personalities 欄位")
            return result
        
        personalities = config["personalities"]
        for key, personality in personalities.items():
            required_fields = ["name", "description", "greeting_style", "response_tone", "closing_style"]
            for field in required_fields:
                if field not in personality:
                    result["errors"].append(f"個性化 {key} 缺少必要欄位: {field}")
                    result["valid"] = False
        
        return result
    
    def _validate_conversation_styles(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """驗證對話風格配置"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        if "conversation_styles" not in config:
            result["valid"] = False
            result["errors"].append("缺少 conversation_styles 欄位")
            return result
        
        return result
    
    def _validate_response_templates(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """驗證回應模板配置"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        if "response_templates" not in config:
            result["valid"] = False
            result["errors"].append("缺少 response_templates 欄位")
            return result
        
        return result
    
    def _validate_error_handling(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """驗證錯誤處理配置"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        if "error_handling" not in config:
            result["valid"] = False
            result["errors"].append("缺少 error_handling 欄位")
            return result
        
        return result
    
    def _validate_think_prompts(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """驗證 Think 階段提示詞配置"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        if "think_prompts" not in config:
            result["valid"] = False
            result["errors"].append("缺少 think_prompts 欄位")
            return result
        
        return result
    
    def _validate_act_prompts(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """驗證 Act 階段提示詞配置"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        if "act_prompts" not in config:
            result["valid"] = False
            result["errors"].append("缺少 act_prompts 欄位")
            return result
        
        return result
    
    def get_config_info(self) -> Dict[str, Any]:
        """獲取配置檔案信息"""
        info = {
            "config_dir": str(self.config_dir),
            "loaded_configs": list(self._config_cache.keys()),
            "last_modified": {
                name: datetime.fromtimestamp(timestamp).isoformat()
                for name, timestamp in self._last_modified.items()
            }
        }
        return info
