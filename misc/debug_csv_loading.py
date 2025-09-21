#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV載入問題分析腳本
"""

import pandas as pd
import sys
from pathlib import Path

def analyze_csv_loading():
    """分析CSV載入問題"""
    print("=== CSV載入問題分析 ===\n")
    
    # 1. 檢查目錄結構
    data_dir = Path('data/raw/EM_New TTL_241104_AllTransformedToGoogleSheet')
    print(f"1. 檢查數據目錄: {data_dir}")
    print(f"   目錄存在: {data_dir.exists()}")
    print(f"   是目錄: {data_dir.is_dir()}")
    
    # 2. 查找CSV文件
    csv_files = list(data_dir.glob('*_result.csv'))
    print(f"\n2. 查找CSV文件:")
    print(f"   找到 {len(csv_files)} 個 *_result.csv 文件")
    
    # 3. 分析第一個CSV文件
    if csv_files:
        first_file = csv_files[0]
        print(f"\n3. 分析第一個文件: {first_file.name}")
        
        try:
            df = pd.read_csv(first_file, encoding='utf-8')
            print(f"   成功讀取，行數: {len(df)}")
            print(f"   列名: {list(df.columns)}")
            
            # 檢查必要欄位
            required_cols = ['modeltype', 'modelname']
            for col in required_cols:
                if col in df.columns:
                    value = df.iloc[0].get(col, 'NOT_FOUND')
                    print(f"   {col}: '{value}'")
                else:
                    print(f"   {col}: 欄位不存在")
            
            # 檢查數據格式問題
            print(f"\n4. 數據格式分析:")
            modelname = df.iloc[0].get('modelname', '')
            print(f"   modelname原始值: '{modelname}'")
            print(f"   modelname類型: {type(modelname)}")
            print(f"   modelname長度: {len(str(modelname))}")
            
            # 檢查是否包含前綴
            if isinstance(modelname, str) and 'Model Name:' in modelname:
                print(f"   ⚠️  發現問題: modelname包含'Model Name:'前綴")
                actual_name = modelname.replace('Model Name:', '').strip()
                print(f"   實際名稱: '{actual_name}'")
            
        except Exception as e:
            print(f"   讀取失敗: {e}")
    
    # 4. 測試多個文件
    print(f"\n5. 測試多個文件的modelname格式:")
    for i, file in enumerate(csv_files[:5]):
        try:
            df = pd.read_csv(file, encoding='utf-8')
            modelname = df.iloc[0].get('modelname', 'NOT_FOUND')
            print(f"   {file.name}: '{modelname}'")
        except Exception as e:
            print(f"   {file.name}: 讀取失敗 - {e}")

if __name__ == "__main__":
    analyze_csv_loading()
