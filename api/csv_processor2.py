# api/csv_processor2.py
import os
import tempfile
from typing import List, Dict, Optional
from pathlib import Path
import logging
import re
import pandas as pd
import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from libs.parse.csvparse2.csv_parser2 import CSVParser2

logger = logging.getLogger(__name__)

class CSVProcessor2:
    """CSV 處理器，使用 strategy pattern 和 csv_parser2 解析 CSV 檔案"""
    
    def __init__(self):
        self.parser = CSVParser2()
    
    
    def process_csv_content(self, csv_content: str, custom_rules: Optional[Dict] = None) -> List[Dict[str, str]]:
        """
        處理 CSV 內容並返回結構化資料 (使用 strategy pattern)
        
        Args:
            csv_content: CSV 檔案內容字串
            custom_rules: 自訂解析規則 (目前未使用，保留擴充性)
            
        Returns:
            List[Dict]: 解析後的結構化資料
        """
        try:
            # 創建臨時檔案存放 CSV 內容
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(csv_content)
                temp_file_path = temp_file.name
            
            try:
                # 使用 csv_parser2 解析
                logger.info(f"開始使用 CSVProcessor2 strategy 解析檔案: {temp_file_path}")
                
                # 執行解析流程
                success = self.parser.beforeParse(temp_file_path)
                if not success:
                    raise Exception("CSV 解析前準備失敗")
                
                # 執行主要解析
                parsed_data = self.parser.inParse()
                if not parsed_data:
                    raise Exception("CSV 解析無結果")
                
                # 執行後處理 (會將結果存到 self.parser.processed_csv)
                success = self.parser.endParse()
                if not success:
                    logger.warning("CSV 解析後處理失敗，但繼續執行")
                
                # 從記憶體中獲取處理好的資料
                if hasattr(self.parser, 'processed_csv') and self.parser.processed_csv:
                    result = self.parser.processed_csv
                    logger.info(f"CSVProcessor2 解析完成，從記憶體獲取 {len(result)} 筆記錄")
                    return result
                else:
                    # 如果 processed_csv 還沒實作，暫時回傳原始結果
                    logger.warning("processed_csv 尚未實作，回傳原始解析結果")
                    return parsed_data
                
            finally:
                # 清理臨時檔案
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"CSVProcessor2 處理失敗: {str(e)}")
            raise Exception(f"CSV 處理錯誤: {str(e)}")
    
    def process_csv_file(self, file_path: str, custom_rules: Optional[Dict] = None) -> List[Dict[str, str]]:
        """
        處理 CSV 檔案並返回結構化資料
        
        Args:
            file_path: CSV 檔案路徑
            custom_rules: 自訂解析規則
            
        Returns:
            List[Dict]: 解析後的結構化資料
        """
        try:
            if not os.path.exists(file_path):
                raise Exception(f"檔案不存在: {file_path}")
            
            logger.info(f"開始使用 CSVProcessor2 處理檔案: {file_path}")
            
            # 執行解析流程
            success = self.parser.beforeParse(file_path)
            if not success:
                raise Exception("CSV 解析前準備失敗")
            
            # 執行主要解析
            parsed_data = self.parser.inParse()
            if not parsed_data:
                raise Exception("CSV 解析無結果")
            
            # 執行後處理
            success = self.parser.endParse()
            if not success:
                logger.warning("CSV 解析後處理失敗，但繼續執行")
            
            # 從記憶體中獲取處理好的資料
            if hasattr(self.parser, 'processed_csv') and self.parser.processed_csv:
                result = self.parser.processed_csv
                logger.info(f"CSVProcessor2 檔案處理完成，從記憶體獲取 {len(result)} 筆記錄")
                return result
            else:
                # 如果 processed_csv 還沒實作，暫時回傳原始結果
                logger.warning("processed_csv 尚未實作，回傳原始解析結果")
                return parsed_data
            
        except Exception as e:
            logger.error(f"CSVProcessor2 檔案處理失敗: {str(e)}")
            raise Exception(f"CSV 檔案處理錯誤: {str(e)}")
    
    def get_parser_info(self) -> Dict[str, any]:
        """
        獲取解析器資訊
        
        Returns:
            Dict: 解析器配置資訊
        """
        try:
            # 載入規則檔案獲取基本資訊
            rules_file = Path(__file__).parent.parent / "libs/parse/csvparse2/rules.json"
            
            import json
            with open(rules_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            
            config = rules[0][0] if rules and len(rules) > 0 and len(rules[0]) > 0 else {}
            rule_count = len(rules[1]) if len(rules) > 1 else 0
            
            return {
                "processor": "CSVProcessor2 (strategy pattern)",
                "parser": "csv_parser2",
                "model_count": config.get("model_count", 0),
                "model_type": config.get("model_type", "unknown"),
                "rule_count": rule_count,
                "rules_file": str(rules_file),
                "default_output_path": config.get("default_output_path", "./output.csv")
            }
            
        except Exception as e:
            logger.error(f"CSVProcessor2 獲取解析器資訊失敗: {str(e)}")
            return {
                "processor": "CSVProcessor2 (strategy pattern)",
                "parser": "csv_parser2",
                "error": str(e)
            }
    
    def detect_modeltype(self, file_name: str, parsed_data: list) -> str:
        """
        依序嘗試從檔名、內容自動判斷 modeltype，失敗則回傳 None。
        Args:
            file_name: 上傳檔案名稱
            parsed_data: 解析後的資料（list of dict）
        Returns:
            modeltype 字串或 None
        """
        # 1. 標準數字檔名判斷（如 960.csv → 960）
        m = re.match(r"(\d{3,4})\.csv$", file_name, re.IGNORECASE)
        if m:
            return m.group(1)
        
        # 2. 新增：靈活檔名解析（如 AC01.csv → AC01，Model_123.csv → Model_123）
        if file_name:
            # 移除副檔名並清理檔名
            base_name = re.sub(r'\.(csv|CSV)$', '', file_name)
            # 檢查是否為合理的 modeltype（長度限制，避免過長檔名）
            if base_name and 1 <= len(base_name) <= 15 and re.match(r'^[A-Za-z0-9_-]+$', base_name):
                logger.info(f"從檔名提取 modeltype: {file_name} → {base_name}")
                return base_name
        
        # 3. 內容判斷（逐行找 modeltype 欄位或 Model Name 關鍵字）
        if parsed_data and isinstance(parsed_data, list):
            # 先檢查所有資料的 modeltype 欄位
            types = set()
            for row in parsed_data:
                if isinstance(row, dict):
                    # 檢查多個可能的欄位名稱
                    t = (row.get("modeltype") or row.get("Model Name") or 
                         row.get("model") or row.get("Model") or 
                         row.get("model_type") or row.get("ModelType"))
                    if t and isinstance(t, str) and t.strip():
                        types.add(t.strip())
            if len(types) == 1:
                modeltype = list(types)[0]
                logger.info(f"從 CSV 內容檢測到 modeltype: {modeltype}")
                return modeltype
        
        # 失敗
        logger.warning(f"無法從檔名 '{file_name}' 或內容自動檢測 modeltype")
        return None