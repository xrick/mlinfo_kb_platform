#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析enhanced_slot_extractor的問題
"""

import sys
import logging
from pathlib import Path

# 設置詳細日誌
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 添加libs目錄到Python路徑
sys.path.insert(0, str(Path(__file__).parent / 'libs'))

def analyze_enhanced_extractor():
    """分析enhanced_slot_extractor的問題"""
    print("=== 分析Enhanced Slot Extractor問題 ===\n")
    
    try:
        # 直接導入enhanced_slot_extractor
        from mgfd_cursor.enhanced_slot_extractor import EnhancedSlotExtractor
        
        print("1. 分析特殊案例知識庫...")
        
        # 檢查特殊案例DSL003
        from mgfd_cursor.special_cases_knowledge import SpecialCasesKnowledgeBase
        
        knowledge_base = SpecialCasesKnowledgeBase()
        
        # 測試DSL003匹配
        test_query = "請介紹目前比較新出來的筆電"
        matched_case = knowledge_base.find_matching_case(test_query)
        
        if matched_case:
            print(f"   找到匹配案例: {matched_case.get('case_id', 'unknown')}")
            print(f"   案例內容: {matched_case}")
            
            # 檢查推斷的槽位
            detected_intent = matched_case.get('detected_intent', {})
            inferred_slots = detected_intent.get('inferred_slots', {})
            print(f"   推斷的槽位: {inferred_slots}")
            
            # 檢查推薦回應
            recommended_response = matched_case.get('recommended_response', {})
            print(f"   推薦回應類型: {recommended_response.get('response_type', 'unknown')}")
            print(f"   跳過通用問題: {recommended_response.get('skip_generic_usage_question', False)}")
            
            # 這裡發現問題！
            if recommended_response.get('skip_generic_usage_question', False):
                print("   ⚠️  問題發現: 特殊案例DSL003設置了skip_generic_usage_question=True")
                print("   💥 這導致系統跳過了正常的funnel流程，直接進行推薦")
        else:
            print("   沒有找到匹配案例")
        
        print("\n2. 分析enhanced_slot_extractor的處理流程...")
        
        # 模擬enhanced_slot_extractor的處理
        current_slots = {}
        session_id = "test_session"
        
        # 創建一個模擬的LLM管理器
        class MockLLMManager:
            def __init__(self):
                pass
        
        # 創建slot_schema
        slot_schema = {
            "usage_purpose": {"required": True},
            "budget_range": {"required": True}
        }
        
        # 初始化enhanced_extractor
        enhanced_extractor = EnhancedSlotExtractor(MockLLMManager(), slot_schema)
        
        # 測試槽位提取
        result = enhanced_extractor.extract_slots_with_classification(
            test_query, current_slots, session_id
        )
        
        print(f"   提取結果: {result}")
        print(f"   提取方法: {result.get('extraction_method', 'unknown')}")
        print(f"   提取的槽位: {result.get('extracted_slots', {})}")
        
        if result.get('extraction_method') == 'special_case_knowledge':
            special_case = result.get('special_case', {})
            print(f"   特殊案例: {special_case.get('case_id', 'unknown')}")
            
            # 檢查是否跳過了funnel流程
            recommended_response = special_case.get('recommended_response', {})
            if recommended_response.get('skip_generic_usage_question', False):
                print("   💥 確認問題: 系統跳過了funnel流程")
                print("   🔧 解決方案: 需要修改特殊案例配置或處理邏輯")
        
        print("\n3. 問題根源分析...")
        print("   問題根源:")
        print("   1. 特殊案例DSL003設置了skip_generic_usage_question=True")
        print("   2. 這導致系統跳過了正常的槽位收集流程")
        print("   3. 直接進入產品推薦階段，但產品規格顯示undefined")
        print("   4. 因為RAG系統可能沒有正確初始化或產品數據有問題")
        
        print("\n4. 解決方案建議...")
        print("   方案1: 修改特殊案例DSL003的配置")
        print("   方案2: 修改enhanced_slot_extractor的處理邏輯")
        print("   方案3: 確保RAG系統正確初始化")
        print("   方案4: 檢查產品數據格式和載入")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = analyze_enhanced_extractor()
    if success:
        print("\n🎉 分析完成！找到問題根源")
    else:
        print("\n💥 分析失敗")
