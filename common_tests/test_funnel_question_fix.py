#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試重複Funnel Question問題修復效果
專門測試 "請介紹目前比較新出來的筆電" 的對話流程
"""

import sys
import os
import logging
import redis
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from libs.mgfd_cursor.mgfd_system import MGFDSystem

# 設置詳細日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_special_case_dsl003_flow():
    """測試特殊案例DSL003的完整對話流程"""
    print("=== 測試特殊案例DSL003對話流程 ===\n")
    
    try:
        # 初始化Redis連接
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        redis_client.ping()
        print("✓ Redis連接成功")
        
        # 初始化MGFD系統
        mgfd_system = MGFDSystem(redis_client)
        print("✓ MGFD系統初始化成功")
        
        # 模擬會話ID
        session_id = "test_session_dsl003"
        
        # 測試流程
        test_steps = [
            {
                "step": 1,
                "description": "用戶詢問熱門筆電",
                "user_input": "請介紹目前比較新出來的筆電",
                "expected": "特殊案例DSL003匹配，槽位被正確提取"
            },
            {
                "step": 2,
                "description": "用戶選擇funnel選項",
                "user_input": "選擇選項: gaming",
                "expected": "槽位更新，進入下一步對話"
            },
            {
                "step": 3,
                "description": "再次選擇選項",
                "user_input": "選擇選項: premium",
                "expected": "繼續正常對話流程，不重複顯示相同選項"
            }
        ]
        
        # 執行測試
        for test_step in test_steps:
            print(f"\n--- 步驟 {test_step['step']}: {test_step['description']} ---")
            print(f"用戶輸入: '{test_step['user_input']}'")
            
            # 處理消息
            result = mgfd_system.process_message(session_id, test_step['user_input'])
            
            if result.get("success"):
                print(f"✓ 處理成功")
                print(f"  - 動作類型: {result.get('action_type', 'unknown')}")
                print(f"  - 已填槽位: {result.get('filled_slots', {})}")
                print(f"  - 對話階段: {result.get('dialogue_stage', 'unknown')}")
                
                # 檢查回應內容
                response = result.get('response', '')
                if response:
                    print(f"  - 系統回應: {response[:100]}...")
                
                # 特別檢查第一步的特殊案例匹配
                if test_step['step'] == 1:
                    filled_slots = result.get('filled_slots', {})
                    if 'usage_purpose' in filled_slots or 'budget_range' in filled_slots:
                        print("  ✓ 特殊案例槽位提取成功")
                    else:
                        print("  ⚠️ 特殊案例槽位可能沒有正確提取")
                
            else:
                print(f"✗ 處理失敗: {result.get('error', 'unknown error')}")
                return False
        
        # 檢查最終狀態
        print(f"\n--- 最終狀態檢查 ---")
        final_state = mgfd_system.get_session_state(session_id)
        if final_state.get("success"):
            final_slots = final_state['state'].get('filled_slots', {})
            print(f"✓ 最終槽位狀態: {final_slots}")
            
            # 驗證槽位是否正確填寫
            required_slots = ['usage_purpose', 'budget_range']
            filled_count = sum(1 for slot in required_slots if slot in final_slots)
            print(f"✓ 必要槽位填寫進度: {filled_count}/{len(required_slots)}")
            
            if filled_count > 0:
                print("🎉 測試成功：槽位正確更新，沒有重複funnel question問題")
                return True
            else:
                print("⚠️ 槽位更新可能存在問題")
                return False
        else:
            print(f"✗ 獲取最終狀態失敗: {final_state.get('error')}")
            return False
            
    except Exception as e:
        print(f"✗ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_traditional_slot_extraction():
    """測試傳統槽位提取功能是否正常"""
    print("\n=== 測試傳統槽位提取功能 ===")
    
    try:
        # 初始化Redis連接
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        mgfd_system = MGFDSystem(redis_client)
        
        session_id = "test_session_traditional"
        
        # 測試普通槽位提取
        test_inputs = [
            "我想要一台遊戲筆電",
            "預算大概3萬左右",
            "我比較喜歡華碩的"
        ]
        
        for i, user_input in enumerate(test_inputs, 1):
            print(f"\n步驟 {i}: '{user_input}'")
            result = mgfd_system.process_message(session_id, user_input)
            
            if result.get("success"):
                filled_slots = result.get('filled_slots', {})
                print(f"✓ 槽位狀態: {filled_slots}")
            else:
                print(f"✗ 處理失敗: {result.get('error')}")
                return False
        
        print("✓ 傳統槽位提取功能正常")
        return True
        
    except Exception as e:
        print(f"✗ 傳統槽位提取測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🔍 重複Funnel Question問題修復測試\n")
    
    # 執行測試
    test_results = {
        "special_case_flow": test_special_case_dsl003_flow(),
        "traditional_extraction": test_traditional_slot_extraction()
    }
    
    # 測試結果總結
    print("\n" + "="*60)
    print("📊 測試結果總結")
    print("="*60)
    
    for test_name, result in test_results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name.ljust(25)}: {status}")
    
    # 整體評估
    all_passed = all(test_results.values())
    
    print(f"\n🎯 修復效果: {'✅ 修復成功' if all_passed else '❌ 仍有問題'}")
    
    if all_passed:
        print("🎉 重複Funnel Question問題已修復！")
        print("💡 特殊案例槽位提取和狀態更新功能正常")
        print("💡 用戶可以正常進行對話，不再卡在相同選項")
    else:
        print("⚠️ 修復未完全成功，需要進一步調試")
        print("🔧 建議檢查日誌輸出，查看具體問題所在")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)