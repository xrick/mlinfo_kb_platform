# import pandas as pd
import json
# import re
from typing import Any, Dict, Optional
from pathlib import Path
import csv
# import argparse

import logging
import pandas as pd

# 導入父類別
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsebase import ParseBase

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CSVParser2(ParseBase):

    def __init__(self):
        super().__init__()
        self.rawcsv = None
        self.processed_csv = None
        self.datalist = None
        self._rules = None
        self._rules_file = Path(__file__).parent / "rules.json"
        self.headers = None
        self.processed_result = None
        self.default_output_path = None

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
            # 設置輸入資料
            self.rawcsv = data
            #first check if the file is xlsx, if so, convert to csv
            self.rawcsv = self.convert_xlsx_to_csv_if_needed(self.rawcsv)
            # 載入 CSV 並自動檢測格式
            self.datalist = self._load_csv(self.rawcsv)
            
            # 自動檢測 CSV 格式並決定處理方式
            if self._is_structured_specs_csv():
                # 使用規則驅動解析（適用於筆電規格CSV）
                logger.info("檢測到結構化規格 CSV，使用規則驅動解析")
                self._rules = self._load_rules()
                if not self._rules:
                    logger.error("無法載入解析規則")
                    return False
                
                # 設置標題
                self.headers = [
                    rule.get("column_name", f"欄位{i+1}")
                    for i, rule in enumerate(self._rules[1])
                ]
                
                # 設置模型參數
                self.default_output_path = self._rules[0][0].get("default_output_path", "./output.csv")
                
            else:
                # 使用動態解析（適用於一般CSV）
                logger.info("檢測到一般 CSV 格式，使用動態解析")
                self._setup_dynamic_parsing()
            
            logger.info(f"解析前準備完成 - 標題: {self.headers}")
            return True
            
        except Exception as e:
            logger.error(f"解析前準備失敗: {str(e)}")
            return False
         

    def inParse(self):
        """
        主要解析邏輯
        
        Returns:
            List[Dict]: 解析結果列表
        """
        if self._rules is None:
            # 動態解析模式
            self._dynamic_collect_results()
        else:
            # 規則驅動解析模式
            self.collect_results()
        
        return self.processed_result

    
    def endParse(self) -> bool:
        """
        解析後處理工作
        
        Returns:
            bool: 後處理是否成功
        """
        try:
            if self.processed_result:
                self.write_csv()
                logger.info("解析後處理完成")
                return True
            else:
                logger.error("無解析結果可處理")
                return False
        except Exception as e:
            logger.error(f"解析後處理失敗: {str(e)}")
            return False
        
    
    def _load_rules(self):
        with open(self._rules_file, "r", encoding="utf-8-sig") as f:
            return json.load(f)
        


    def _load_csv(self, file_path):
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            return list(csv.reader(f))
    
    def _is_structured_specs_csv(self) -> bool:
        """
        檢測是否為結構化規格 CSV（如 raw_938.csv 格式）
        
        Returns:
            bool: 是否為結構化規格格式
        """
        if not self.datalist or len(self.datalist) < 3:
            return False
        
        # 檢查是否包含筆電規格的關鍵詞
        spec_keywords = ["Model", "Model Name", "CPU", "GPU", "Memory", "LCD", "Battery", "Stage", "Version"]
        
        # 檢查前幾行是否包含這些關鍵詞
        content_text = " ".join([" ".join(row) for row in self.datalist[:10]])
        
        keyword_count = sum(1 for keyword in spec_keywords if keyword in content_text)
        
        # 如果包含3個以上的規格關鍵詞，認為是結構化規格CSV
        return keyword_count >= 3
    
    def _setup_dynamic_parsing(self):
        """
        設置動態解析模式（適用於一般CSV）
        """
        if not self.datalist:
            raise Exception("CSV 資料為空")
        
        # 使用第一行作為標題行
        if len(self.datalist) > 0:
            self.headers = self.datalist[0]
            # 移除標題行
            self.datalist = self.datalist[1:]
        else:
            self.headers = []
        
        # 設置動態參數
        self.default_output_path = "./output.csv"
        
        # 創建動態規則（不進行規則匹配，直接使用原始資料）
        self._rules = None
        
        logger.info(f"動態解析設定 - 標題: {self.headers}, 資料行數: {len(self.datalist)}")

    def _dynamic_collect_results(self):
        """
        動態收集結果（適用於一般CSV）
        """
        self.processed_result = []
        valid_rows = 0
        empty_rows_skipped = 0
        
        for row in self.datalist:
            # 檢查是否為有效行：至少包含一個非空值
            if self._is_valid_row(row):
                # 確保行資料長度與標題匹配
                padded_row = row + [''] * (len(self.headers) - len(row))
                self.processed_result.append(padded_row[:len(self.headers)])
                valid_rows += 1
            else:
                empty_rows_skipped += 1
        
        logger.info(f"動態解析完成 - 處理了 {valid_rows} 行有效資料，跳過 {empty_rows_skipped} 行空資料")

    def _is_valid_row(self, row):
        """
        檢查行是否包含有效資料
        
        Args:
            row: CSV 行資料列表
            
        Returns:
            bool: 是否為有效行
        """
        if not row:
            return False
        
        # 檢查是否至少有一個非空值
        for cell in row:
            if cell and str(cell).strip():
                return True
        
        return False

    def collect_results(self):
        # 使用配置中的 model_count，如果未設定則預設為1
        model_count = self._rules[0][0].get("model_count", 1)
        result_rows = [[] for _ in range(model_count)]

        for rule_index, rule in enumerate(self._rules[1]):
            keywords = rule.get("keywords", [])
            logic = rule.get("logic", "OR").upper()
            rowspan = rule.get("rowspan", 1)
            column_name = rule.get("column_name", f"欄位{rule_index+1}")

            matched_blocks = []

            for i, row in enumerate(self.datalist):
                if logic == "AND":
                    match = True
                    for kw in keywords:
                        if not any(kw.lower() in str(cell).lower() for cell in row):
                            match = False
                            break
                else:
                    match = False
                    for kw in keywords:
                        if any(kw.lower() in str(cell).lower() for cell in row):
                            match = True
                            break

                if match:
                    block = self.datalist[i:i + rowspan]
                    matched_blocks.append((i, block))

            if len(matched_blocks) == 0:
                print(f"⚠️ 規則 {rule_index+1} - {column_name}: 找不到關鍵字 {keywords}，全欄填空白")
                for idx in range(model_count):
                    result_rows[idx].append("")
            else:
                if len(matched_blocks) > 1:
                    print(f"⚠️ 警告：規則 {rule_index+1} - {column_name} 找到超過一個匹配（共 {len(matched_blocks)} 個），僅使用第一筆！")
                first_index, block = matched_blocks[0]
                print(f"🔍 規則 {rule_index+1} - {column_name}: 找到關鍵字 {keywords} 於第 {first_index+1} 行")

                for idx in range(model_count):
                    col_index = 2 + idx
                    if all(col_index < len(row) for row in block):
                        lines = []
                        for r in block:
                            value = r[col_index].strip()
                            prefix_label = r[1].strip() if len(r) > 1 else ""
                            if prefix_label:
                                lines.append(f"{prefix_label}: {value}")
                            else:
                                lines.append(value)
                        result = "\n".join(lines).strip()
                        result_rows[idx].append(result)
                        print(f"  → 機種{idx+1}: {result}")
                    else:
                        result_rows[idx].append("")
                        print(f"  → 機種{idx+1}: ⚠️警告：該機種此處無資料")

        # 將結果轉為 dict 並存到 processed_result
        self.processed_result = []
        for row in result_rows:
            # 只根據 headers 組裝欄位，不自動加 modeltype
            row_dict = {}
            for i, header in enumerate(self.headers):
                row_dict[header] = row[i] if i < len(row) else ""
            self.processed_result.append(row_dict)
    

    # def write_csv(self, output_path, result_rows, headers, model_type):
    def write_csv(self):
        if self._rules is None:
            # 動態模式：直接使用標題
            headers = self.headers
        else:
            # 規則模式：添加 modeltype 欄位
            headers = ["modeltype"] + self.headers
        
        # 建立記憶體中的 processed_csv 資料結構
        self.processed_csv = []
        
        for row in self.processed_result:
            if self._rules is None:
                # 動態模式：直接映射資料
                row_dict = {}
                for i, header in enumerate(self.headers):
                    row_dict[header] = row[i] if i < len(row) else ""
            else:
                # 規則模式：添加 modeltype
                row_dict = {"modeltype": "dynamic"}
                for i, header in enumerate(self.headers):
                    row_dict[header] = row[i] if i < len(row) else ""
            self.processed_csv.append(row_dict)
        
        print(f"✅ 已建立記憶體資料：{len(self.processed_csv)} 筆記錄")
        
        # 保持原有的檔案輸出功能
        with open(self.default_output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for row in self.processed_result:
                writer.writerow([row[i] for i in range(len(row))])
        print(f"✅ 已輸出至：{self.default_output_path}")

    # 轉換 XLSX 為 CSV 檔案 cayman 20250722
    def convert_xlsx_to_csv_if_needed(self, file_path):
        if file_path.lower().endswith(".csv"):
            return file_path
        elif file_path.lower().endswith(".xlsx"):
            print(f"🔁 偵測到 XLSX 檔案，正在轉換為 CSV：{file_path}")
            df = pd.read_excel(file_path, sheet_name=0, header=None)
            temp_csv_path = os.path.join(tempfile.gettempdir(), "_converted_temp.csv")
            df.to_csv(temp_csv_path, index=False, header=False, encoding="utf-8-sig")
            print(f"✅ 已轉換為暫存 CSV：{temp_csv_path}")
            return temp_csv_path
        else:
            raise ValueError("❌ 僅支援 .csv 或 .xlsx 檔案！")

# def main():
#     parser = argparse.ArgumentParser(description="根據 JSON 規則搜尋 CSV 並轉為每機種一列格式（v4 + prefix 每列讀取）")
#     parser.add_argument("csv_path", help="輸入CSV")
#     parser.add_argument("json_path", help="規則JSON")
#     parser.add_argument("--model_count", type=int, required=True, help="幾個機種")
#     parser.add_argument("--model_type", type=str, required=True, help="共用的 model type 字串")
#     parser.add_argument("--output_csv", required=True, help="輸出CSV檔名")

#     args = parser.parse_args()

#     reader = load_csv(args.csv_path)
#     rules = load_rules(args.json_path)
#     results = collect_results(reader, rules, args.model_count)

#     headers = [
#         rule.get("column_name").strip() if rule.get("column_name") and rule.get("column_name").strip() != "" else f"欄位{i+1}"
#         for i, rule in enumerate(rules)
#     ]
#     write_csv(args.output_csv, results, headers, args.model_type)

# if __name__ == "__main__":
#     main()