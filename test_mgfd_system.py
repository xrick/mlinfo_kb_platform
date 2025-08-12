#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD 系統測試
"""

import sys
from pathlib import Path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from libs.mgfd_cursor import MGFDDialogueManager, create_notebook_sales_graph

def test_mgfd_system():
    """測試MGFD系統"""
    print("🧪 開始測試 MGFD 系統...")
    
    # 初始化系統
    print("\n1. 初始化 MGFD 系統...")
    state_machine = create_notebook_sales_graph()
    dialogue_manager = state_machine.dialogue_manager
    
    # 創建會話
    print("\n2. 創建新會話...")
    session_id = dialogue_manager.create_session()
    print(f"   會話ID: {session_id}")
    
    # 測試對話流程
    test_conversations = [
        "我想要一台遊戲筆電",
        "預算大概3萬左右",
        "品牌偏好華碩",
        "需要經常攜帶"
    ]
    
    print("\n3. 開始對話測試...")
    for i, user_input in enumerate(test_conversations, 1):
        print(f"\n   回合 {i}:")
        print(f"   用戶: {user_input}")
        
        result = state_machine.process_user_input(session_id, user_input)
        
        print(f"   系統回應: {result['response']}")
        print(f"   行動類型: {result['action_type']}")
        print(f"   已填寫槽位: {result['filled_slots']}")
        print(f"   當前階段: {result['current_stage']}")
        
        if result.get('recommendations'):
            print(f"   推薦產品數量: {len(result['recommendations'])}")
    
    # 測試統計信息
    print("\n4. 測試統計信息...")
    stats = dialogue_manager.get_session_stats()
    print(f"   活躍會話: {stats['active_sessions']}")
    print(f"   產品數量: {stats['total_products']}")
    print(f"   槽位架構: {stats['slot_schema_count']}")
    
    # 測試產品搜索
    print("\n5. 測試產品搜索...")
    search_results = dialogue_manager.notebook_kb.semantic_search("遊戲")
    print(f"   搜索'遊戲'結果數量: {len(search_results)}")
    
    # 測試產品過濾
    print("\n6. 測試產品過濾...")
    preferences = {
        "usage_purpose": "gaming",
        "budget_range": "premium",
        "brand_preference": "asus"
    }
    filtered_products = dialogue_manager.notebook_kb.filter_products(preferences)
    print(f"   根據偏好過濾結果數量: {len(filtered_products)}")
    
    print("\n✅ MGFD 系統測試完成！")

def test_error_handling():
    """測試錯誤處理"""
    print("\n🧪 測試錯誤處理...")
    
    state_machine = create_notebook_sales_graph()
    
    # 測試無效會話ID
    print("\n1. 測試無效會話ID...")
    result = state_machine.process_user_input("invalid_session_id", "測試消息")
    print(f"   結果: {result.get('error', '無錯誤')}")
    
    # 測試中斷意圖
    print("\n2. 測試中斷意圖...")
    session_id = state_machine.dialogue_manager.create_session()
    result = state_machine.process_user_input(session_id, "重新開始")
    print(f"   行動類型: {result['action_type']}")
    print(f"   回應: {result['response']}")
    
    print("\n✅ 錯誤處理測試完成！")

if __name__ == "__main__":
    try:
        test_mgfd_system()
        test_error_handling()
        print("\n🎉 所有測試通過！")
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()



