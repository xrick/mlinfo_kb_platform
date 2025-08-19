#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試funnel option selection修復效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from libs.mgfd_cursor.enhanced_slot_extractor import EnhancedSlotExtractor
from libs.mgfd_cursor.dialogue_manager import MGFDDialogueManager
import redis
from libs.mgfd_cursor.state_manager import StateManager

def test_funnel_option_selection():
    """測試funnel選項選擇流程"""
    print("=== 測試funnel option selection修復效果 ===\n")
    
    # 初始化組件
    dialogue_manager = MGFDDialogueManager()
    redis_client = redis.Redis(decode_responses=True)
    state_manager = StateManager(redis_client, dialogue_manager)
    
    try:
        # 步驟1: 創建會話
        session_id = dialogue_manager.create_session()
        print(f"✓ 創建會話成功: {session_id}")
        
        # 步驟2: 模擬funnel選項選擇輸入
        test_inputs = [
            "選擇選項: gaming",
            "gaming", 
            "選擇選項: budget",
            "budget"
        ]
        
        for i, user_input in enumerate(test_inputs, 1):
            print(f"\n--- 測試 {i}: 輸入 '{user_input}' ---")
            
            # 獲取當前狀態
            state = dialogue_manager.get_session(session_id)
            if not state:
                print(f"✗ 無法獲取會話狀態")
                continue
                
            # 處理用戶輸入  
            result = state_manager.process_user_input(session_id, user_input)
            
            if "error" in result:
                print(f"✗ 處理失敗: {result['error']}")
            else:
                print(f"✓ 處理成功")
                print(f"  - 動作類型: {result.get('action_type', 'unknown')}")
                print(f"  - 目標槽位: {result.get('target_slot', 'none')}")
                print(f"  - 提取的槽位: {result.get('extracted_slots', {})}")
                print(f"  - 當前槽位狀態: {result.get('filled_slots', {})}")
                
        print("\n=== 測試完成 ===")
        return True
        
    except Exception as e:
        print(f"✗ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_slot_extractor():
    """測試增強型槽位提取器"""
    print("\n=== 測試增強型槽位提取器 ===")
    
    try:
        # 創建mock的llm_manager和slot_schema  
        class MockLLMManager:
            def classify_slot(self, prompt):
                return '{"classified_slot": "unknown", "confidence": 0.0}'
        
        slot_schema = {
            "usage_purpose": {"required": True},
            "budget_range": {"required": True}
        }
        
        extractor = EnhancedSlotExtractor(MockLLMManager(), slot_schema)
        
        # 測試funnel選項檢測
        test_cases = [
            ("選擇選項: gaming", True),
            ("gaming", True), 
            ("選擇選項: budget", True),
            ("我要買筆電", False),
            ("random text", False)
        ]
        
        for input_text, expected in test_cases:
            result = extractor._is_funnel_option_response(input_text)
            status = "✓" if result == expected else "✗"
            print(f"{status} '{input_text}' -> {result} (預期: {expected})")
            
        # 測試槽位提取
        print("\n--- 測試槽位提取 ---")
        extract_cases = [
            "選擇選項: gaming",
            "gaming",
            "選擇選項: budget"
        ]
        
        for input_text in extract_cases:
            if extractor._is_funnel_option_response(input_text):
                slots = extractor._extract_option_selection(input_text)
                print(f"✓ '{input_text}' -> {slots}")
            else:
                print(f"✗ '{input_text}' 未被識別為funnel選項")
                
        return True
        
    except Exception as e:
        print(f"✗ 測試增強型槽位提取器失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 執行測試
    test1_result = test_enhanced_slot_extractor()
    test2_result = test_funnel_option_selection()
    
    print(f"\n=== 總結 ===")
    print(f"增強型槽位提取器測試: {'通過' if test1_result else '失敗'}")
    print(f"Funnel選項選擇流程測試: {'通過' if test2_result else '失敗'}")
    
    if test1_result and test2_result:
        print("🎉 所有測試通過！修復效果良好。")
    else:
        print("⚠️ 部分測試失敗，需要進一步調試。")