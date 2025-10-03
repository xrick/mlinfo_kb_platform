#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-round Funnel Conversation 測試腳本
驗證漏斗對話系統的完整功能
"""

import asyncio
import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

# DEPRECATED: multichat directory does not exist anymore
# from libs.opmp_services.opmp_kernel.multichat.funnel_manager import (
#     FunnelConversationManager, FunnelQueryType, FunnelFlowType
# )

def test_query_classification():
    """測試查詢分類功能"""
    print("=" * 80)
    print("🧪 測試查詢分類功能")
    print("=" * 80)
    
    funnel_manager = FunnelConversationManager()
    
    test_cases = [
        # 系列比較查詢
        ("比較958系列哪款筆記型電腦更適合遊戲？", FunnelQueryType.MIXED_AMBIGUOUS),
        ("請比較839系列機型的電池續航力比較？", FunnelQueryType.SERIES_COMPARISON),
        ("請比較819系列顯示螢幕規格有什麼不同？", FunnelQueryType.SERIES_COMPARISON),
        ("958系列有哪些規格差異？", FunnelQueryType.SERIES_COMPARISON),
        
        # 用途推薦查詢
        ("推薦一款適合遊戲的筆電", FunnelQueryType.PURPOSE_RECOMMENDATION),
        ("我需要一台商務筆電", FunnelQueryType.PURPOSE_RECOMMENDATION),
        ("什麼筆電最適合學生使用？", FunnelQueryType.PURPOSE_RECOMMENDATION),
        ("找一台創作用的高性能筆電", FunnelQueryType.PURPOSE_RECOMMENDATION),
        
        # 混合模糊查詢
        ("958系列哪款最適合遊戲？", FunnelQueryType.MIXED_AMBIGUOUS),
        ("比較適合辦公的筆電有哪些？", FunnelQueryType.MIXED_AMBIGUOUS),
        ("哪個系列適合學生使用？", FunnelQueryType.MIXED_AMBIGUOUS),
    ]
    
    results = []
    print(f"{'序號':<4} {'查詢內容':<45} {'預期類型':<20} {'實際類型':<20} {'信心度':<8} {'狀態'}")
    print("-" * 110)
    
    for i, (query, expected_type) in enumerate(test_cases, 1):
        actual_type, confidence = funnel_manager.classify_ambiguous_query(query)
        status = "✅ 通過" if actual_type == expected_type else "❌ 失敗"
        
        print(f"{i:<4} {query[:43]:<45} {expected_type.value:<20} {actual_type.value:<20} {confidence:<8.2f} {status}")
        results.append((query, expected_type, actual_type, confidence, status))
    
    # 統計結果
    passed = sum(1 for _, expected, actual, _, _ in results if expected == actual)
    total = len(results)
    success_rate = passed / total * 100
    
    print(f"\n📊 分類測試結果:")
    print(f"總測試案例: {total}")
    print(f"通過案例: {passed}")
    print(f"成功率: {success_rate:.1f}%")
    
    return success_rate > 80  # 80%以上算成功

def test_funnel_triggering():
    """測試漏斗觸發邏輯"""
    print("\n" + "=" * 80)
    print("🧪 測試漏斗觸發邏輯")
    print("=" * 80)
    
    funnel_manager = FunnelConversationManager()
    
    test_cases = [
        # 應該觸發漏斗的查詢
        ("比較958系列哪款筆記型電腦更適合遊戲？", True),
        ("推薦一款適合遊戲的筆電", True),
        ("我需要一台商務筆電", True),
        ("958系列和839系列哪個好？", True),
        
        # 不應該觸發漏斗的查詢（太明確）
        ("AG958的規格如何？", False),
        ("列出所有筆電型號", False),
        ("958系列的價格範圍", False),
    ]
    
    results = []
    print(f"{'序號':<4} {'查詢內容':<50} {'預期觸發':<10} {'實際觸發':<10} {'狀態'}")
    print("-" * 85)
    
    for i, (query, expected_trigger) in enumerate(test_cases, 1):
        should_trigger, query_type = funnel_manager.should_trigger_funnel(query)
        status = "✅ 通過" if should_trigger == expected_trigger else "❌ 失敗"
        
        trigger_str = "是" if should_trigger else "否"
        expected_str = "是" if expected_trigger else "否"
        
        print(f"{i:<4} {query[:48]:<50} {expected_str:<10} {trigger_str:<10} {status}")
        results.append((query, expected_trigger, should_trigger, status))
    
    # 統計結果
    passed = sum(1 for _, expected, actual, _ in results if expected == actual)
    total = len(results)
    success_rate = passed / total * 100
    
    print(f"\n📊 觸發測試結果:")
    print(f"總測試案例: {total}")
    print(f"通過案例: {passed}")
    print(f"成功率: {success_rate:.1f}%")
    
    return success_rate > 85  # 85%以上算成功

def test_funnel_session_flow():
    """測試漏斗會話流程"""
    print("\n" + "=" * 80)
    print("🧪 測試漏斗會話流程")
    print("=" * 80)
    
    funnel_manager = FunnelConversationManager()
    
    # 測試案例1: 系列比較查詢
    test_query_1 = "比較958系列哪款筆記型電腦更適合遊戲？"
    print(f"測試案例1: {test_query_1}")
    
    try:
        # 開始漏斗會話
        session_id_1, funnel_question_1 = funnel_manager.start_funnel_session(test_query_1)
        print(f"✅ 會話建立成功: {session_id_1}")
        print(f"   問題: {funnel_question_1.question_text}")
        print(f"   選項數量: {len(funnel_question_1.options)}")
        
        # 模擬用戶選擇系列比較
        choice_result_1 = funnel_manager.process_funnel_choice(session_id_1, "series_comparison")
        if "error" not in choice_result_1:
            print(f"✅ 選擇處理成功: {choice_result_1['target_flow']}")
        else:
            print(f"❌ 選擇處理失敗: {choice_result_1['error']}")
            return False
        
    except Exception as e:
        print(f"❌ 會話流程測試失敗: {e}")
        return False
    
    # 測試案例2: 用途推薦查詢
    test_query_2 = "推薦一款適合商務辦公的筆電"
    print(f"\n測試案例2: {test_query_2}")
    
    try:
        # 開始漏斗會話
        session_id_2, funnel_question_2 = funnel_manager.start_funnel_session(test_query_2)
        print(f"✅ 會話建立成功: {session_id_2}")
        
        # 模擬用戶選擇用途推薦
        choice_result_2 = funnel_manager.process_funnel_choice(session_id_2, "purpose_recommendation")
        if "error" not in choice_result_2:
            print(f"✅ 選擇處理成功: {choice_result_2['target_flow']}")
        else:
            print(f"❌ 選擇處理失敗: {choice_result_2['error']}")
            return False
        
    except Exception as e:
        print(f"❌ 會話流程測試失敗: {e}")
        return False
    
    print(f"\n📊 會話流程測試: ✅ 全部通過")
    return True

def test_funnel_question_generation():
    """測試漏斗問題生成"""
    print("\n" + "=" * 80)
    print("🧪 測試漏斗問題生成")
    print("=" * 80)
    
    funnel_manager = FunnelConversationManager()
    
    test_queries = [
        "比較958系列的筆電",
        "推薦遊戲筆電",
        "我需要一台適合工作的筆電"
    ]
    
    all_passed = True
    
    for i, query in enumerate(test_queries, 1):
        print(f"測試 {i}: {query}")
        
        try:
            # 分類查詢
            query_type, confidence = funnel_manager.classify_ambiguous_query(query)
            
            # 生成漏斗問題
            funnel_question = funnel_manager.generate_funnel_questions(query, query_type)
            
            print(f"  ✅ 問題生成成功")
            print(f"     問題ID: {funnel_question.question_id}")
            print(f"     問題文本: {funnel_question.question_text}")
            print(f"     選項數量: {len(funnel_question.options)}")
            
            # 驗證問題結構
            if not funnel_question.question_text:
                print(f"  ❌ 問題文本為空")
                all_passed = False
            
            if len(funnel_question.options) < 2:
                print(f"  ❌ 選項數量不足: {len(funnel_question.options)}")
                all_passed = False
            
            # 驗證選項結構
            for option in funnel_question.options:
                required_keys = ["option_id", "label", "description", "route"]
                missing_keys = [key for key in required_keys if key not in option]
                if missing_keys:
                    print(f"  ❌ 選項缺少必要欄位: {missing_keys}")
                    all_passed = False
            
        except Exception as e:
            print(f"  ❌ 問題生成失敗: {e}")
            all_passed = False
    
    status = "✅ 全部通過" if all_passed else "❌ 部分失敗"
    print(f"\n📊 問題生成測試: {status}")
    return all_passed

def test_funnel_config_loading():
    """測試漏斗配置載入"""
    print("\n" + "=" * 80)
    print("🧪 測試漏斗配置載入")
    print("=" * 80)
    
    try:
        funnel_manager = FunnelConversationManager()
        
        # 檢查配置是否正確載入
        config = funnel_manager.funnel_config
        
        # 驗證必要的配置結構
        required_sections = ["questions", "flows"]
        for section in required_sections:
            if section not in config:
                print(f"❌ 配置缺少必要部分: {section}")
                return False
            print(f"✅ 配置部分存在: {section}")
        
        # 驗證問題配置
        questions = config.get("questions", {})
        if "series_vs_purpose" not in questions:
            print(f"❌ 缺少主要分流問題配置")
            return False
        print(f"✅ 主要分流問題配置存在")
        
        # 驗證流程配置
        flows = config.get("flows", {})
        required_flows = ["series_comparison_flow", "purpose_recommendation_flow"]
        for flow in required_flows:
            if flow not in flows:
                print(f"❌ 缺少流程配置: {flow}")
                return False
            print(f"✅ 流程配置存在: {flow}")
        
        # 驗證分類規則
        rules = funnel_manager.classification_rules
        required_rule_types = ["series_comparison_indicators", "purpose_recommendation_indicators", "mixed_indicators"]
        for rule_type in required_rule_types:
            if rule_type not in rules:
                print(f"❌ 缺少分類規則: {rule_type}")
                return False
            if not rules[rule_type]:
                print(f"❌ 分類規則為空: {rule_type}")
                return False
            print(f"✅ 分類規則存在: {rule_type} ({len(rules[rule_type])} 條規則)")
        
        print(f"\n📊 配置載入測試: ✅ 全部通過")
        return True
        
    except Exception as e:
        print(f"❌ 配置載入測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 Multi-round Funnel Conversation 系統測試")
    print("=" * 100)
    
    test_results = []
    
    # 執行所有測試
    test_functions = [
        ("配置載入測試", test_funnel_config_loading),
        ("查詢分類測試", test_query_classification),
        ("漏斗觸發測試", test_funnel_triggering),
        ("問題生成測試", test_funnel_question_generation),
        ("會話流程測試", test_funnel_session_flow),
    ]
    
    for test_name, test_func in test_functions:
        print(f"\n🔄 執行 {test_name}...")
        try:
            result = test_func()
            test_results.append((test_name, result))
            status = "✅ 通過" if result else "❌ 失敗"
            print(f"✨ {test_name}: {status}")
        except Exception as e:
            print(f"❌ {test_name} 執行失敗: {e}")
            test_results.append((test_name, False))
    
    # 總結測試結果
    print("\n" + "=" * 100)
    print("📊 測試結果總結")
    print("=" * 100)
    
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    success_rate = passed_tests / total_tests * 100
    
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name:<20}: {status}")
    
    print(f"\n總測試數量: {total_tests}")
    print(f"通過測試: {passed_tests}")
    print(f"成功率: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("\n🎉 Multi-round Funnel Conversation 系統測試全面通過！")
        print("   系統已準備好提供智能化的對話分流服務。")
    elif success_rate >= 70:
        print("\n⚠️ 系統基本功能正常，但需要進一步優化。")
    else:
        print("\n❌ 系統存在重大問題，需要修復後再測試。")
    
    return success_rate >= 90

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)