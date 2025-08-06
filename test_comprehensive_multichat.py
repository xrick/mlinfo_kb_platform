#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面的多輪對話觸發邏輯測試
驗證修復後的系統對各種查詢類型的處理
"""

import re
import json
from pathlib import Path

def test_has_specific_models(query: str) -> bool:
    """模擬修復後的 _has_specific_models 函數邏輯"""
    specific_model_patterns = [
        r'[A-Z]{2,3}\d{3}',  # 如 AG958, APX958, NB819 等
        r'i[3579]-\d+',      # 如 i7-1234 等具體CPU型號
        r'Ryzen\s+[579]\s+\d+',  # 如 Ryzen 7 5800H 等具體CPU型號
    ]
    
    for pattern in specific_model_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return True
    
    model_mention_patterns = [
        r'[A-Z]{1,3}\d{3}[A-Z]*[-\s]*[A-Z]*\d*',  # 完整機型名稱
    ]
    
    for pattern in model_mention_patterns:
        matches = re.findall(pattern, query, re.IGNORECASE)
        if matches and len(matches) >= 1:
            valid_models = [m for m in matches if len(m) > 3 and not re.match(r'^\d{3}$', m)]
            if valid_models:
                return True
    
    return False

def test_is_series_comparison(query: str) -> bool:
    """模擬修復後的 _is_series_comparison 函數邏輯"""
    series_patterns = [
        r'\b(819|839|958)\s*系列',           # 819系列、958系列
        r'\b(819|839|958)\s*機型',           # 819機型、958機型  
        r'\b(819|839|958)\s*款',             # 819款、958款
        r'\b(819|839|958)\s*型號',           # 819型號、958型號
        r'比較\s*(819|839|958)\s*系列',      # 比較819系列
        r'(819|839|958)\s*系列.*比較',       # 819系列...比較
        r'(819|839|958)\s*系列.*哪款',       # 819系列哪款
        r'(819|839|958)\s*系列.*機型',       # 819系列機型
    ]
    
    for pattern in series_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return True
    
    # 額外檢查：是否同時包含數字系列和比較關鍵字，但沒有具體機型名稱
    if re.search(r'\b(819|839|958)\b', query) and any(keyword in query.lower() for keyword in ["比較", "差別", "不同", "差異"]):
        if not test_has_specific_models(query):
            return True
    
    return False

def load_trigger_keywords():
    """載入觸發關鍵字"""
    try:
        features_path = Path(__file__).parent / "libs/services/sales_assistant/multichat/nb_features.json"
        with open(features_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get("trigger_keywords", {})
    except Exception as e:
        print(f"載入配置失敗: {e}")
        return {}

def test_multichat_trigger(query: str) -> tuple:
    """模擬修復後的 should_activate_multichat 函數邏輯"""
    trigger_keywords = load_trigger_keywords()
    vague_keywords = trigger_keywords.get("vague_queries", [])
    comparison_keywords = trigger_keywords.get("comparison_queries", [])
    
    query_lower = query.lower()
    
    # 場景識別
    gaming_keywords = ["遊戲", "gaming", "電競", "遊戲用", "玩遊戲", "game", "fps", "moba", 
                      "顯卡", "gpu", "高畫質", "高效能遊戲"]
    business_keywords = ["商務", "辦公", "工作", "企業", "商用", "業務", "職場", "公司", 
                        "文書處理", "文書", "處理", "office", "business", "工作用", "上班"]
    
    detected_scenario = "general"
    if any(keyword in query_lower for keyword in gaming_keywords):
        detected_scenario = "gaming"
    elif any(keyword in query_lower for keyword in business_keywords):
        detected_scenario = "business"
    
    # 優先檢查比較查詢關鍵字
    for keyword in comparison_keywords:
        if keyword in query_lower:
            if test_is_series_comparison(query):
                return False, None  # 不觸發多輪對話，直接執行比較
            elif not test_has_specific_models(query):
                return True, detected_scenario
    
    # 檢查模糊查詢關鍵字
    for keyword in vague_keywords:
        if keyword in query_lower:
            return True, detected_scenario
    
    # 檢查使用場景關鍵字
    scenario_keywords = ["適合", "用於", "專門", "主要", "需要", "想要", "希望", "打算"]
    for keyword in scenario_keywords:
        if keyword in query_lower and not test_has_specific_models(query):
            return True, detected_scenario
    
    return False, None

def main():
    """主測試函數"""
    print("=" * 100)
    print("🧪 全面的多輪對話觸發邏輯測試")
    print("=" * 100)
    
    test_cases = [
        # 原始問題案例
        ("比較958系列哪款筆記型電腦更適合遊戲？", False, "系列比較 - 不應觸發問卷"),
        ("請比較839系列機型的電池續航力比較？", False, "系列比較 - 不應觸發問卷"),
        ("請比較819系列顯示螢幕規格有什麼不同？", False, "系列比較 - 不應觸發問卷"),
        
        # 系列比較的其他變形
        ("958系列有哪些機型可以比較？", True, "模糊查詢 - 應該觸發問卷"),
        ("839系列和958系列哪個好？", False, "跨系列比較 - 不應觸發問卷"),
        ("比較958系列的所有機型", False, "系列比較 - 不應觸發問卷"),
        
        # 具體機型比較
        ("比較AG958和APX958的差異", False, "具體機型比較 - 不應觸發問卷"),
        ("AG958 vs APX958性能對比", False, "具體機型比較 - 不應觸發問卷"),
        
        # 模糊查詢
        ("推薦一款適合遊戲的筆電", True, "模糊查詢 - 應該觸發問卷"),
        ("我需要一台商務筆電", True, "模糊查詢 - 應該觸發問卷"),
        ("什麼筆電最適合學生使用？", True, "模糊查詢 - 應該觸發問卷"),
        
        # 一般查詢
        ("AG958的規格如何？", False, "具體查詢 - 不應觸發問卷"),
        ("958系列的價格範圍", False, "系列查詢 - 不應觸發問卷"),
        ("列出所有筆電型號", False, "列表查詢 - 不應觸發問卷"),
    ]
    
    results = []
    print(f"{'序號':<4} {'查詢內容':<40} {'預期結果':<12} {'實際結果':<12} {'狀態':<6} {'說明'}")
    print("-" * 100)
    
    for i, (query, expected_trigger, description) in enumerate(test_cases, 1):
        should_trigger, scenario = test_multichat_trigger(query)
        expected_str = "觸發問卷" if expected_trigger else "不觸發問卷"
        actual_str = "觸發問卷" if should_trigger else "不觸發問卷"
        status = "✅ 通過" if should_trigger == expected_trigger else "❌ 失敗"
        
        print(f"{i:<4} {query[:38]:<40} {expected_str:<12} {actual_str:<12} {status:<6} {description}")
        results.append((query, expected_trigger, should_trigger, status))
    
    # 統計結果
    passed = sum(1 for _, expected, actual, _ in results if expected == actual)
    total = len(results)
    success_rate = passed / total * 100
    
    print("\n" + "=" * 100)
    print(f"📊 測試結果統計")
    print("=" * 100)
    print(f"總測試案例: {total}")
    print(f"通過案例: {passed}")
    print(f"失敗案例: {total - passed}")
    print(f"成功率: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 所有測試案例通過！系統邏輯修復成功。")
    else:
        print(f"\n⚠️  有 {total - passed} 個案例需要進一步調整。")
        print("\n失敗案例詳情:")
        for query, expected, actual, status in results:
            if expected != actual:
                print(f"  - {query}")
                print(f"    預期: {'觸發問卷' if expected else '不觸發問卷'}")
                print(f"    實際: {'觸發問卷' if actual else '不觸發問卷'}")

if __name__ == "__main__":
    main()