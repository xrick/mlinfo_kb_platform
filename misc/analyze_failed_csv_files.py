#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析失敗的CSV檔案
"""

import pandas as pd
import sys
from pathlib import Path

# 添加libs目錄到Python路徑
sys.path.insert(0, str(Path(__file__).parent / 'libs'))

def analyze_failed_csv_files():
    """分析失敗的CSV檔案"""
    print("=== 分析失敗的CSV檔案 ===\n")
    
    # 失敗的檔案列表
    failed_files = [
        "17_result.csv",
        "AC01_result.csv", 
        "27_result.csv",
        "728_result.csv",
        "960_result.csv",
        "656_result.csv",
        "326_result.csv",
        "835_result.csv"
    ]
    
    csv_dir = Path("data/raw/EM_New TTL_241104_AllTransformedToGoogleSheet")
    
    for csv_file in failed_files:
        file_path = csv_dir / csv_file
        print(f"--- 分析檔案: {csv_file} ---")
        
        if not file_path.exists():
            print(f"   ❌ 檔案不存在: {file_path}")
            continue
            
        try:
            # 讀取CSV檔案
            df = pd.read_csv(file_path)
            print(f"   📊 檔案大小: {len(df)} 行, {len(df.columns)} 列")
            
            # 檢查必要欄位
            required_cols = ['modeltype', 'modelname']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                print(f"   ❌ 缺少必要欄位: {missing_cols}")
                continue
            
            # 檢查第一行數據
            first_row = df.iloc[0]
            print(f"   📋 第一行數據:")
            print(f"      modeltype: '{first_row.get('modeltype', 'N/A')}'")
            print(f"      modelname: '{first_row.get('modelname', 'N/A')}'")
            
            # 檢查是否為公司產品
            modelname = str(first_row.get('modelname', ''))
            modeltype = str(first_row.get('modeltype', ''))
            
            # 清理前綴
            if 'Model Name:' in modelname:
                modelname = modelname.replace('Model Name:', '').strip()
            if 'Version:' in modeltype:
                modeltype = modeltype.replace('Version:', '').strip()
            
            print(f"   🔧 清理後:")
            print(f"      modeltype: '{modeltype}'")
            print(f"      modelname: '{modelname}'")
            
            # 檢查公司產品驗證
            from mgfd_cursor.knowledge_base import NotebookKnowledgeBase
            kb = NotebookKnowledgeBase()
            
            # 模擬驗證過程
            is_company_product = kb._is_company_product(modelname)
            is_valid_modeltype = kb._is_valid_modeltype(modeltype)
            
            print(f"   ✅ 驗證結果:")
            print(f"      公司產品: {is_company_product}")
            print(f"      有效型號: {is_valid_modeltype}")
            
            if not is_company_product:
                print(f"   ❌ 失敗原因: 不是公司產品 (modelname: {modelname})")
            elif not is_valid_modeltype:
                print(f"   ❌ 失敗原因: 無效型號格式 (modeltype: {modeltype})")
            else:
                print(f"   ✅ 驗證通過")
            
            print()
            
        except Exception as e:
            print(f"   ❌ 讀取檔案失敗: {e}")
            print()

if __name__ == "__main__":
    analyze_failed_csv_files()
