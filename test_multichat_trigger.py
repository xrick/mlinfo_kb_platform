#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試多輪對話觸發邏輯的腳本
用於驗證三個查詢範例的實際執行路徑
"""

import re
import json
from pathlib import Path

def test_has_specific_models(query: str) -> bool:
    """模擬修復後的 _has_specific_models 函數邏輯"""
    # 具體機型模式：完整的機型名稱，如 AG958, APX958, NB819-A 等
    # 排除純系列號碼（819, 839, 958）的匹配
    specific_model_patterns = [
        r'[A-Z]{2,3}\d{3}',  # 如 AG958, APX958, NB819 等
        r'i[3579]-\d+',      # 如 i7-1234 等具體CPU型號
        r'Ryzen\s+[579]\s+\d+',  # 如 Ryzen 7 5800H 等具體CPU型號
    ]
    
    # 檢查是否包含具體機型名稱
    for pattern in specific_model_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            print(f"  ✅ 找到具體機型模式: '{pattern}'")
            return True
    
    # 檢查是否包含常見的機型名稱關鍵字組合
    # 例如：「AG958 和 APX958 的比較」這類具體機型比較
    model_mention_patterns = [
        r'[A-Z]{1,3}\d{3}[A-Z]*[-\s]*[A-Z]*\d*',  # 完整機型名稱
    ]
    
    for pattern in model_mention_patterns:
        matches = re.findall(pattern, query, re.IGNORECASE)
        if matches and len(matches) >= 1:  # 至少提到一個具體機型
            # 驗證是否為有效的機型名稱格式（不只是系列號碼）
            valid_models = [m for m in matches if len(m) > 3 and not re.match(r'^\d{3}$', m)]
            if valid_models:
                print(f"  ✅ 找到具體機型名稱: {valid_models}")
                return True
    
    print(f"  ❌ 未檢測到具體機型，判定為系列或模糊查詢")
    return False

def test_is_series_comparison(query: str) -> bool:
    """模擬 _is_series_comparison 函數邏輯"""
    # 系列比較的模式：包含系列號碼+系列關鍵字的組合
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
            print(f"  ✅ 找到系列比較模式: {pattern}")
            return True
    
    # 額外檢查：是否同時包含數字系列和比較關鍵字，但沒有具體機型名稱
    if re.search(r'\b(819|839|958)\b', query) and any(keyword in query.lower() for keyword in ["比較", "差別", "不同", "差異"]):
        # 確認不包含具體機型名稱
        if not test_has_specific_models(query):
            print(f"  ✅ 找到數字系列+比較關鍵字組合")
            return True
    
    print(f"  ❌ 未檢測到系列比較模式")
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
    """模擬 should_activate_multichat 函數邏輯"""
    print(f"\n🔍 測試查詢: '{query}'")
    
    # 載入觸發關鍵字
    trigger_keywords = load_trigger_keywords()
    vague_keywords = trigger_keywords.get("vague_queries", [])
    comparison_keywords = trigger_keywords.get("comparison_queries", [])
    
    print(f"  📝 vague_keywords 數量: {len(vague_keywords)}")
    print(f"  📝 comparison_keywords: {comparison_keywords}")
    
    query_lower = query.lower()
    
    # 場景識別
    gaming_keywords = ["遊戲", "gaming", "電競", "遊戲用", "玩遊戲", "game", "fps", "moba", 
                      "顯卡", "gpu", "高畫質", "高效能遊戲"]
    
    detected_scenario = "general"
    if any(keyword in query_lower for keyword in gaming_keywords):
        detected_scenario = "gaming"
        print(f"  🎮 檢測到遊戲場景")
    
    # 優先檢查比較查詢關鍵字（避免被模糊查詢攔截）
    print(f"  🔍 檢查比較查詢關鍵字...")
    for keyword in comparison_keywords:
        if keyword in query_lower:
            print(f"  ✅ 找到比較查詢關鍵字: '{keyword}'")
            # 檢查是否為具體系列比較
            is_series_comp = test_is_series_comparison(query)
            if is_series_comp:
                print(f"  ➡️ 結果: 不觸發多輪對話 (系列比較查詢)")
                return False, None
            else:
                has_specific = test_has_specific_models(query)
                if not has_specific:
                    print(f"  ➡️ 結果: 觸發多輪對話 (模糊比較查詢)")
                    return True, detected_scenario
                else:
                    print(f"  ➡️ 結果: 不觸發多輪對話 (具體機型比較)")
                    return False, None
    
    # 檢查模糊查詢關鍵字
    print(f"  🔍 檢查模糊查詢關鍵字...")
    for keyword in vague_keywords:
        if keyword in query_lower:
            print(f"  ✅ 找到模糊查詢關鍵字: '{keyword}'")
            print(f"  ➡️ 結果: 觸發多輪對話 (場景: {detected_scenario})")
            return True, detected_scenario
    
    # 檢查使用場景關鍵字
    print(f"  🔍 檢查使用場景關鍵字...")
    scenario_keywords = ["適合", "用於", "專門", "主要", "需要", "想要", "希望", "打算"]
    for keyword in scenario_keywords:
        if keyword in query_lower:
            print(f"  ✅ 找到場景關鍵字: '{keyword}'")
            has_specific = test_has_specific_models(query)
            if not has_specific:
                print(f"  ➡️ 結果: 觸發多輪對話 (使用場景查詢)")
                return True, detected_scenario
            else:
                print(f"  ➡️ 結果: 不觸發多輪對話 (具體機型場景查詢)")
                return False, None
    
    print(f"  ➡️ 結果: 不觸發多輪對話")
    return False, None

def main():
    """主測試函數"""
    print("=" * 80)
    print("🧪 多輪對話觸發邏輯測試")
    print("=" * 80)
    
    test_queries = [
        "比較958系列哪款筆記型電腦更適合遊戲？",
        "請比較839系列機型的電池續航力比較？", 
        "請比較819系列顯示螢幕規格有什麼不同？"
    ]
    
    results = []
    for query in test_queries:
        should_trigger, scenario = test_multichat_trigger(query)
        results.append((query, should_trigger, scenario))
    
    print("\n" + "=" * 80)
    print("📊 測試結果總結")
    print("=" * 80)
    
    for i, (query, should_trigger, scenario) in enumerate(results, 1):
        status = "🟢 觸發問卷" if should_trigger else "🔴 不觸發問卷"
        print(f"{i}. {query}")
        print(f"   {status} (場景: {scenario})")
        print()

if __name__ == "__main__":
    main()