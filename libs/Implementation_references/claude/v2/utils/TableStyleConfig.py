"""
表格樣式配置系統
提供豐富的表格樣式選項
"""

import logging
from typing import Dict, Any, List, Optional, Union
from enum import Enum


class AlignmentType(Enum):
    """對齊類型"""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class TableStyle(Enum):
    """表格樣式"""
    SIMPLE = "simple"
    COMPACT = "compact"
    DETAILED = "detailed"
    COMPARISON = "comparison"
    RECOMMENDATION = "recommendation"


class TableStyleConfig:
    """表格樣式配置"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.default_styles = self._load_default_styles()
    
    def _load_default_styles(self) -> Dict[str, Dict[str, Any]]:
        """載入預設樣式"""
        return {
            "simple": {
                "alignment": AlignmentType.LEFT,
                "max_width": 80,
                "show_borders": True,
                "compact": True
            },
            "compact": {
                "alignment": AlignmentType.LEFT,
                "max_width": 60,
                "show_borders": False,
                "compact": True,
                "truncate_long_text": True
            },
            "detailed": {
                "alignment": AlignmentType.CENTER,
                "max_width": 120,
                "show_borders": True,
                "compact": False,
                "show_row_numbers": True
            },
            "comparison": {
                "alignment": AlignmentType.CENTER,
                "max_width": 100,
                "show_borders": True,
                "compact": False,
                "highlight_differences": True,
                "color_coding": True
            },
            "recommendation": {
                "alignment": AlignmentType.LEFT,
                "max_width": 90,
                "show_borders": True,
                "compact": False,
                "highlight_best": True,
                "show_ratings": True
            }
        }
    
    def get_style_config(self, style_name: str) -> Dict[str, Any]:
        """
        獲取樣式配置
        
        Args:
            style_name: 樣式名稱
        
        Returns:
            樣式配置字典
        """
        return self.default_styles.get(style_name, self.default_styles["simple"])
    
    def create_custom_style(
        self,
        alignment: AlignmentType = AlignmentType.LEFT,
        max_width: int = 80,
        show_borders: bool = True,
        compact: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        創建自定義樣式
        
        Args:
            alignment: 對齊方式
            max_width: 最大寬度
            show_borders: 是否顯示邊框
            compact: 是否緊湊模式
            **kwargs: 其他樣式選項
        
        Returns:
            自定義樣式配置
        """
        custom_style = {
            "alignment": alignment,
            "max_width": max_width,
            "show_borders": show_borders,
            "compact": compact
        }
        
        # 添加其他選項
        custom_style.update(kwargs)
        
        return custom_style
    
    def apply_style_to_table(
        self, 
        table_content: str, 
        style_config: Dict[str, Any]
    ) -> str:
        """
        將樣式應用到表格內容
        
        Args:
            table_content: 原始表格內容
            style_config: 樣式配置
        
        Returns:
            應用樣式後的表格內容
        """
        try:
            # 這裡可以添加樣式應用的邏輯
            # 例如：調整對齊、添加顏色等
            
            # 目前返回原始內容，實際應用中可以根據需要修改
            return table_content
            
        except Exception as e:
            self.logger.error(f"應用樣式時發生錯誤: {e}")
            return table_content
    
    def get_recommendation_style_config(self) -> Dict[str, Any]:
        """
        獲取推薦表格樣式配置
        
        Returns:
            推薦樣式配置
        """
        return {
            "alignment": AlignmentType.LEFT,
            "max_width": 90,
            "show_borders": True,
            "compact": False,
            "highlight_best": True,
            "show_ratings": True,
            "column_order": ["產品名稱", "品牌", "價格", "推薦理由", "匹配度"],
            "color_coding": {
                "high_match": "green",
                "medium_match": "yellow", 
                "low_match": "red"
            }
        }
    
    def get_comparison_style_config(self) -> Dict[str, Any]:
        """
        獲取比較表格樣式配置
        
        Returns:
            比較樣式配置
        """
        return {
            "alignment": AlignmentType.CENTER,
            "max_width": 100,
            "show_borders": True,
            "compact": False,
            "highlight_differences": True,
            "color_coding": True,
            "show_winner": True,
            "column_order": ["規格項目", "產品A", "產品B", "產品C"]
        }
    
    def get_specs_style_config(self) -> Dict[str, Any]:
        """
        獲取規格表格樣式配置
        
        Returns:
            規格樣式配置
        """
        return {
            "alignment": AlignmentType.LEFT,
            "max_width": 80,
            "show_borders": True,
            "compact": True,
            "group_specs": True,
            "column_order": ["規格項目", "規格值"]
        }
    
    def validate_style_config(self, style_config: Dict[str, Any]) -> bool:
        """
        驗證樣式配置
        
        Args:
            style_config: 樣式配置
        
        Returns:
            是否有效
        """
        try:
            required_fields = ["alignment", "max_width", "show_borders", "compact"]
            
            for field in required_fields:
                if field not in style_config:
                    return False
            
            # 驗證對齊方式
            alignment = style_config["alignment"]
            if not isinstance(alignment, AlignmentType):
                return False
            
            # 驗證最大寬度
            max_width = style_config["max_width"]
            if not isinstance(max_width, int) or max_width <= 0:
                return False
            
            return True
            
        except Exception:
            return False
    
    def merge_style_configs(
        self, 
        base_config: Dict[str, Any], 
        override_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        合併樣式配置
        
        Args:
            base_config: 基礎配置
            override_config: 覆蓋配置
        
        Returns:
            合併後的配置
        """
        merged_config = base_config.copy()
        merged_config.update(override_config)
        return merged_config
    
    def get_available_styles(self) -> List[str]:
        """
        獲取可用的樣式列表
        
        Returns:
            樣式名稱列表
        """
        return list(self.default_styles.keys())
    
    def add_custom_style(self, style_name: str, style_config: Dict[str, Any]) -> bool:
        """
        添加自定義樣式
        
        Args:
            style_name: 樣式名稱
            style_config: 樣式配置
        
        Returns:
            是否成功添加
        """
        try:
            if self.validate_style_config(style_config):
                self.default_styles[style_name] = style_config
                self.logger.info(f"添加自定義樣式: {style_name}")
                return True
            else:
                self.logger.warning(f"樣式配置無效: {style_name}")
                return False
        except Exception as e:
            self.logger.error(f"添加自定義樣式時發生錯誤: {e}")
            return False
    
    def remove_style(self, style_name: str) -> bool:
        """
        移除樣式
        
        Args:
            style_name: 樣式名稱
        
        Returns:
            是否成功移除
        """
        if style_name in self.default_styles and style_name not in ["simple"]:
            del self.default_styles[style_name]
            self.logger.info(f"移除樣式: {style_name}")
            return True
        else:
            self.logger.warning(f"無法移除樣式: {style_name}")
            return False
