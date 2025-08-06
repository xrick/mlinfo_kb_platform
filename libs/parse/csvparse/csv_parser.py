import pandas as pd
import json
import re
from typing import Any, Dict, List, Optional
from pathlib import Path
import logging

# 導入父類別
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsebase import ParseBase

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CSVParser(ParseBase):
    """
    CSV 檔案解析器
    
    專門用於解析產品規格 CSV 檔案，提取模型資訊、硬體配置等資料
    """
    
    def __init__(self):
        """初始化 CSV 解析器"""
        super().__init__()
        self._df = None
        self._rules = None
        self._parsed_data = []
        self._rules_file = Path(__file__).parent / "rules.json"
    
    def beforeParse(self, data: Any, config: Optional[Dict] = None) -> bool:
        """
        解析前準備工作
        
        Args:
            data: CSV 檔案路徑或 DataFrame
            config: 解析配置參數
            
        Returns:
            bool: 準備工作是否成功
        """
        try:
            # 載入解析規則
            if not self._load_rules():
                logger.error("無法載入解析規則")
                return False
            
            # 載入 CSV 資料
            if isinstance(data, str):
                # 如果是檔案路徑，處理多行合併的情況
                self._df = pd.read_csv(data, encoding='utf-8', keep_default_na=False)
            elif isinstance(data, pd.DataFrame):
                # 如果已經是 DataFrame
                self._df = data
            else:
                logger.error("不支援的資料格式")
                return False
            
            # 預處理：合併多行資料
            self._preprocess_multiline_data()
            
            # 儲存配置
            if config:
                self.config = config
            
            # 基本資料驗證
            if self._df.empty:
                logger.error("CSV 檔案為空")
                return False
            
            logger.info(f"成功載入 CSV 資料，共 {len(self._df)} 行")
            return True
            
        except Exception as e:
            logger.error(f"解析前準備失敗: {str(e)}")
            return False
    
    def inParse(self) -> List[Dict]:
        """
        主要解析邏輯
        
        Returns:
            List[Dict]: 解析結果列表
        """
        try:
            results = []
            
            # 1. 提取模型資訊
            model_data = self._extract_model_info()
            if model_data:
                results.extend(model_data)
            
            # 2. 提取版本資訊
            version_data = self._extract_version_info()
            if version_data:
                results.extend(version_data)
            
            # 3. 提取硬體配置
            hardware_data = self._extract_hardware_info()
            if hardware_data:
                results.extend(hardware_data)
            
            # 4. 提取顯示器資訊
            display_data = self._extract_display_info()
            if display_data:
                results.extend(display_data)
            
            # 5. 提取連接性資訊
            connectivity_data = self._extract_connectivity_info()
            if connectivity_data:
                results.extend(connectivity_data)
            
            # 6. 提取電池資訊
            battery_data = self._extract_battery_info()
            if battery_data:
                results.extend(battery_data)
            
            # 7. 提取尺寸資訊
            dimension_data = self._extract_dimension_info()
            if dimension_data:
                results.extend(dimension_data)
            
            # 8. 提取開發時程
            timeline_data = self._extract_timeline_info()
            if timeline_data:
                results.extend(timeline_data)
            
            # 9. 提取軟體資訊
            software_data = self._extract_software_info()
            if software_data:
                results.extend(software_data)
            
            # 10. 提取認證資訊
            cert_data = self._extract_certification_info()
            if cert_data:
                results.extend(cert_data)
            
            self._parsed_data = results
            logger.info(f"解析完成，共提取 {len(results)} 條記錄")
            return results
            
        except Exception as e:
            logger.error(f"解析過程發生錯誤: {str(e)}")
            return []
    
    def endParse(self) -> bool:
        """
        解析後處理工作，輸出處理過的 CSV 檔案
        
        Returns:
            bool: 後處理是否成功
        """
        try:
            # 資料清理
            self._clean_data()
            
            # 資料驗證
            if not self._validate_data():
                logger.warning("資料驗證失敗，但繼續處理")
            
            # 轉換為結構化的 DataFrame
            processed_df = self._convert_to_structured_dataframe()
            
            # 輸出為 CSV 檔案
            output_path = Path(__file__).parent / "processed_output.csv"
            processed_df.to_csv(output_path, index=False, encoding='utf-8')
            
            # 儲存解析結果
            self.data = self._parsed_data
            self.processed_dataframe = processed_df
            
            logger.info(f"解析後處理完成，CSV 檔案已儲存到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"解析後處理失敗: {str(e)}")
            return False
    
    def _load_rules(self) -> bool:
        """載入解析規則"""
        try:
            with open(self._rules_file, 'r', encoding='utf-8') as f:
                self._rules = json.load(f)
            return True
        except Exception as e:
            logger.error(f"載入規則檔案失敗: {str(e)}")
            return False
    
    def _preprocess_multiline_data(self):
        """預處理多行資料，合併分散在多行的內容"""
        try:
            # 針對每一列，檢查是否需要與下一行合併
            for col in self._df.columns:
                for idx in range(len(self._df) - 1):
                    current_value = str(self._df.iloc[idx][col]).strip()
                    next_value = str(self._df.iloc[idx + 1][col]).strip()
                    
                    # 如果當前行以特定模式結尾，且下一行有內容，則合併
                    if (current_value and next_value and 
                        not next_value.startswith(('Updated', 'Stage', 'Model', 'P/N', 'ID', 'MB', 'DB')) and
                        current_value.endswith((',', ':', '(', '-', '：'))):
                        # 合併兩行
                        merged_value = f"{current_value} {next_value}"
                        self._df.iloc[idx, self._df.columns.get_loc(col)] = merged_value
                        self._df.iloc[idx + 1, self._df.columns.get_loc(col)] = ""
            
            logger.info("多行資料預處理完成")
            
        except Exception as e:
            logger.warning(f"多行資料預處理失敗: {str(e)}")
    
    def _extract_from_cell_content(self, content: str, patterns: List[str], regex_list: List[str]) -> List[str]:
        """從單元格內容中提取匹配的資料"""
        results = []
        content_str = str(content).strip()
        
        if not content_str or content_str in ["", "nan", "None"]:
            return results
        
        # 檢查是否包含關鍵詞模式
        for pattern in patterns:
            if pattern.lower() in content_str.lower():
                # 使用正則表達式提取具體值
                for regex in regex_list:
                    try:
                        matches = re.findall(regex, content_str, re.IGNORECASE)
                        results.extend(matches)
                    except re.error as e:
                        logger.warning(f"正則表達式錯誤 {regex}: {str(e)}")
                break
        
        return list(set(results))  # 去重
    
    def _extract_model_info(self) -> List[Dict]:
        """提取模型資訊"""
        results = []
        rules = self._rules['csv_parsing_rules']['model_extraction']
        
        # 檢查所有單元格內容
        for idx, row in self._df.iterrows():
            for col in self._df.columns:
                cell_content = str(row[col]).strip()
                if cell_content:
                    # 使用新的統一提取方法
                    matches = self._extract_from_cell_content(
                        cell_content, 
                        rules['model_name_patterns'], 
                        rules['model_regex']
                    )
                    
                    for match in matches:
                        results.append({
                            'category': 'model_info',
                            'type': 'model_name',
                            'value': match,
                            'source': f"{col}:{idx}",
                            'raw_data': cell_content
                        })
        
        return results
    
    def _extract_version_info(self) -> List[Dict]:
        """提取版本資訊"""
        results = []
        rules = self._rules['csv_parsing_rules']['version_extraction']
        
        # 檢查所有單元格內容
        for idx, row in self._df.iterrows():
            for col in self._df.columns:
                cell_content = str(row[col]).strip()
                if cell_content:
                    matches = self._extract_from_cell_content(
                        cell_content, 
                        rules['version_patterns'], 
                        rules['version_regex']
                    )
                    
                    for match in matches:
                        results.append({
                            'category': 'version_info',
                            'type': 'version',
                            'value': match,
                            'source': f"{col}:{idx}",
                            'raw_data': cell_content
                        })
        
        return results
    
    def _extract_hardware_info(self) -> List[Dict]:
        """提取硬體配置資訊"""
        results = []
        rules = self._rules['csv_parsing_rules']['hardware_extraction']
        
        for category, category_rules in rules.items():
            for idx, row in self._df.iterrows():
                for col in self._df.columns:
                    cell_content = str(row[col]).strip()
                    if cell_content:
                        matches = self._extract_from_cell_content(
                            cell_content, 
                            category_rules.get('patterns', []), 
                            category_rules.get('regex', [])
                        )
                        
                        for match in matches:
                            results.append({
                                'category': 'hardware_info',
                                'type': category.replace('_patterns', ''),
                                'value': match,
                                'source': f"{col}:{idx}",
                                'raw_data': cell_content
                            })
        
        return results
    
    def _extract_display_info(self) -> List[Dict]:
        """提取顯示器資訊"""
        results = []
        rules = self._rules['csv_parsing_rules']['display_extraction']
        
        for category, category_rules in rules.items():
            for idx, row in self._df.iterrows():
                for col in self._df.columns:
                    cell_content = str(row[col]).strip()
                    if cell_content:
                        matches = self._extract_from_cell_content(
                            cell_content, 
                            category_rules.get('patterns', []), 
                            category_rules.get('regex', [])
                        )
                        
                        for match in matches:
                            results.append({
                                'category': 'display_info',
                                'type': category.replace('_patterns', ''),
                                'value': match,
                                'source': f"{col}:{idx}",
                                'raw_data': cell_content
                            })
        
        return results
    
    def _extract_connectivity_info(self) -> List[Dict]:
        """提取連接性資訊"""
        results = []
        rules = self._rules['csv_parsing_rules']['connectivity_extraction']
        
        for category, category_rules in rules.items():
            for idx, row in self._df.iterrows():
                for col in self._df.columns:
                    cell_content = str(row[col]).strip()
                    if cell_content:
                        matches = self._extract_from_cell_content(
                            cell_content, 
                            category_rules.get('patterns', []), 
                            category_rules.get('regex', [])
                        )
                        
                        for match in matches:
                            results.append({
                                'category': 'connectivity_info',
                                'type': category.replace('_patterns', ''),
                                'value': match,
                                'source': f"{col}:{idx}",
                                'raw_data': cell_content
                            })
        
        return results
    
    def _extract_battery_info(self) -> List[Dict]:
        """提取電池資訊"""
        results = []
        rules = self._rules['csv_parsing_rules']['battery_extraction']
        
        for idx, row in self._df.iterrows():
            for col in self._df.columns:
                cell_content = str(row[col]).strip()
                if cell_content:
                    matches = self._extract_from_cell_content(
                        cell_content, 
                        rules['battery_patterns'], 
                        rules['battery_regex']
                    )
                    
                    for match in matches:
                        results.append({
                            'category': 'battery_info',
                            'type': 'battery_spec',
                            'value': match,
                            'source': f"{col}:{idx}",
                            'raw_data': cell_content
                        })
        
        return results
    
    def _extract_dimension_info(self) -> List[Dict]:
        """提取尺寸資訊"""
        results = []
        rules = self._rules['csv_parsing_rules']['dimension_extraction']
        
        for col in self._df.columns:
            if any(pattern.lower() in col.lower() for pattern in rules['dimension_patterns']):
                for idx, value in enumerate(self._df[col]):
                    if pd.notna(value) and str(value).strip():
                        for regex in rules['dimension_regex']:
                            matches = re.findall(regex, str(value))
                            for match in matches:
                                results.append({
                                    'category': 'dimension_info',
                                    'type': 'dimension',
                                    'value': match,
                                    'source': f"{col}:{idx}",
                                    'raw_data': str(value)
                                })
        
        return results
    
    def _extract_timeline_info(self) -> List[Dict]:
        """提取開發時程資訊"""
        results = []
        rules = self._rules['csv_parsing_rules']['development_extraction']
        
        for col in self._df.columns:
            if any(pattern.lower() in col.lower() for pattern in rules['timeline_patterns']):
                for idx, value in enumerate(self._df[col]):
                    if pd.notna(value) and str(value).strip():
                        for regex in rules['timeline_regex']:
                            matches = re.findall(regex, str(value))
                            for match in matches:
                                results.append({
                                    'category': 'timeline_info',
                                    'type': 'development_stage',
                                    'value': match,
                                    'source': f"{col}:{idx}",
                                    'raw_data': str(value)
                                })
        
        return results
    
    def _extract_software_info(self) -> List[Dict]:
        """提取軟體資訊"""
        results = []
        rules = self._rules['csv_parsing_rules']['software_extraction']
        
        for col in self._df.columns:
            if any(pattern.lower() in col.lower() for pattern in rules['os_patterns']):
                for idx, value in enumerate(self._df[col]):
                    if pd.notna(value) and str(value).strip():
                        for regex in rules['os_regex']:
                            matches = re.findall(regex, str(value), re.IGNORECASE)
                            for match in matches:
                                results.append({
                                    'category': 'software_info',
                                    'type': 'operating_system',
                                    'value': match,
                                    'source': f"{col}:{idx}",
                                    'raw_data': str(value)
                                })
        
        return results
    
    def _extract_certification_info(self) -> List[Dict]:
        """提取認證資訊"""
        results = []
        rules = self._rules['csv_parsing_rules']['certification_extraction']
        
        for col in self._df.columns:
            if any(pattern.lower() in col.lower() for pattern in rules['cert_patterns']):
                for idx, value in enumerate(self._df[col]):
                    if pd.notna(value) and str(value).strip():
                        for regex in rules['cert_regex']:
                            matches = re.findall(regex, str(value), re.IGNORECASE)
                            for match in matches:
                                results.append({
                                    'category': 'certification_info',
                                    'type': 'certification',
                                    'value': match,
                                    'source': f"{col}:{idx}",
                                    'raw_data': str(value)
                                })
        
        return results
    
    def _clean_data(self):
        """清理解析後的資料"""
        if not self._parsed_data:
            return
        
        remove_patterns = self._rules['data_cleaning_rules']['remove_patterns']
        
        for item in self._parsed_data:
            # 移除不需要的值
            if item['value'] in remove_patterns:
                item['value'] = None
                continue
            
            # 清理空白字元
            if isinstance(item['value'], str):
                item['value'] = re.sub(r'\s+', ' ', item['value']).strip()
    
    def _validate_data(self) -> bool:
        """驗證解析後的資料"""
        if not self._parsed_data:
            return False
        
        valid_count = sum(1 for item in self._parsed_data if item['value'] is not None)
        total_count = len(self._parsed_data)
        
        logger.info(f"資料驗證: {valid_count}/{total_count} 條記錄有效")
        return valid_count > 0
    
    def _convert_to_structured_dataframe(self) -> pd.DataFrame:
        """將解析結果轉換為結構化的 DataFrame"""
        try:
            # 按類別組織資料
            structured_data = {}
            
            # 從原始 CSV 中提取基本資訊（模型名稱作為主鍵）
            models = []
            for idx, row in self._df.iterrows():
                for col in self._df.columns:
                    cell_content = str(row[col]).strip()
                    # 尋找模型名稱（如 APX938, ARB938 等）
                    if re.match(r'^[A-Z]{3}\d{3}[A-Z]?$', cell_content):
                        if cell_content not in models:
                            models.append(cell_content)
            
            # 如果沒有找到模型，使用列名作為模型
            if not models:
                models = [col for col in self._df.columns if col not in ['Unnamed: 0', 'Unnamed: 6', 'Unnamed: 7']][:4]
            
            # 為每個模型創建記錄
            output_rows = []
            for model in models:
                row_data = {'model_name': model}
                
                # 按類別整理資料
                for item in self._parsed_data:
                    category = item['category']
                    item_type = item['type']
                    value = item['value']
                    
                    # 根據來源欄位判斷是否屬於此模型
                    if self._belongs_to_model(item['source'], model):
                        column_name = f"{category}_{item_type}"
                        
                        # 如果已存在該欄位，合併值
                        if column_name in row_data:
                            if isinstance(row_data[column_name], str):
                                if value not in row_data[column_name]:
                                    row_data[column_name] += f"; {value}"
                            else:
                                row_data[column_name] = f"{row_data[column_name]}; {value}"
                        else:
                            row_data[column_name] = value
                
                output_rows.append(row_data)
            
            # 創建 DataFrame
            df = pd.DataFrame(output_rows)
            
            # 重新排列欄位順序
            preferred_order = ['model_name']
            other_cols = [col for col in df.columns if col != 'model_name']
            other_cols.sort()
            df = df[preferred_order + other_cols]
            
            logger.info(f"轉換為結構化 DataFrame: {len(df)} 行, {len(df.columns)} 欄")
            return df
            
        except Exception as e:
            logger.error(f"轉換為 DataFrame 失敗: {str(e)}")
            # 返回基本的 DataFrame
            return pd.DataFrame(self._parsed_data)
    
    def _belongs_to_model(self, source: str, model: str) -> bool:
        """判斷資料項目是否屬於特定模型"""
        # 簡單的歸屬判斷邏輯
        # 可以根據來源欄位名稱或位置來判斷
        if model in ['APX938', 'ARB938', 'AHP938U', 'AKK938']:
            model_index = ['APX938', 'ARB938', 'AHP938U', 'AKK938'].index(model)
            if f'FP7r2.{model_index}' in source or f'FP8' in source:
                return True
            if source.startswith('FP7r2:') and model_index == 0:
                return True
        return True  # 默認情況下歸屬於所有模型
    
    def get_parsed_data(self) -> List[Dict]:
        """獲取解析後的資料"""
        return self._parsed_data
    
    def export_to_json(self, output_path: str) -> bool:
        """匯出解析結果到 JSON 檔案"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self._parsed_data, f, ensure_ascii=False, indent=2)
            logger.info(f"解析結果已匯出到: {output_path}")
            return True
        except Exception as e:
            logger.error(f"匯出失敗: {str(e)}")
            return False 