#!/usr/bin/env python3
"""
CSV 解析器測試腳本

用於測試 CSVParser 類別的功能
"""

import sys
import os
import json
from pathlib import Path

# 添加父目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from csvparse import CSVParser


def test_csv_parser():
    """測試 CSV 解析器"""
    
    # 初始化解析器
    parser = CSVParser()
    
    # CSV 檔案路徑
    csv_file = Path(__file__).parent.parent.parent.parent.parent.parent / "refData" / "data" / "raw_938.csv"
    
    print(f"測試檔案路徑: {csv_file}")
    print(f"檔案是否存在: {csv_file.exists()}")
    
    if not csv_file.exists():
        print("錯誤: CSV 檔案不存在")
        return False
    
    try:
        # 執行解析流程
        print("\n=== 開始解析流程 ===")
        
        # 1. 解析前準備
        print("1. 執行 beforeParse...")
        if not parser.beforeParse(str(csv_file)):
            print("錯誤: beforeParse 失敗")
            return False
        print("✓ beforeParse 成功")
        
        # 2. 主要解析
        print("2. 執行 inParse...")
        results = parser.inParse()
        if not results:
            print("警告: inParse 沒有返回結果")
        else:
            print(f"✓ inParse 成功，提取 {len(results)} 條記錄")
        
        # 3. 解析後處理
        print("3. 執行 endParse...")
        if not parser.endParse():
            print("錯誤: endParse 失敗")
            return False
        print("✓ endParse 成功")
        
        # 4. 顯示解析結果
        print("\n=== 解析結果摘要 ===")
        categories = {}
        for item in results:
            category = item.get('category', 'unknown')
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        for category, count in categories.items():
            print(f"{category}: {count} 條記錄")
        
        # 5. 顯示詳細結果（前10條）
        print("\n=== 詳細結果（前10條）===")
        for i, item in enumerate(results[:10]):
            print(f"{i+1}. {item['category']} - {item['type']}: {item['value']}")
            print(f"   來源: {item['source']}")
            print(f"   原始資料: {item['raw_data'][:100]}...")
            print()
        
        # 6. 匯出結果
        output_file = Path(__file__).parent / "parsed_results.json"
        if parser.export_to_json(str(output_file)):
            print(f"✓ 結果已匯出到: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"測試過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=== CSV 解析器測試 ===")
    success = test_csv_parser()
    
    if success:
        print("\n✓ 測試完成")
    else:
        print("\n✗ 測試失敗")
        sys.exit(1) 