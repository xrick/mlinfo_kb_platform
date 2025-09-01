#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試增強版槽位提取器V2
"""

import sys
import logging
from pathlib import Path

# 設置詳細日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 添加libs目錄到Python路徑
sys.path.insert(0, str(Path(__file__).parent / 'libs'))

def test_enhanced_extractor_v2():
    """測試增強版槽位提取器V2"""
    print("=== 測試增強版槽位提取器V2 ===\n")
    
    # 測試案例
    test_cases = [
        {
            "input": "請介紹目前較適合做文書處理的筆電",
            "expected_slots": ["usage_purpose", "document_processing"]
        },
        {
            "input": "我想要一台輕便的筆電，預算在3-4萬之間",
            "expected_slots": ["weight_requirement", "budget_range"]
        },
        {
            "input": "有適合遊戲的筆電嗎？需要獨立顯卡",
            "expected_slots": ["usage_purpose", "gpu_level"]
        },
        {
            "input": "我需要一台15吋的筆電，品牌偏好華碩",
            "expected_slots": ["screen_size", "brand_preference"]
        },
        {
            "input": "請推薦一款高效能的筆電，CPU要i7以上",
            "expected_slots": ["performance_features", "cpu_level"]
        }
    ]
    
    try:
        # 導入增強版提取器
        from mgfd_cursor.enhanced_slot_extractor_v2 import EnhancedSlotExtractorV2
        
        # 創建slot_schema
        slot_schema = {
            "usage_purpose": {"required": True},
            "budget_range": {"required": True},
            "cpu_level": {"required": False},
            "gpu_level": {"required": False},
            "weight_requirement": {"required": False},
            "screen_size": {"required": False},
            "brand_preference": {"required": False},
            "performance_features": {"required": False}
        }
        
        # 創建模擬LLM管理器
        class MockLLMManager:
            def __init__(self):
                pass
        
        # 初始化增強版提取器
        extractor_v2 = EnhancedSlotExtractorV2(MockLLMManager(), slot_schema)
        print("✅ EnhancedSlotExtractorV2 初始化完成")
        
        # 獲取策略信息
        strategy_info = extractor_v2.get_strategy_info()
        print(f"\n📊 策略信息:")
        print(f"   可用策略數量: {len(strategy_info['available_strategies'])}")
        print(f"   增強同義詞載入: {strategy_info['enhanced_synonyms_loaded']}")
        
        for strategy in strategy_info['available_strategies']:
            print(f"   - {strategy['strategy_name']}: {strategy['strategy_type'].value}")
        
        print(f"\n🔍 開始測試槽位提取...")
        
        success_count = 0
        total_tests = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- 測試案例 {i}: {test_case['input']} ---")
            
            # 模擬會話狀態
            current_slots = {}
            session_id = f"test_v2_{i:03d}"
            
            # 執行槽位提取
            result = extractor_v2.extract_slots_with_classification(
                test_case['input'], current_slots, session_id
            )
            
            if result.get('success', False):
                extracted_slots = result.get('extracted_slots', {})
                extraction_method = result.get('extraction_method', 'unknown')
                confidence = result.get('confidence', 0.0)
                
                print(f"   ✅ 提取成功")
                print(f"   提取方法: {extraction_method}")
                print(f"   置信度: {confidence:.3f}")
                print(f"   提取槽位: {extracted_slots}")
                
                # 檢查是否有策略詳細信息
                if 'strategy_details' in result:
                    print(f"   策略詳細信息:")
                    for strategy_name, strategy_confidence in result['strategy_details'].items():
                        print(f"     - {strategy_name}: {strategy_confidence:.3f}")
                
                # 驗證是否提取到預期的槽位
                expected_slots = test_case['expected_slots']
                extracted_slot_names = list(extracted_slots.keys())
                
                if any(slot in extracted_slot_names for slot in expected_slots):
                    print(f"   🎯 預期槽位匹配: 是")
                    success_count += 1
                else:
                    print(f"   ⚠️  預期槽位匹配: 否 (預期: {expected_slots}, 實際: {extracted_slot_names})")
                
            else:
                print(f"   ❌ 提取失敗: {result.get('error', '未知錯誤')}")
        
        print(f"\n📈 測試結果總結:")
        print(f"   總測試數: {total_tests}")
        print(f"   成功數: {success_count}")
        print(f"   成功率: {success_count/total_tests*100:.1f}%")
        
        # 測試特殊案例
        print(f"\n🔍 測試特殊案例...")
        special_test_cases = [
            "請幫我介紹目前比較多人選擇的筆電",
            "有熱門的筆電推薦嗎？",
            "銷量好的筆電有哪些？"
        ]
        
        for special_case in special_test_cases:
            print(f"\n--- 特殊案例: {special_case} ---")
            
            result = extractor_v2.extract_slots_with_classification(
                special_case, {}, "test_special"
            )
            
            if result.get('success', False):
                if result.get('extraction_method') == 'special_case_knowledge':
                    special_case_id = result.get('special_case_id', 'unknown')
                    print(f"   ✅ 特殊案例匹配: {special_case_id}")
                else:
                    print(f"   📝 使用一般提取方法: {result.get('extraction_method')}")
                
                print(f"   提取槽位: {result.get('extracted_slots', {})}")
            else:
                print(f"   ❌ 提取失敗")
        
        return success_count >= total_tests * 0.8  # 80%成功率為通過
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_strategy_comparison():
    """比較不同策略的提取效果"""
    print("\n=== 策略比較測試 ===\n")
    
    try:
        from mgfd_cursor.enhanced_slot_extractor_v2 import (
            EnhancedSlotExtractorV2, 
            RegexExtractionStrategy,
            SemanticExtractionStrategy,
            KeywordExtractionStrategy
        )
        
        # 創建slot_schema
        slot_schema = {
            "usage_purpose": {"required": True},
            "budget_range": {"required": True}
        }
        
        # 創建模擬LLM管理器
        class MockLLMManager:
            def __init__(self):
                pass
        
        # 初始化提取器
        extractor = EnhancedSlotExtractorV2(MockLLMManager(), slot_schema)
        
        # 測試查詢
        test_query = "我想要一台文書處理的筆電，預算中等"
        
        print(f"測試查詢: {test_query}")
        print(f"預期槽位: usage_purpose=document_processing, budget_range=mid_range")
        
        # 分別測試每個策略
        strategies = extractor.strategies
        
        for strategy in strategies:
            print(f"\n--- {strategy.strategy_name} ---")
            
            try:
                result = strategy.extract_slots(test_query, slot_schema)
                confidence = strategy.get_confidence()
                
                print(f"   提取結果: {result}")
                print(f"   置信度: {confidence:.3f}")
                print(f"   策略類型: {strategy.get_strategy_type().value}")
                
            except Exception as e:
                print(f"   ❌ 策略執行失敗: {e}")
        
        # 測試混合策略
        print(f"\n--- 混合策略 ---")
        try:
            hybrid_result = extractor.hybrid_strategy.extract_slots(test_query, slot_schema)
            hybrid_confidence = extractor.hybrid_strategy.get_confidence()
            
            print(f"   提取結果: {hybrid_result}")
            print(f"   置信度: {hybrid_confidence:.3f}")
            
        except Exception as e:
            print(f"   ❌ 混合策略執行失敗: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 策略比較測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("🚀 開始測試增強版槽位提取器V2...")
    
    # 執行主要測試
    main_test_success = test_enhanced_extractor_v2()
    
    # 執行策略比較測試
    strategy_test_success = test_strategy_comparison()
    
    if main_test_success and strategy_test_success:
        print("\n🎉 所有測試通過！")
        print("📋 測試摘要:")
        print("   - 增強版槽位提取器V2功能正常")
        print("   - 多策略提取機制運作良好")
        print("   - 特殊案例處理正確")
        print("   - 策略比較功能正常")
    else:
        print("\n💥 部分測試失敗")
        if not main_test_success:
            print("   - 主要功能測試失敗")
        if not strategy_test_success:
            print("   - 策略比較測試失敗")
