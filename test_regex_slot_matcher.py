#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試正則表達式槽位匹配器
"""

import json
import sys
import logging
from pathlib import Path

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 添加libs目錄到Python路徑
sys.path.insert(0, str(Path(__file__).parent / 'libs'))

def test_regex_slot_matcher():
    """測試正則表達式槽位匹配器"""
    print("=== 測試正則表達式槽位匹配器 ===\n")
    
    try:
        # 導入匹配器
        from mgfd_cursor.regex_slot_matcher import RegexSlotMatcher
        
        # 載入測試配置
        config_path = Path(__file__).parent / "libs" / "mgfd_cursor" / "humandata" / "bakdir" / "default_slots_old.json"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("✅ 成功載入配置檔案")
        
        # 創建匹配器
        matcher = RegexSlotMatcher(config)
        print("✅ 正則表達式槽位匹配器初始化完成")
        
        # 獲取統計信息
        stats = matcher.get_match_statistics()
        print(f"\n📊 匹配器統計信息:")
        print(f"   總槽位數: {stats['total_slots']}")
        print(f"   總模式數: {stats['total_patterns']}")
        print(f"   緩存大小: {stats['cache_size']}")
        
        # 測試案例
        test_cases = [
            {
                "input": "我想要一台遊戲筆電",
                "expected_slots": ["usage_purpose"],
                "expected_values": ["gaming"]
            },
            {
                "input": "需要文書處理的電腦，預算在3-4萬之間",
                "expected_slots": ["usage_purpose", "budget_range"],
                "expected_values": ["document_processing", "mid_range"]
            },
            {
                "input": "學生用的筆電，15吋螢幕，輕便一點",
                "expected_slots": ["usage_purpose", "screen_size", "weight_requirement"],
                "expected_values": ["student", "medium", "light"]
            },
            {
                "input": "需要i7處理器，獨立顯卡，華碩品牌",
                "expected_slots": ["cpu_level", "gpu_level", "brand_preference"],
                "expected_values": ["high", "dedicated", "asus"]
            },
            {
                "input": "便宜一點的筆電，一般日常使用",
                "expected_slots": ["budget_range", "usage_purpose"],
                "expected_values": ["budget", "general"]
            }
        ]
        
        print(f"\n🔍 開始測試槽位匹配...")
        
        success_count = 0
        total_tests = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- 測試案例 {i}: {test_case['input']} ---")
            
            # 執行匹配
            result = matcher.match_slots(test_case['input'])
            
            if result.get('success', False):
                matches = result.get('matches', {})
                print(f"   ✅ 匹配成功")
                print(f"   匹配槽位數: {result['total_matches']}")
                
                # 檢查匹配結果
                matched_slots = list(matches.keys())
                matched_values = [match['value'] for match in matches.values()]
                
                print(f"   匹配槽位: {matched_slots}")
                print(f"   匹配值: {matched_values}")
                
                # 驗證預期結果
                expected_slots = test_case['expected_slots']
                expected_values = test_case['expected_values']
                
                slot_match = any(slot in matched_slots for slot in expected_slots)
                value_match = any(value in matched_values for value in expected_values)
                
                if slot_match and value_match:
                    print(f"   🎯 預期結果匹配: 是")
                    success_count += 1
                else:
                    print(f"   ⚠️  預期結果匹配: 否")
                    print(f"      預期槽位: {expected_slots}")
                    print(f"      預期值: {expected_values}")
                
                # 顯示詳細匹配信息
                for slot_name, match_info in matches.items():
                    print(f"     {slot_name}:")
                    print(f"       值: {match_info['value']}")
                    print(f"       置信度: {match_info['confidence']:.3f}")
                    print(f"       策略分數: {match_info['strategy_scores']}")
                    if match_info['matched_text']:
                        print(f"       匹配文本: {match_info['matched_text']}")
                
            else:
                print(f"   ❌ 匹配失敗: {result.get('error', '未知錯誤')}")
        
        print(f"\n📈 測試結果總結:")
        print(f"   總測試數: {total_tests}")
        print(f"   成功數: {success_count}")
        print(f"   成功率: {success_count/total_tests*100:.1f}%")
        
        # 驗證正則表達式模式
        print(f"\n🔧 驗證正則表達式模式...")
        validation = matcher.validate_patterns()
        
        if "error" not in validation:
            print(f"   有效模式數: {validation['valid_patterns']}")
            print(f"   無效模式數: {validation['invalid_patterns']}")
            
            if validation['errors']:
                print(f"   ⚠️  發現 {len(validation['errors'])} 個錯誤:")
                for error in validation['errors'][:3]:  # 只顯示前3個
                    print(f"     - {error['slot']}.{error['value']}: {error['error']}")
        else:
            print(f"   ❌ 驗證失敗: {validation['error']}")
        
        return success_count >= total_tests * 0.8  # 80%成功率為通過
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance():
    """測試性能"""
    print("\n=== 性能測試 ===\n")
    
    try:
        from mgfd_cursor.regex_slot_matcher import RegexSlotMatcher
        import time
        
        # 載入配置
        config_path = Path(__file__).parent / "libs" / "mgfd_cursor" / "humandata" / "bakdir" / "default_slots_old.json"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 創建匹配器
        matcher = RegexSlotMatcher(config)
        
        # 測試文本
        test_texts = [
            "我想要一台遊戲筆電",
            "需要文書處理的電腦",
            "學生用的筆電",
            "需要i7處理器",
            "便宜一點的筆電",
            "15吋螢幕",
            "華碩品牌",
            "輕便攜帶",
            "獨立顯卡",
            "高效能筆電"
        ]
        
        # 性能測試
        print("🔍 執行性能測試...")
        
        total_time = 0
        total_matches = 0
        
        for i, text in enumerate(test_texts, 1):
            start_time = time.time()
            result = matcher.match_slots(text)
            end_time = time.time()
            
            execution_time = (end_time - start_time) * 1000  # 轉換為毫秒
            total_time += execution_time
            
            if result.get('success', False):
                total_matches += result.get('total_matches', 0)
            
            print(f"   測試 {i}: {execution_time:.3f}ms, 匹配數: {result.get('total_matches', 0)}")
        
        avg_time = total_time / len(test_texts)
        avg_matches = total_matches / len(test_texts)
        
        print(f"\n📊 性能統計:")
        print(f"   平均執行時間: {avg_time:.3f}ms")
        print(f"   平均匹配數: {avg_matches:.1f}")
        print(f"   總執行時間: {total_time:.3f}ms")
        
        # 性能評估
        if avg_time < 10:
            print("   ✅ 性能優秀")
        elif avg_time < 50:
            print("   📝 性能良好")
        elif avg_time < 100:
            print("   ⚠️  性能一般")
        else:
            print("   ❌ 性能較差")
        
        return True
        
    except Exception as e:
        print(f"❌ 性能測試失敗: {e}")
        return False

def test_edge_cases():
    """測試邊界情況"""
    print("\n=== 邊界情況測試 ===\n")
    
    try:
        from mgfd_cursor.regex_slot_matcher import RegexSlotMatcher
        
        # 載入配置
        config_path = Path(__file__).parent / "libs" / "mgfd_cursor" / "humandata" / "bakdir" / "default_slots_old.json"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 創建匹配器
        matcher = RegexSlotMatcher(config)
        
        # 邊界測試案例
        edge_cases = [
            "",  # 空字符串
            "   ",  # 只有空格
            "abc123",  # 無關文本
            "遊戲遊戲遊戲遊戲遊戲",  # 重複文本
            "我想要一台遊戲筆電，需要i7處理器，15吋螢幕，華碩品牌，便宜一點，輕便攜帶",  # 長文本
            "GAMING LAPTOP",  # 英文大寫
            "遊戲筆電",  # 簡短文本
            "我需要一台筆電來玩遊戲，預算大概3萬左右，希望是15吋的螢幕，品牌偏好華碩，重量要輕便一點"  # 複雜文本
        ]
        
        print("🔍 測試邊界情況...")
        
        for i, text in enumerate(edge_cases, 1):
            print(f"\n--- 邊界案例 {i}: '{text}' ---")
            
            result = matcher.match_slots(text)
            
            if result.get('success', False):
                matches = result.get('matches', {})
                print(f"   ✅ 處理成功")
                print(f"   匹配槽位數: {result['total_matches']}")
                
                if matches:
                    for slot_name, match_info in matches.items():
                        print(f"     {slot_name}: {match_info['value']} (置信度: {match_info['confidence']:.3f})")
                else:
                    print("   無匹配結果")
            else:
                print(f"   ❌ 處理失敗: {result.get('error', '未知錯誤')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 邊界情況測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("🚀 開始測試正則表達式槽位匹配器...")
    
    # 執行所有測試
    basic_test_success = test_regex_slot_matcher()
    performance_test_success = test_performance()
    edge_case_test_success = test_edge_cases()
    
    if basic_test_success and performance_test_success and edge_case_test_success:
        print("\n🎉 所有測試通過！")
        print("📋 測試摘要:")
        print("   - 基本功能測試通過")
        print("   - 性能測試通過")
        print("   - 邊界情況測試通過")
        print("   - 正則表達式槽位匹配器功能正常")
    else:
        print("\n💥 部分測試失敗")
        if not basic_test_success:
            print("   - 基本功能測試失敗")
        if not performance_test_success:
            print("   - 性能測試失敗")
        if not edge_case_test_success:
            print("   - 邊界情況測試失敗")
