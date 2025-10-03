#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試特殊案例知識庫系統
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import logging
from libs.mgfd_cursor.special_cases_knowledge import SpecialCasesKnowledgeBase

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_knowledge_base():
    """測試知識庫基本功能"""
    print("=== 測試特殊案例知識庫系統 ===")
    
    try:
        # 初始化知識庫
        kb = SpecialCasesKnowledgeBase()
        print("✓ 知識庫初始化成功")
        
        # 測試案例1: "我想要效能好的筆電" - 這是造成循環的原始問題
        test_queries = [
            "我想要效能好的筆電",
            "需要高效能的筆電", 
            "我對電腦不太懂，希望不要太複雜",
            "我需要一台能帶出國，但在家也能當桌機用的筆電",
            "跟我朋友那台一樣的，但要更好一點",
            "不知道該選哪台筆電"  # 應該匹配DSL002
        ]
        
        print("\n=== 測試查詢匹配 ===")
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. 測試查詢: '{query}'")
            
            # 尋找匹配案例
            matched_case = kb.find_matching_case(query, f"test_session_{i}")
            
            if matched_case:
                case_id = matched_case.get("case_id", "Unknown")
                similarity = matched_case.get("similarity_score", 0.0)
                category = matched_case.get("matched_category", "Unknown")
                
                print(f"   ✓ 找到匹配: {case_id} (相似度: {similarity:.3f})")
                print(f"   ✓ 分類: {category}")
                
                # 獲取回應
                case_response = kb.get_case_response(matched_case)
                response_type = case_response.get("response_type", "unknown")
                message = case_response.get("message", "")
                
                print(f"   ✓ 回應類型: {response_type}")
                print(f"   ✓ 消息: {message[:80]}...")
                
                # 檢查是否有漏斗問題
                if "funnel_question" in case_response:
                    funnel = case_response["funnel_question"]
                    print(f"   ✓ 漏斗問題: {funnel.get('question_text', 'N/A')}")
                    options_count = len(funnel.get("options", []))
                    print(f"   ✓ 選項數量: {options_count}")
            else:
                print("   ✗ 未找到匹配案例")
        
        # 測試循環檢測
        print("\n=== 測試循環檢測 ===")
        test_session = "loop_test_session"
        repeat_query = "我想要效能好的筆電"
        
        print(f"重複查詢 '{repeat_query}' 3次:")
        for i in range(3):
            matched_case = kb.find_matching_case(repeat_query, test_session)
            if matched_case:
                is_loop_breaker = matched_case.get("case_id") == "LOOP_BREAKER"
                print(f"   第{i+1}次: {'循環檢測' if is_loop_breaker else '正常匹配'}")
            else:
                print(f"   第{i+1}次: 未匹配")
        
        # 測試知識庫統計
        print("\n=== 知識庫統計 ===")
        stats = kb.get_knowledge_base_stats()
        print(f"總案例數: {stats.get('total_cases', 0)}")
        print(f"總匹配次數: {stats.get('total_successful_matches', 0)}")
        print(f"平均成功率: {stats.get('average_success_rate', 0):.3f}")
        
        print("\n✓ 所有測試完成")
        return True
        
    except Exception as e:
        print(f"✗ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_knowledge_base()
    print(f"\n測試結果: {'成功' if success else '失敗'}")
    exit(0 if success else 1)