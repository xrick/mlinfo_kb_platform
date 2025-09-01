#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試停用enhanced_slot_extractor並分析問題
"""

import sys
import logging
from pathlib import Path

# 設置詳細日誌
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 添加libs目錄到Python路徑
sys.path.insert(0, str(Path(__file__).parent / 'libs'))

def test_without_enhanced_extractor():
    """測試不使用enhanced_slot_extractor的情況"""
    print("=== 測試停用Enhanced Slot Extractor ===\n")
    
    try:
        # 導入必要的模組
        from libs.UserInputHandler.UserInputHandler import UserInputHandler
        from mgfd_cursor.dialogue_manager import DialogueManager
        from mgfd_cursor.state_machine import DialogueStateMachine
        from mgfd_cursor.knowledge_base import NotebookKnowledgeBase
        
        print("1. 初始化組件...")
        
        # 初始化知識庫
        kb = NotebookKnowledgeBase()
        print(f"   知識庫載入產品數量: {len(kb.products)}")
        
        # 初始化對話管理器
        dialogue_manager = DialogueManager()
        
        # 初始化狀態機
        state_machine = DialogueStateMachine()
        
        # 創建一個簡化的UserInputHandler，不使用enhanced_extractor
        class SimpleUserInputHandler:
            def __init__(self, knowledge_base):
                self.knowledge_base = knowledge_base
                self.logger = logging.getLogger(__name__)
            
            def extract_slots_from_text(self, text: str, current_state: dict) -> dict:
                """簡化的槽位提取，不使用enhanced_extractor"""
                self.logger.info(f"簡化槽位提取，輸入: {text}")
                
                # 使用傳統的關鍵詞匹配
                extracted_slots = {}
                text_lower = text.lower()
                
                # 檢查使用目的
                if any(word in text_lower for word in ["遊戲", "gaming", "打遊戲"]):
                    extracted_slots["usage_purpose"] = "gaming"
                elif any(word in text_lower for word in ["工作", "business", "辦公", "商務"]):
                    extracted_slots["usage_purpose"] = "business"
                elif any(word in text_lower for word in ["學習", "student", "上課"]):
                    extracted_slots["usage_purpose"] = "student"
                elif any(word in text_lower for word in ["一般", "general", "日常"]):
                    extracted_slots["usage_purpose"] = "general"
                
                # 檢查預算範圍
                if any(word in text_lower for word in ["便宜", "budget", "經濟", "平價"]):
                    extracted_slots["budget_range"] = "budget"
                elif any(word in text_lower for word in ["中等", "mid_range", "中端"]):
                    extracted_slots["budget_range"] = "mid_range"
                elif any(word in text_lower for word in ["高級", "premium", "高端"]):
                    extracted_slots["budget_range"] = "premium"
                
                self.logger.info(f"簡化槽位提取結果: {extracted_slots}")
                return extracted_slots
            
            def _update_dialogue_state(self, current_state: dict, user_input: str, extracted_slots: dict) -> dict:
                """更新對話狀態"""
                updated_state = current_state.copy()
                filled_slots = updated_state.get("filled_slots", {})
                
                if extracted_slots:
                    filled_slots.update(extracted_slots)
                    self.logger.info(f"更新槽位: {extracted_slots}")
                
                updated_state["filled_slots"] = filled_slots
                return updated_state
        
        # 創建簡化的處理器
        simple_handler = SimpleUserInputHandler(kb)
        
        print("2. 測試用戶輸入處理...")
        
        # 測試用戶輸入
        test_inputs = [
            "請介紹目前比較新出來的筆電",
            "有適合遊戲的筆電嗎?",
            "輕便，開關機快，適合攜帶",
            "4~5萬"
        ]
        
        current_state = {
            "filled_slots": {},
            "session_id": "test_session_001",
            "chat_history": []
        }
        
        for i, user_input in enumerate(test_inputs):
            print(f"\n--- 測試 {i+1}: {user_input} ---")
            
            # 提取槽位
            extracted_slots = simple_handler.extract_slots_from_text(user_input, current_state)
            print(f"   提取的槽位: {extracted_slots}")
            
            # 更新狀態
            current_state = simple_handler._update_dialogue_state(current_state, user_input, extracted_slots)
            print(f"   更新後狀態: {current_state['filled_slots']}")
            
            # 檢查是否需要收集更多槽位
            required_slots = ["usage_purpose", "budget_range"]
            missing_slots = [slot for slot in required_slots if slot not in current_state["filled_slots"]]
            
            if missing_slots:
                print(f"   ⚠️  缺少必要槽位: {missing_slots}")
                print(f"   💡 應該詢問: {missing_slots[0] if missing_slots else '無'}")
            else:
                print(f"   ✅ 所有必要槽位已填寫，可以進行推薦")
        
        print("\n3. 分析問題...")
        print("   問題分析:")
        print("   - 簡化槽位提取器沒有自動填充槽位")
        print("   - 系統應該按照funnel流程收集槽位")
        print("   - 只有在所有必要槽位填寫後才進行推薦")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_without_enhanced_extractor()
    if success:
        print("\n🎉 測試完成！Enhanced Slot Extractor可能是問題來源")
    else:
        print("\n💥 測試失敗")
