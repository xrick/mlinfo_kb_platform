#!/usr/bin/env python3
"""
使用 raw_938.csv 進行 CSVParser2 實際測試
"""

import sys
import os
from pathlib import Path

# 添加父目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from csv_parser2 import CSVParser2


def test_with_raw_938():
    """使用 raw_938.csv 進行實際測試"""
    
    print("🚀 使用 raw_938.csv 測試 CSVParser2")
    print("=" * 50)
    
    # 初始化解析器
    parser = CSVParser2()
    
    # 設置檔案路徑
    raw_csv = Path(__file__).parent.parent.parent.parent.parent.parent / "refData" / "data" / "raw_938.csv"
    rules_file = Path(__file__).parent / "rules.json"
    
    print(f"📄 輸入檔案: {raw_csv}")
    print(f"📋 規則檔案: {rules_file}")
    
    if not raw_csv.exists():
        print(f"❌ 輸入檔案不存在: {raw_csv}")
        return False
    
    if not rules_file.exists():
        print(f"❌ 規則檔案不存在: {rules_file}")
        return False
    
    try:
        # 設置規則檔案路徑
        parser._rules_file = rules_file
        
        # 執行完整解析流程
        print("\n📋 階段 1: 解析前準備")
        if not parser.beforeParse(str(raw_csv)):
            print("❌ 解析前準備失敗")
            return False
        print("✅ 解析前準備成功")
        print(f"   模型數量: {parser.model_count}")
        print(f"   模型類型: {parser.model_type}")
        print(f"   欄位數量: {len(parser.headers)}")
        
        print("\n⚙️ 階段 2: 執行解析")
        results = parser.inParse()
        print(f"✅ 解析完成")
        print(f"   解析結果: {len(results)} 個模型")
        
        print("\n🔧 階段 3: 解析後處理")
        if not parser.endParse():
            print("❌ 解析後處理失敗")
            return False
        print("✅ 解析後處理成功")
        
        # 檢查輸出檔案
        output_file = Path(parser.default_output_path)
        if output_file.exists():
            print(f"\n📄 輸出檔案: {output_file}")
            print(f"📊 檔案大小: {output_file.stat().st_size} bytes")
            
            # 顯示檔案內容前幾行
            with open(output_file, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
                print(f"📋 檔案內容 (前 3 行):")
                for i, line in enumerate(lines[:3]):
                    print(f"   {i+1}: {line.strip()}")
            
            # 移動到標準位置供檢驗
            test_result_path = Path(__file__).parent / "test_result.csv"
            import shutil
            shutil.copy(output_file, test_result_path)
            print(f"\n✅ 測試結果已複製到: {test_result_path}")
            
        else:
            print(f"❌ 輸出檔案不存在: {output_file}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 測試過程發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函數"""
    success = test_with_raw_938()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 raw_938.csv 測試成功完成！")
    else:
        print("💥 raw_938.csv 測試失敗！")
    
    return success


if __name__ == "__main__":
    main()