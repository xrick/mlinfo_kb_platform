"""
Markdown 表格生成器
整合 TableDataConverter 提供完整的表格生成功能
"""

import logging
from typing import Dict, Any, List, Optional
from .TableDataConverter import TableDataConverter


class MarkdownTableGenerator:
    """Markdown 表格生成器"""
    
    def __init__(self):
        self.converter = TableDataConverter()
        self.logger = logging.getLogger(__name__)
    
    def generate_table(
        self, 
        data: Dict[str, Any], 
        table_name: str = "",
        style_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成 Markdown 表格
        
        Args:
            data: 表格數據
            table_name: 表格名稱
            style_config: 樣式配置
                - alignment: 對齊方式
                - max_width: 最大寬度
                - format_rules: 格式化規則
        
        Returns:
            Markdown 表格字符串
        """
        try:
            # 驗證數據
            if not self.converter.validate_data(data):
                self.logger.warning("數據格式不適合轉換為表格")
                return self._create_fallback_table(data)
            
            # 生成表格
            table_content = self.converter.create_markdown_table(data, table_name, style_config)
            
            self.logger.info(f"成功生成 Markdown 表格: {table_name}")
            return table_content
            
        except Exception as e:
            self.logger.error(f"生成 Markdown 表格時發生錯誤: {e}")
            return self._create_error_table(str(e))
    
    def generate_comparison_table(
        self, 
        comparison_data: List[Dict[str, Any]], 
        product_names: List[str],
        table_name: str = "產品比較表"
    ) -> str:
        """
        生成產品比較表格
        
        Args:
            comparison_data: 比較數據
            product_names: 產品名稱列表
            table_name: 表格名稱
        
        Returns:
            Markdown 比較表格字符串
        """
        try:
            # 格式化比較數據
            formatted_data = self._format_comparison_data(comparison_data, product_names)
            
            # 生成表格
            return self.generate_table(formatted_data, table_name)
            
        except Exception as e:
            self.logger.error(f"生成比較表格時發生錯誤: {e}")
            return self._create_error_table(str(e))
    
    def generate_recommendation_table(
        self, 
        recommendations: List[Dict[str, Any]], 
        table_name: str = "推薦產品"
    ) -> str:
        """
        生成推薦產品表格
        
        Args:
            recommendations: 推薦產品列表
            table_name: 表格名稱
        
        Returns:
            Markdown 推薦表格字符串
        """
        try:
            # 格式化推薦數據
            formatted_data = self._format_recommendation_data(recommendations)
            
            # 生成表格
            return self.generate_table(formatted_data, table_name)
            
        except Exception as e:
            self.logger.error(f"生成推薦表格時發生錯誤: {e}")
            return self._create_error_table(str(e))
    
    def generate_specs_table(
        self, 
        specs_data: Dict[str, Any], 
        product_name: str = "",
        table_name: str = "產品規格"
    ) -> str:
        """
        生成產品規格表格
        
        Args:
            specs_data: 規格數據
            product_name: 產品名稱
            table_name: 表格名稱
        
        Returns:
            Markdown 規格表格字符串
        """
        try:
            # 格式化規格數據
            formatted_data = self._format_specs_data(specs_data)
            
            # 生成表格
            full_table_name = f"{product_name} {table_name}" if product_name else table_name
            return self.generate_table(formatted_data, full_table_name)
            
        except Exception as e:
            self.logger.error(f"生成規格表格時發生錯誤: {e}")
            return self._create_error_table(str(e))
    
    def _format_comparison_data(
        self, 
        comparison_data: List[Dict[str, Any]], 
        product_names: List[str]
    ) -> List[Dict[str, Any]]:
        """
        格式化比較數據
        
        Args:
            comparison_data: 原始比較數據
            product_names: 產品名稱列表
        
        Returns:
            格式化後的比較數據
        """
        formatted_data = []
        
        for item in comparison_data:
            if isinstance(item, dict):
                # 處理字典格式的數據
                feature = item.get("feature", "未知規格")
                row_data = {"規格項目": feature}
                
                for i, product_name in enumerate(product_names):
                    value = item.get(product_name, "N/A")
                    row_data[product_name] = value
                
                formatted_data.append(row_data)
            elif isinstance(item, list):
                # 處理列表格式的數據
                if len(item) == len(product_names) + 1:  # +1 for feature name
                    row_data = {"規格項目": item[0]}
                    for i, product_name in enumerate(product_names):
                        row_data[product_name] = item[i + 1]
                    formatted_data.append(row_data)
        
        return formatted_data
    
    def _format_recommendation_data(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        格式化推薦數據
        
        Args:
            recommendations: 原始推薦數據
        
        Returns:
            格式化後的推薦數據
        """
        formatted_data = []
        
        for rec in recommendations:
            formatted_rec = {
                "產品名稱": rec.get("name", "未知型號"),
                "品牌": rec.get("brand", "未知品牌"),
                "價格": rec.get("price", "價格待詢"),
                "推薦理由": rec.get("recommendation_reason", ""),
                "匹配度": f"{rec.get('match_score', 0):.1f}%"
            }
            
            # 添加規格信息
            specs = rec.get("specs", {})
            if specs:
                formatted_rec["CPU"] = specs.get("cpu", "N/A")
                formatted_rec["記憶體"] = specs.get("memory", "N/A")
                formatted_rec["儲存"] = specs.get("storage", "N/A")
            
            formatted_data.append(formatted_rec)
        
        return formatted_data
    
    def _format_specs_data(self, specs_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        格式化規格數據
        
        Args:
            specs_data: 原始規格數據
        
        Returns:
            格式化後的規格數據
        """
        formatted_data = []
        
        # 將規格數據轉換為列表格式
        for key, value in specs_data.items():
            formatted_data.append({
                "規格項目": key,
                "規格值": value
            })
        
        return formatted_data
    
    def _create_fallback_table(self, data: Dict[str, Any]) -> str:
        """
        創建備選表格
        
        Args:
            data: 原始數據
        
        Returns:
            備選表格字符串
        """
        try:
            # 嘗試簡單的格式化
            if isinstance(data, dict):
                table_content = "| 項目 | 值 |\n|------|----|\n"
                for key, value in data.items():
                    table_content += f"| {key} | {value} |\n"
                return table_content
            else:
                return f"數據格式不支援: {type(data)}"
        except Exception:
            return "無法生成表格"
    
    def _create_error_table(self, error_message: str) -> str:
        """
        創建錯誤表格
        
        Args:
            error_message: 錯誤消息
        
        Returns:
            錯誤表格字符串
        """
        return f"| 錯誤 | 詳情 |\n|------|------|\n| 表格生成失敗 | {error_message} |"
    
    def get_table_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        獲取表格信息
        
        Args:
            data: 表格數據
        
        Returns:
            表格信息字典
        """
        return self.converter.get_data_info(data)
    
    def validate_table_data(self, data: Dict[str, Any]) -> bool:
        """
        驗證表格數據
        
        Args:
            data: 表格數據
        
        Returns:
            是否有效
        """
        return self.converter.validate_data(data)
