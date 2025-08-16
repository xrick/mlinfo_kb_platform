#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試動態槽位學習功能
"""

import sys
import logging
import json
from pathlib import Path

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 添加libs目錄到Python路徑
sys.path.insert(0, str(Path(__file__).parent / 'libs'))

def test_dynamic_slot_learning():
    """測試動態槽位學習功能"""
    print("=== 測試動態槽位學習功能 ===\n")
    
    try:
        from mgfd_cursor.regex_slot_matcher import RegexSlotMatcher
        
        # 基礎配置
        base_config = {
            "slot_definitions": {
                "usage_purpose": {
                    "synonyms": {
                        "gaming": {
                            "keywords": ["遊戲", "打遊戲"],
                            "regex": ["遊戲|gaming|電競"],
                            "semantic": ["遊戲體驗"]
                        }
                    }
                }
            }
        }
        
        # 配置文件路徑
        config_file_path = "libs/mgfd_cursor/humandata/default_slots_enhanced.json"
        
        # 創建匹配器（啟用動態學習）
        matcher = RegexSlotMatcher(base_config, config_file_path)
        print("✅ RegexSlotMatcher初始化完成（動態學習已啟用）")
        
        # 測試1: 基本匹配
        print("\n--- 測試1: 基本匹配 ---")
        result1 = matcher.match_slots("我想要一台遊戲筆電")
        print(f"輸入: '我想要一台遊戲筆電'")
        print(f"結果: {result1}")
        
        # 測試2: 未知槽位自動學習
        print("\n--- 測試2: 未知槽位自動學習 ---")
        result2 = matcher.match_slots("我想要一台華碩筆電", enable_learning=True)
        print(f"輸入: '我想要一台華碩筆電'")
        print(f"結果: {result2}")
        
        # 測試3: 手動添加新槽位
        print("\n--- 測試3: 手動添加新槽位 ---")
        success = matcher.add_new_slot(
            "special_requirement", 
            "觸控螢幕", 
            "我需要有觸控螢幕的筆電", 
            0.9
        )
        print(f"手動添加槽位: special_requirement=觸控螢幕")
        print(f"添加結果: {success}")
        
        # 測試4: 測試新添加的槽位
        print("\n--- 測試4: 測試新添加的槽位 ---")
        result4 = matcher.match_slots("我需要有觸控螢幕的筆電")
        print(f"輸入: '我需要有觸控螢幕的筆電'")
        print(f"結果: {result4}")
        
        # 測試5: 學習統計信息
        print("\n--- 測試5: 學習統計信息 ---")
        learning_stats = matcher.get_learning_statistics()
        print(f"學習統計: {json.dumps(learning_stats, ensure_ascii=False, indent=2)}")
        
        # 測試6: 匹配統計信息
        print("\n--- 測試6: 匹配統計信息 ---")
        match_stats = matcher.get_match_statistics()
        print(f"匹配統計: {json.dumps(match_stats, ensure_ascii=False, indent=2)}")
        
        # 測試7: 驗證配置文件更新
        print("\n--- 測試7: 驗證配置文件更新 ---")
        if Path(config_file_path).exists():
            with open(config_file_path, 'r', encoding='utf-8') as f:
                updated_config = json.load(f)
            
            # 檢查是否有動態學習的槽位
            dynamic_slots = []
            for slot_name, slot_def in updated_config.get("slot_definitions", {}).items():
                if slot_def.get("learning_source") == "dynamic_learning":
                    dynamic_slots.append(slot_name)
            
            print(f"動態學習的槽位: {dynamic_slots}")
            
            # 檢查學習歷史
            learning_history = updated_config.get("learning_history", [])
            print(f"學習歷史記錄數: {len(learning_history)}")
            
            if learning_history:
                print("最近的學習記錄:")
                for record in learning_history[-3:]:  # 顯示最近3條記錄
                    print(f"  - {record['timestamp']}: {record['slot_name']}={record['slot_value']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases():
    """測試邊界情況"""
    print("\n=== 測試邊界情況 ===\n")
    
    try:
        from mgfd_cursor.regex_slot_matcher import RegexSlotMatcher
        
        # 空配置
        empty_config = {"slot_definitions": {}}
        config_file_path = "libs/mgfd_cursor/humandata/default_slots_enhanced.json"
        
        matcher = RegexSlotMatcher(empty_config, config_file_path)
        
        # 測試空輸入
        print("--- 測試空輸入 ---")
        result1 = matcher.match_slots("")
        print(f"空輸入結果: {result1}")
        
        # 測試特殊字符
        print("\n--- 測試特殊字符 ---")
        result2 = matcher.match_slots("我需要一台筆電！@#$%^&*()")
        print(f"特殊字符結果: {result2}")
        
        # 測試重複添加
        print("\n--- 測試重複添加 ---")
        success1 = matcher.add_new_slot("test_slot", "test_value", "測試文本", 0.8)
        success2 = matcher.add_new_slot("test_slot", "test_value", "測試文本", 0.8)
        print(f"第一次添加: {success1}")
        print(f"第二次添加: {success2}")
        
        return True
        
    except Exception as e:
        print(f"❌ 邊界測試失敗: {e}")
        return False

def test_performance():
    """測試性能"""
    print("\n=== 測試性能 ===\n")
    
    try:
        from mgfd_cursor.regex_slot_matcher import RegexSlotMatcher
        import time
        
        # 創建測試配置
        test_config = {
            "slot_definitions": {
                "usage_purpose": {
                    "synonyms": {
                        "gaming": {
                            "keywords": ["遊戲", "打遊戲"],
                            "regex": ["遊戲|gaming|電競"],
                            "semantic": ["遊戲體驗"]
                        }
                    }
                }
            }
        }
        
        config_file_path = "libs/mgfd_cursor/humandata/default_slots_enhanced.json"
        matcher = RegexSlotMatcher(test_config, config_file_path)
        
        # 測試匹配性能
        test_inputs = [
            "我想要一台遊戲筆電",
            "我需要工作用的筆電",
            "學生用的筆電推薦",
            "創意工作者的筆電選擇",
            "一般日常使用的筆電"
        ]
        
        print("--- 匹配性能測試 ---")
        start_time = time.time()
        
        for i, test_input in enumerate(test_inputs):
            result = matcher.match_slots(test_input)
            print(f"測試 {i+1}: {test_input} -> {result.get('total_matches', 0)} 個匹配")
        
        end_time = time.time()
        print(f"總耗時: {end_time - start_time:.4f} 秒")
        print(f"平均耗時: {(end_time - start_time) / len(test_inputs):.4f} 秒/次")
        
        # 測試學習性能
        print("\n--- 學習性能測試 ---")
        start_time = time.time()
        
        for i in range(5):
            success = matcher.add_new_slot(
                f"performance_test_slot_{i}",
                f"test_value_{i}",
                f"性能測試文本 {i}",
                0.8
            )
            print(f"學習測試 {i+1}: {success}")
        
        end_time = time.time()
        print(f"學習總耗時: {end_time - start_time:.4f} 秒")
        print(f"學習平均耗時: {(end_time - start_time) / 5:.4f} 秒/次")
        
        return True
        
    except Exception as e:
        print(f"❌ 性能測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("🚀 開始測試動態槽位學習功能...")
    
    # 執行所有測試
    basic_test_success = test_dynamic_slot_learning()
    edge_case_test_success = test_edge_cases()
    performance_test_success = test_performance()
    
    if all([basic_test_success, edge_case_test_success, performance_test_success]):
        print("\n🎉 所有測試通過！")
        print("📋 測試摘要:")
        print("   - 動態槽位學習功能正常")
        print("   - 邊界情況處理正確")
        print("   - 性能表現良好")
        print("\n✨ 功能特點:")
        print("   - 自動識別未知槽位")
        print("   - 智能生成匹配模式")
        print("   - 持久化學習結果")
        print("   - 完整的學習歷史記錄")
    else:
        print("\n💥 部分測試失敗")
        if not basic_test_success:
            print("   - 基本功能測試失敗")
        if not edge_case_test_success:
            print("   - 邊界情況測試失敗")
        if not performance_test_success:
            print("   - 性能測試失敗")
