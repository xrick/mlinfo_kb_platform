#!/usr/bin/env python3
"""
測試完整的 CSV 處理流程：Raw CSV → Program → Processed CSV
"""

import sys
import os
from pathlib import Path
import pandas as pd

# 添加父目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from csv_parser import CSVParser


def test_csv_processing_flow():
    """測試完整的 CSV 處理流程"""
    
    print("🚀 測試 CSV 處理流程")
    print("Raw CSV → Program → Processed CSV")
    print("=" * 50)
    
    # 1. 輸入：Raw, Unprocessed CSV
    input_csv = Path(__file__).parent.parent.parent.parent.parent.parent / "refData" / "data" / "raw_938.csv"
    print(f"📥 輸入檔案: {input_csv.name}")
    
    if not input_csv.exists():
        print(f"❌ 輸入檔案不存在: {input_csv}")
        return False
    
    # 檢查輸入檔案資訊
    input_df = pd.read_csv(input_csv, encoding='utf-8')
    print(f"   原始資料: {len(input_df)} 行, {len(input_df.columns)} 欄")
    
    # 2. 程式處理
    print(f"\n⚙️ 程式處理階段")
    parser = CSVParser()
    
    try:
        # 執行完整的解析流程
        if parser.beforeParse(str(input_csv)):
            print("   ✅ 解析前準備完成")
        else:
            print("   ❌ 解析前準備失敗")
            return False
        
        results = parser.inParse()
        print(f"   ✅ 主要解析完成，提取 {len(results)} 條記錄")
        
        if parser.endParse():
            print("   ✅ 解析後處理完成")
        else:
            print("   ❌ 解析後處理失敗")
            return False
            
    except Exception as e:
        print(f"   ❌ 處理過程發生錯誤: {str(e)}")
        return False
    
    # 3. 輸出：Processed CSV Table
    output_csv = Path(__file__).parent / "processed_output.csv"
    print(f"\n📤 輸出檔案: {output_csv.name}")
    
    if not output_csv.exists():
        print(f"❌ 輸出檔案不存在: {output_csv}")
        return False
    
    # 檢查輸出檔案資訊
    try:
        output_df = pd.read_csv(output_csv, encoding='utf-8')
        print(f"   處理後資料: {len(output_df)} 行, {len(output_df.columns)} 欄")
        print(f"   檔案大小: {output_csv.stat().st_size} bytes")
        
        # 顯示輸出檔案的結構
        print(f"\n📋 輸出 CSV 結構:")
        print(f"   模型數量: {len(output_df)}")
        print(f"   欄位數量: {len(output_df.columns)}")
        
        # 顯示前幾個欄位
        print(f"   主要欄位:")
        for i, col in enumerate(output_df.columns[:8]):
            print(f"     {i+1}. {col}")
        
        if len(output_df.columns) > 8:
            print(f"     ... 還有 {len(output_df.columns) - 8} 個欄位")
        
        # 顯示第一行資料的部分內容
        if len(output_df) > 0:
            print(f"\n📄 第一個模型的部分資料:")
            first_row = output_df.iloc[0]
            for col in output_df.columns[:5]:
                value = first_row[col]
                if pd.notna(value) and str(value).strip():
                    print(f"     {col}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 讀取輸出檔案失敗: {str(e)}")
        return False


def main():
    """主函數"""
    success = test_csv_processing_flow()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 CSV 處理流程測試成功！")
        print("✅ Raw CSV → Program → Processed CSV 流程正常運作")
    else:
        print("💥 CSV 處理流程測試失敗！")
    
    return success


if __name__ == "__main__":
    main()