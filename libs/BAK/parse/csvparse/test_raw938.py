#!/usr/bin/env python3
"""
測試 CSV 解析器處理 raw_938.csv 的功能
"""

import sys
import os
from pathlib import Path

# 添加父目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from csv_parser import CSVParser
import json


def test_raw938_parsing():
    """測試 raw_938.csv 解析功能"""
    
    # 初始化解析器
    parser = CSVParser()
    
    # CSV 檔案路徑
    csv_file = Path(__file__).parent.parent.parent.parent.parent.parent / "refData" / "data" / "raw_938.csv"
    
    print(f"🔍 測試 CSV 檔案: {csv_file}")
    
    if not csv_file.exists():
        print(f"❌ 檔案不存在: {csv_file}")
        return False
    
    try:
        # 1. 解析前準備
        print("\n📋 階段 1: 解析前準備")
        if not parser.beforeParse(str(csv_file)):
            print("❌ 解析前準備失敗")
            return False
        print("✅ 解析前準備成功")
        
        # 2. 執行解析
        print("\n⚙️ 階段 2: 執行解析")
        results = parser.inParse()
        print(f"✅ 解析完成，共提取 {len(results)} 條記錄")
        
        # 3. 解析後處理
        print("\n🔧 階段 3: 解析後處理")
        if not parser.endParse():
            print("❌ 解析後處理失敗")
            return False
        print("✅ 解析後處理成功")
        
        # 4. 分析結果
        print("\n📊 解析結果分析:")
        categories = {}
        for item in results:
            category = item.get('category', 'unknown')
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
        
        for category, items in categories.items():
            print(f"  📁 {category}: {len(items)} 條記錄")
            # 顯示前 3 條記錄
            for i, item in enumerate(items[:3]):
                print(f"    - {item.get('type', '')}: {item.get('value', '')}")
        
        # 5. 輸出結果到檔案
        output_file = Path(__file__).parent / "test_results.json"
        parser.export_to_json(str(output_file))
        print(f"\n💾 結果已儲存到: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試過程發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函數"""
    print("🚀 開始測試 CSV 解析器處理 raw_938.csv")
    print("=" * 50)
    
    success = test_raw938_parsing()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 測試成功完成！")
    else:
        print("💥 測試失敗！")
    
    return success


if __name__ == "__main__":
    main()