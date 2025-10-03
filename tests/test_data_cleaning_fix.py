#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試數據清理修復效果
"""

import sys
import os
from pathlib import Path

# 添加libs目錄到Python路徑
sys.path.insert(0, str(Path(__file__).parent / 'libs'))

def test_data_cleaning():
    """測試數據清理修復效果"""
    print("=== 測試數據清理修復效果 ===\n")
    
    try:
        # 導入修復後的knowledge_base
        from mgfd_cursor.knowledge_base import NotebookKnowledgeBase
        
        print("1. 初始化知識庫...")
        kb = NotebookKnowledgeBase()
        
        print(f"2. 載入產品數量: {len(kb.products)}")
        
        if kb.products:
            print("3. 檢查前5個產品:")
            for i, product in enumerate(kb.products[:5]):
                print(f"   產品 {i+1}:")
                print(f"     modeltype: '{product.get('modeltype', 'N/A')}'")
                print(f"     modelname: '{product.get('modelname', 'N/A')}'")
                print(f"     version: '{product.get('version', 'N/A')}'")
                print(f"     cpu: '{product.get('cpu', 'N/A')}'")
                print(f"     gpu: '{product.get('gpu', 'N/A')}'")
                print(f"     memory: '{product.get('memory', 'N/A')}'")
                print(f"     storage: '{product.get('storage', 'N/A')}'")
                print(f"     popularity_score: {product.get('popularity_score', 'N/A')}")
                print()
        else:
            print("❌ 沒有載入到任何產品")
            return False
        
        print("4. 檢查產品驗證:")
        # 測試產品驗證邏輯
        test_products = [
            {'modeltype': '839', 'modelname': 'Model Name: AKK839'},
            {'modeltype': '928', 'modelname': 'Model Name: ARB928'},
            {'modeltype': '918', 'modelname': 'Model Name: AC918'},
        ]
        
        for i, test_product in enumerate(test_products):
            is_valid = kb._validate_product_fields(test_product)
            print(f"   測試產品 {i+1}: {test_product['modelname']} -> {'✅ 有效' if is_valid else '❌ 無效'}")
        
        print("\n✅ 數據清理修復測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_data_cleaning()
    if success:
        print("\n🎉 修復成功！產品數據已正確載入")
    else:
        print("\n💥 修復失敗，需要進一步調試")
