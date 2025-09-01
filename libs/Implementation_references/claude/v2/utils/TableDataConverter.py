"""
表格數據轉換器
智能將 JSON 數據轉換為 pytablewriter 的 value_matrix 格式
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from pytablewriter import MarkdownTableWriter


class TableDataConverter:
    """表格數據轉換器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def convert_json_to_value_matrix(
        self, 
        json_data: Dict[str, Any], 
        table_config: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[List[Any]]]:
        """
        智能將 JSON 數據轉換為 pytablewriter 格式
        
        Args:
            json_data: 輸入的 JSON 數據
            table_config: 表格配置（可選）
                - headers: 自定義表頭
                - column_mapping: 列映射
                - data_transforms: 數據轉換規則
        
        Returns:
            (headers, value_matrix) 元組
        """
        try:
            # 檢測數據結構類型
            data_structure = self._detect_data_structure(json_data)
            self.logger.debug(f"檢測到數據結構類型: {data_structure}")
            
            if data_structure == "list_of_dicts":
                return self._extract_list_data(json_data)
            elif data_structure == "dict_of_lists":
                return self._convert_dict_of_lists(json_data)
            elif data_structure == "nested_dict":
                return self._flatten_nested_dict(json_data)
            elif data_structure == "simple_dict":
                return self._convert_simple_dict(json_data)
            else:
                raise ValueError(f"不支援的數據結構類型: {data_structure}")
                
        except Exception as e:
            self.logger.error(f"轉換 JSON 數據時發生錯誤: {e}")
            # 返回空表格作為備選
            return [], []
    
    def _detect_data_structure(self, data: Any) -> str:
        """
        檢測數據結構類型
        
        Args:
            data: 輸入數據
            
        Returns:
            數據結構類型字符串
        """
        if isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                return "list_of_dicts"
            else:
                return "simple_list"
        elif isinstance(data, dict):
            # 檢查是否為 dict of lists
            if all(isinstance(value, list) for value in data.values()):
                return "dict_of_lists"
            # 檢查是否有嵌套結構
            elif any(isinstance(value, dict) for value in data.values()):
                return "nested_dict"
            else:
                return "simple_dict"
        else:
            return "unknown"
    
    def _extract_list_data(self, data: List[Dict[str, Any]]) -> Tuple[List[str], List[List[Any]]]:
        """
        提取列表數據
        
        Args:
            data: 列表字典數據
            
        Returns:
            (headers, value_matrix) 元組
        """
        if not data:
            return [], []
        
        # 獲取所有可能的表頭
        all_keys = set()
        for item in data:
            all_keys.update(item.keys())
        
        headers = list(all_keys)
        
        # 生成 value_matrix
        value_matrix = []
        for item in data:
            row = [item.get(header, "") for header in headers]
            value_matrix.append(row)
        
        return headers, value_matrix
    
    def _convert_dict_of_lists(self, data: Dict[str, List[Any]]) -> Tuple[List[str], List[List[Any]]]:
        """
        轉換字典列表格式
        
        Args:
            data: 字典列表數據
            
        Returns:
            (headers, value_matrix) 元組
        """
        headers = list(data.keys())
        
        # 找到最長的列表長度
        max_length = max(len(value) for value in data.values()) if data else 0
        
        # 生成 value_matrix
        value_matrix = []
        for i in range(max_length):
            row = [data[header][i] if i < len(data[header]) else "" for header in headers]
            value_matrix.append(row)
        
        return headers, value_matrix
    
    def _flatten_nested_dict(self, data: Dict[str, Any]) -> Tuple[List[str], List[List[Any]]]:
        """
        扁平化嵌套字典
        
        Args:
            data: 嵌套字典數據
            
        Returns:
            (headers, value_matrix) 元組
        """
        flattened_data = self._flatten_dict(data)
        
        # 轉換為單行表格
        headers = list(flattened_data.keys())
        value_matrix = [[flattened_data[header] for header in headers]]
        
        return headers, value_matrix
    
    def _flatten_dict(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """
        遞歸扁平化字典
        
        Args:
            data: 要扁平化的字典
            prefix: 鍵前綴
            
        Returns:
            扁平化後的字典
        """
        flattened = {}
        
        for key, value in data.items():
            new_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                flattened.update(self._flatten_dict(value, new_key))
            elif isinstance(value, list):
                # 將列表轉換為字符串
                flattened[new_key] = ", ".join(str(item) for item in value)
            else:
                flattened[new_key] = value
        
        return flattened
    
    def _convert_simple_dict(self, data: Dict[str, Any]) -> Tuple[List[str], List[List[Any]]]:
        """
        轉換簡單字典
        
        Args:
            data: 簡單字典數據
            
        Returns:
            (headers, value_matrix) 元組
        """
        headers = list(data.keys())
        value_matrix = [[data[header] for header in headers]]
        
        return headers, value_matrix
    
    def create_markdown_table(
        self, 
        data: Dict[str, Any], 
        table_name: str = "",
        style_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        創建 Markdown 表格
        
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
            # 轉換數據
            headers, value_matrix = self.convert_json_to_value_matrix(data)
            
            if not headers or not value_matrix:
                return "無數據可顯示"
            
            # 創建 MarkdownTableWriter
            writer = MarkdownTableWriter(
                table_name=table_name,
                headers=headers,
                value_matrix=value_matrix
            )
            
            # 應用樣式配置
            if style_config:
                self._apply_style_config(writer, style_config)
            
            # 生成表格
            return writer.dumps()
            
        except Exception as e:
            self.logger.error(f"創建 Markdown 表格時發生錯誤: {e}")
            return f"表格生成失敗: {str(e)}"
    
    def _apply_style_config(self, writer: MarkdownTableWriter, style_config: Dict[str, Any]) -> None:
        """
        應用樣式配置
        
        Args:
            writer: MarkdownTableWriter 實例
            style_config: 樣式配置
        """
        # 這裡可以添加更多樣式配置選項
        if "alignment" in style_config:
            # 設置對齊方式
            pass
        
        if "max_width" in style_config:
            # 設置最大寬度
            pass
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        驗證數據是否適合轉換為表格
        
        Args:
            data: 要驗證的數據
            
        Returns:
            是否適合轉換
        """
        try:
            data_structure = self._detect_data_structure(data)
            return data_structure in ["list_of_dicts", "dict_of_lists", "nested_dict", "simple_dict"]
        except Exception:
            return False
    
    def get_data_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        獲取數據信息
        
        Args:
            data: 輸入數據
            
        Returns:
            數據信息字典
        """
        try:
            data_structure = self._detect_data_structure(data)
            
            info = {
                "structure_type": data_structure,
                "is_valid": self.validate_data(data)
            }
            
            if data_structure == "list_of_dicts":
                info["row_count"] = len(data)
                info["column_count"] = len(data[0]) if data else 0
            elif data_structure == "dict_of_lists":
                info["column_count"] = len(data)
                info["row_count"] = max(len(value) for value in data.values()) if data else 0
            elif data_structure == "simple_dict":
                info["column_count"] = len(data)
                info["row_count"] = 1
            
            return info
            
        except Exception as e:
            return {
                "structure_type": "unknown",
                "is_valid": False,
                "error": str(e)
            }
    
    # 智能 JSON 到 value_matrix 轉換函式
    def smart_convert_json_to_value_matrix(
        self, 
        json_data: Union[Dict[str, Any], List[Dict[str, Any]]], 
        table_config: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[List[Any]]]:
        """
        智能 JSON 到 value_matrix 轉換函式
        
        Args:
            json_data: 輸入的 JSON 數據（可以是字典或列表）
            table_config: 表格配置（可選）
                - headers: 自定義表頭
                - column_mapping: 列映射
                - data_transforms: 數據轉換規則
                - max_rows: 最大行數限制
                - column_order: 列順序
        
        Returns:
            (headers, value_matrix) 元組
        """
        try:
            # 處理配置
            headers = table_config.get("headers") if table_config else None
            column_mapping = table_config.get("column_mapping") if table_config else None
            max_rows = table_config.get("max_rows") if table_config else None
            column_order = table_config.get("column_order") if table_config else None
            
            # 轉換數據
            if isinstance(json_data, list):
                # 列表數據
                if not json_data:
                    return [], []
                
                # 獲取表頭
                if headers:
                    # 使用自定義表頭
                    final_headers = headers
                else:
                    # 自動檢測表頭
                    all_keys = set()
                    for item in json_data:
                        if isinstance(item, dict):
                            all_keys.update(item.keys())
                    final_headers = list(all_keys)
                
                # 應用列映射
                if column_mapping:
                    final_headers = [column_mapping.get(header, header) for header in final_headers]
                
                # 應用列順序
                if column_order:
                    ordered_headers = []
                    for col in column_order:
                        if col in final_headers:
                            ordered_headers.append(col)
                    # 添加未指定的列
                    for col in final_headers:
                        if col not in ordered_headers:
                            ordered_headers.append(col)
                    final_headers = ordered_headers
                
                # 生成 value_matrix
                value_matrix = []
                for item in json_data:
                    if isinstance(item, dict):
                        row = [item.get(header, "") for header in final_headers]
                        value_matrix.append(row)
                
                # 應用行數限制
                if max_rows and len(value_matrix) > max_rows:
                    value_matrix = value_matrix[:max_rows]
                
                return final_headers, value_matrix
                
            elif isinstance(json_data, dict):
                # 字典數據
                if not json_data:
                    return [], []
                
                # 獲取表頭
                if headers:
                    final_headers = headers
                else:
                    final_headers = list(json_data.keys())
                
                # 應用列映射
                if column_mapping:
                    final_headers = [column_mapping.get(header, header) for header in final_headers]
                
                # 生成單行 value_matrix
                value_matrix = [[json_data.get(header, "") for header in final_headers]]
                
                return final_headers, value_matrix
                
            else:
                raise ValueError(f"不支援的數據類型: {type(json_data)}")
                
        except Exception as e:
            self.logger.error(f"智能轉換 JSON 數據時發生錯誤: {e}")
            return [], []
    
    def create_smart_markdown_table(
        self, 
        json_data: Union[Dict[str, Any], List[Dict[str, Any]]], 
        table_name: str = "",
        table_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        使用智能轉換創建 Markdown 表格
        
        Args:
            json_data: 輸入的 JSON 數據
            table_name: 表格名稱
            table_config: 表格配置
        
        Returns:
            Markdown 表格字符串
        """
        try:
            # 使用智能轉換
            headers, value_matrix = self.smart_convert_json_to_value_matrix(json_data, table_config)
            
            if not headers or not value_matrix:
                return "無數據可顯示"
            
            # 創建 MarkdownTableWriter
            writer = MarkdownTableWriter(
                table_name=table_name,
                headers=headers,
                value_matrix=value_matrix
            )
            
            # 生成表格
            return writer.dumps()
            
        except Exception as e:
            self.logger.error(f"創建智能 Markdown 表格時發生錯誤: {e}")
            return f"表格生成失敗: {str(e)}"

