#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試所有系列查詢功能
驗證960、928、AC01系列查詢是否正常工作
"""

import sys
import json
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# DEPRECATED: service.py does not exist anymore
# from libs.opmp_services.opmp_kernel.service import SalesAssistantService

def test_entity_recognition():
    """測試實體識別功能"""
    print("🔍 測試實體識別功能...")
    
    import re
    pattern = r'(?:819|839|928|958|960|AC01)(?=系列|型號|筆電|notebook|$|\s|[^\d])'
    
    test_cases = [
        ("請比較960系列的筆電", ["960"]),
        ("請比較928系列的筆電", ["928"]),
        ("請比較AC01系列的筆電", ["AC01"]),
        ("請比較819系列的筆電", ["819"]),
        ("請比較958系列的筆電", ["958"]),
        ("請比較656系列的筆電", []),  # 不存在的系列
    ]
    
    all_passed = True
    for query, expected in test_cases:
        matches = [m.group() for m in re.finditer(pattern, query)]
        if matches == expected:
            print(f"  ✅ \"{query}\" -> {matches}")
        else:
            print(f"  ❌ \"{query}\" -> {matches} (期望: {expected})")
            all_passed = False
    
    return all_passed

def test_get_models_by_type():
    """測試_get_models_by_type函數"""
    print("\n🔧 測試_get_models_by_type函數...")
    
    try:
        service = SalesAssistantService()
        
        test_series = ["960", "928", "AC01", "819", "958"]
        all_passed = True
        
        for series in test_series:
            try:
                models = service._get_models_by_type(series)
                if models:
                    print(f"  ✅ {series}系列: {models}")
                else:
                    print(f"  ❌ {series}系列: 未找到模型")
                    all_passed = False
            except Exception as e:
                print(f"  ❌ {series}系列: 查詢失敗 - {e}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"  ❌ 初始化服務失敗: {e}")
        return False

def test_parse_query_intent():
    """測試查詢意圖解析"""
    print("\n🧠 測試查詢意圖解析...")
    
    try:
        service = SalesAssistantService()
        
        test_queries = [
            "請比較960系列的筆電",
            "請比較928系列的筆電", 
            "請比較AC01系列的筆電",
            "請比較656系列的筆電"  # 不存在的系列
        ]
        
        all_passed = True
        
        for query in test_queries:
            try:
                intent = service._parse_query_intent(query)
                query_type = intent.get("query_type", "unknown")
                modeltypes = intent.get("modeltypes", [])
                
                if "656" in query:
                    # 656系列應該被識別但在後續步驟中處理
                    if query_type in ["model_type", "unknown"]:
                        print(f"  ✅ \"{query}\" -> {query_type}, modeltypes: {modeltypes}")
                    else:
                        print(f"  ❌ \"{query}\" -> {query_type} (期望: model_type或unknown)")
                        all_passed = False
                else:
                    # 存在的系列應該被正確識別
                    if query_type == "model_type" and modeltypes:
                        print(f"  ✅ \"{query}\" -> {query_type}, modeltypes: {modeltypes}")
                    else:
                        print(f"  ❌ \"{query}\" -> {query_type}, modeltypes: {modeltypes}")
                        all_passed = False
                        
            except Exception as e:
                print(f"  ❌ \"{query}\" -> 解析失敗: {e}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"  ❌ 初始化服務失敗: {e}")
        return False

def test_get_data_by_query_type():
    """測試資料獲取功能"""
    print("\n📊 測試資料獲取功能...")
    
    try:
        service = SalesAssistantService()
        
        test_cases = [
            {"query_type": "model_type", "modeltypes": ["960"], "modelnames": []},
            {"query_type": "model_type", "modeltypes": ["928"], "modelnames": []},
            {"query_type": "model_type", "modeltypes": ["AC01"], "modelnames": []},
        ]
        
        all_passed = True
        
        for test_case in test_cases:
            try:
                context_data, target_models = service._get_data_by_query_type(test_case)
                series = test_case["modeltypes"][0]
                
                if context_data and target_models:
                    print(f"  ✅ {series}系列: 找到 {len(context_data)} 筆資料, 模型: {target_models}")
                else:
                    print(f"  ❌ {series}系列: 未找到資料")
                    all_passed = False
                    
            except Exception as e:
                series = test_case["modeltypes"][0]
                print(f"  ❌ {series}系列: 資料獲取失敗 - {e}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"  ❌ 初始化服務失敗: {e}")
        return False

def test_error_handling():
    """測試錯誤處理"""
    print("\n⚠️  測試錯誤處理...")
    
    try:
        service = SalesAssistantService()
        
        # 測試不存在的系列
        try:
            test_case = {"query_type": "model_type", "modeltypes": ["656"], "modelnames": []}
            context_data, target_models = service._get_data_by_query_type(test_case)
            print("  ❌ 656系列: 應該拋出錯誤但沒有")
            return False
        except ValueError as e:
            if "656" in str(e):
                print(f"  ✅ 656系列: 正確拋出錯誤 - {e}")
            else:
                print(f"  ❌ 656系列: 錯誤訊息不正確 - {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ 測試錯誤處理失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🧪 系列查詢功能完整測試")
    print("=" * 60)
    
    test_results = []
    
    # 1. 測試實體識別
    test_results.append(("實體識別", test_entity_recognition()))
    
    # 2. 測試模型查詢  
    test_results.append(("模型查詢", test_get_models_by_type()))
    
    # 3. 測試意圖解析
    test_results.append(("意圖解析", test_parse_query_intent()))
    
    # 4. 測試資料獲取
    test_results.append(("資料獲取", test_get_data_by_query_type()))
    
    # 5. 測試錯誤處理
    test_results.append(("錯誤處理", test_error_handling()))
    
    # 總結報告
    print("\n" + "=" * 60)
    print("📋 測試結果總結:")
    
    passed_count = 0
    for test_name, passed in test_results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"  {test_name}: {status}")
        if passed:
            passed_count += 1
    
    print(f"\n🎯 總體結果: {passed_count}/{len(test_results)} 項測試通過")
    
    if passed_count == len(test_results):
        print("🎉 所有測試通過！960、928、AC01系列查詢功能正常")
        return True
    else:
        print("⚠️  部分測試失敗，需要進一步檢查")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)