#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析正則表達式在default_slots.json中的測試成本和優點
"""

import json
import re
import time
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any


def load_default_slots():
    """載入default_slots.json"""

    try:
        default_slots_path = Path(__file__).parent / "libs" / "mgfd_cursor" / "humandata" / "default_slots.json"
        with open(default_slots_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 載入檔案失敗: {e}")
        return None

def analyze_regex_patterns(default_slots: Dict[str, Any]) -> Dict[str, Any]:
    """分析正則表達式模式"""
    print("=== 正則表達式模式分析 ===\n")
    
    regex_stats = {
        "total_patterns": 0,
        "total_slots": 0,
        "slots_with_regex": 0,
        "pattern_complexity": {},
        "pattern_lengths": [],
        "special_chars": {},
        "potential_issues": []
    }
    
    slot_definitions = default_slots["slot_definitions"]
    regex_stats["total_slots"] = len(slot_definitions)
    
    for slot_name, slot_def in slot_definitions.items():
        if "synonyms" not in slot_def:
            continue
            
        synonyms = slot_def["synonyms"]
        slot_has_regex = False
        
        for value_name, value_synonyms in synonyms.items():
            if "regex" not in value_synonyms:
                continue
                
            slot_has_regex = True
            regex_patterns = value_synonyms["regex"]
            
            for pattern in regex_patterns:
                regex_stats["total_patterns"] += 1
                regex_stats["pattern_lengths"].append(len(pattern))
                
                # 分析模式複雜度
                complexity_score = analyze_pattern_complexity(pattern)
                complexity_level = get_complexity_level(complexity_score)
                
                if complexity_level not in regex_stats["pattern_complexity"]:
                    regex_stats["pattern_complexity"][complexity_level] = 0
                regex_stats["pattern_complexity"][complexity_level] += 1
                
                # 檢查特殊字符
                special_chars = analyze_special_characters(pattern)
                for char in special_chars:
                    if char not in regex_stats["special_chars"]:
                        regex_stats["special_chars"][char] = 0
                    regex_stats["special_chars"][char] += 1
                
                # 檢查潛在問題
                issues = check_pattern_issues(pattern)
                if issues:
                    regex_stats["potential_issues"].append({
                        "slot": slot_name,
                        "value": value_name,
                        "pattern": pattern,
                        "issues": issues
                    })
        
        if slot_has_regex:
            regex_stats["slots_with_regex"] += 1
    
    return regex_stats

def analyze_pattern_complexity(pattern: str) -> int:
    """分析正則表達式複雜度"""
    complexity_score = 0
    
    # 基本複雜度因子
    complexity_score += len(pattern) * 0.1
    
    # 特殊字符複雜度
    special_chars = ['*', '+', '?', '{', '}', '[', ']', '(', ')', '|', '\\', '.', '^', '$']
    for char in special_chars:
        complexity_score += pattern.count(char) * 2
    
    # 量詞複雜度
    quantifiers = ['*', '+', '?', '{', '}']
    for quantifier in quantifiers:
        complexity_score += pattern.count(quantifier) * 3
    
    # 分組複雜度
    complexity_score += pattern.count('(') * 2
    complexity_score += pattern.count(')') * 2
    
    # 或運算符複雜度
    complexity_score += pattern.count('|') * 1.5
    
    return int(complexity_score)

def get_complexity_level(score: int) -> str:
    """獲取複雜度等級"""
    if score < 10:
        return "簡單"
    elif score < 25:
        return "中等"
    elif score < 50:
        return "複雜"
    else:
        return "非常複雜"

def analyze_special_characters(pattern: str) -> List[str]:
    """分析特殊字符"""
    special_chars = []
    regex_special = ['*', '+', '?', '{', '}', '[', ']', '(', ')', '|', '\\', '.', '^', '$']
    
    for char in regex_special:
        if char in pattern:
            special_chars.append(char)
    
    return special_chars

def check_pattern_issues(pattern: str) -> List[str]:
    """檢查正則表達式潛在問題"""
    issues = []
    
    # 檢查未轉義的特殊字符
    unescaped_chars = ['.', '*', '+', '?', '{', '}', '[', ']', '(', ')', '|', '^', '$']
    for char in unescaped_chars:
        if char in pattern and f'\\{char}' not in pattern:
            issues.append(f"未轉義的字符: {char}")
    
    # 檢查可能導致災難性回溯的模式
    if '.*.*' in pattern or '++.+' in pattern:
        issues.append("可能導致災難性回溯")
    
    # 檢查過於寬鬆的模式
    if len(pattern) < 3:
        issues.append("模式過於寬鬆")
    
    return issues

def performance_analysis():
    """性能分析"""
    print("\n=== 性能分析 ===\n")
    
    # 測試數據
    test_inputs = [
        "我想要一台遊戲筆電",
        "需要文書處理的電腦",
        "預算在3-4萬之間",
        "需要i7處理器",
        "想要獨立顯卡",
        "重量要輕便",
        "15吋螢幕",
        "偏好華碩品牌",
        "開機要快",
        "需要便攜設計"
    ]
    
    default_slots = load_default_slots()
    if not default_slots:
        return
    
    # 測試關鍵詞匹配
    print("🔍 測試關鍵詞匹配性能...")
    keyword_times = []
    
    for test_input in test_inputs:
        start_time = time.time()
        
        for slot_name, slot_def in default_slots["slot_definitions"].items():
            if "synonyms" not in slot_def:
                continue
                
            for value_name, value_synonyms in slot_def["synonyms"].items():
                keywords = value_synonyms.get("keywords", [])
                for keyword in keywords:
                    if keyword.lower() in test_input.lower():
                        pass  # 找到匹配
        
        end_time = time.time()
        keyword_times.append(end_time - start_time)
    
    avg_keyword_time = sum(keyword_times) / len(keyword_times)
    print(f"   平均關鍵詞匹配時間: {avg_keyword_time*1000:.3f} ms")
    
    # 測試正則表達式匹配
    print("\n🔍 測試正則表達式匹配性能...")
    regex_times = []
    
    for test_input in test_inputs:
        start_time = time.time()
        
        for slot_name, slot_def in default_slots["slot_definitions"].items():
            if "synonyms" not in slot_def:
                continue
                
            for value_name, value_synonyms in slot_def["synonyms"].items():
                regex_patterns = value_synonyms.get("regex", [])
                for pattern in regex_patterns:
                    try:
                        if re.search(pattern, test_input, re.IGNORECASE):
                            pass  # 找到匹配
                    except re.error:
                        pass  # 忽略錯誤的正則表達式
        
        end_time = time.time()
        regex_times.append(end_time - start_time)
    
    avg_regex_time = sum(regex_times) / len(regex_times)
    print(f"   平均正則表達式匹配時間: {avg_regex_time*1000:.3f} ms")
    
    # 計算性能比率
    performance_ratio = avg_regex_time / avg_keyword_time if avg_keyword_time > 0 else 0
    print(f"\n📊 性能比較:")
    print(f"   正則表達式/關鍵詞性能比率: {performance_ratio:.2f}x")
    
    if performance_ratio > 5:
        print("   ⚠️  正則表達式性能開銷較大")
    elif performance_ratio > 2:
        print("   📝 正則表達式性能開銷中等")
    else:
        print("   ✅ 正則表達式性能開銷可接受")

def accuracy_analysis():
    """準確性分析"""
    print("\n=== 準確性分析 ===\n")
    
    # 測試案例
    test_cases = [
        # 使用目的測試
        {"input": "我想要玩遊戲", "expected": {"usage_purpose": "gaming"}},
        {"input": "需要辦公用的筆電", "expected": {"usage_purpose": "business"}},
        {"input": "學生用的電腦", "expected": {"usage_purpose": "student"}},
        {"input": "做設計工作", "expected": {"usage_purpose": "creative"}},
        {"input": "一般日常使用", "expected": {"usage_purpose": "general"}},
        {"input": "文書處理需求", "expected": {"usage_purpose": "document_processing"}},
        
        # 預算範圍測試
        {"input": "便宜一點的", "expected": {"budget_range": "budget"}},
        {"input": "中等價位", "expected": {"budget_range": "mid_range"}},
        {"input": "高端配置", "expected": {"budget_range": "premium"}},
        {"input": "旗艦級別", "expected": {"budget_range": "luxury"}},
        
        # CPU等級測試
        {"input": "i3處理器", "expected": {"cpu_level": "basic"}},
        {"input": "i5效能", "expected": {"cpu_level": "mid"}},
        {"input": "i7以上", "expected": {"cpu_level": "high"}},
        
        # 螢幕尺寸測試
        {"input": "13吋螢幕", "expected": {"screen_size": "small"}},
        {"input": "15.6吋", "expected": {"screen_size": "medium"}},
        {"input": "17吋大螢幕", "expected": {"screen_size": "large"}},
    ]
    
    default_slots = load_default_slots()
    if not default_slots:
        return
    
    keyword_accuracy = 0
    regex_accuracy = 0
    total_tests = len(test_cases)
    
    for test_case in test_cases:
        test_input = test_case["input"]
        expected = test_case["expected"]
        
        # 測試關鍵詞匹配
        keyword_match = False
        for slot_name, expected_value in expected.items():
            if slot_name in default_slots["slot_definitions"]:
                slot_def = default_slots["slot_definitions"][slot_name]
                if "synonyms" in slot_def and expected_value in slot_def["synonyms"]:
                    keywords = slot_def["synonyms"][expected_value].get("keywords", [])
                    for keyword in keywords:
                        if keyword.lower() in test_input.lower():
                            keyword_match = True
                            break
        
        if keyword_match:
            keyword_accuracy += 1
        
        # 測試正則表達式匹配
        regex_match = False
        for slot_name, expected_value in expected.items():
            if slot_name in default_slots["slot_definitions"]:
                slot_def = default_slots["slot_definitions"][slot_name]
                if "synonyms" in slot_def and expected_value in slot_def["synonyms"]:
                    regex_patterns = slot_def["synonyms"][expected_value].get("regex", [])
                    for pattern in regex_patterns:
                        try:
                            if re.search(pattern, test_input, re.IGNORECASE):
                                regex_match = True
                                break
                        except re.error:
                            continue
        
        if regex_match:
            regex_accuracy += 1
    
    print(f"📊 準確性比較:")
    print(f"   關鍵詞匹配準確率: {keyword_accuracy}/{total_tests} ({keyword_accuracy/total_tests*100:.1f}%)")
    print(f"   正則表達式匹配準確率: {regex_accuracy}/{total_tests} ({regex_accuracy/total_tests*100:.1f}%)")
    
    if regex_accuracy > keyword_accuracy:
        print("   ✅ 正則表達式提供更好的準確性")
    elif regex_accuracy == keyword_accuracy:
        print("   📝 兩種方法準確性相當")
    else:
        print("   ⚠️  關鍵詞匹配準確性更高")

def cost_benefit_analysis():
    """成本效益分析"""
    print("\n=== 成本效益分析 ===\n")
    
    default_slots = load_default_slots()
    if not default_slots:
        return
    
    regex_stats = analyze_regex_patterns(default_slots)
    
    print("💰 成本分析:")
    print(f"   總正則表達式模式數: {regex_stats['total_patterns']}")
    print(f"   使用正則表達式的槽位數: {regex_stats['slots_with_regex']}/{regex_stats['total_slots']}")
    
    # 複雜度分布
    print(f"\n📊 複雜度分布:")
    for level, count in regex_stats["pattern_complexity"].items():
        percentage = count / regex_stats["total_patterns"] * 100
        print(f"   {level}: {count} 個 ({percentage:.1f}%)")
    
    # 特殊字符使用
    print(f"\n🔧 特殊字符使用:")
    for char, count in sorted(regex_stats["special_chars"].items(), key=lambda x: x[1], reverse=True):
        percentage = count / regex_stats["total_patterns"] * 100
        print(f"   '{char}': {count} 次 ({percentage:.1f}%)")
    
    # 潛在問題
    if regex_stats["potential_issues"]:
        print(f"\n⚠️  潛在問題 ({len(regex_stats['potential_issues'])} 個):")
        for issue in regex_stats["potential_issues"][:5]:  # 只顯示前5個
            print(f"   - {issue['slot']}.{issue['value']}: {', '.join(issue['issues'])}")
    
    print(f"\n🎯 效益分析:")
    print("   1. 更精確的模式匹配")
    print("   2. 支援複雜的文本模式")
    print("   3. 減少誤匹配")
    print("   4. 提高系統靈活性")
    print("   5. 支援多語言和變體")

def optimization_recommendations():
    """優化建議"""
    print("\n=== 優化建議 ===\n")
    
    print("🔧 性能優化建議:")
    print("   1. 預編譯正則表達式")
    print("   2. 使用更簡單的模式")
    print("   3. 避免災難性回溯")
    print("   4. 實施緩存機制")
    print("   5. 分層匹配策略")
    
    print(f"\n📝 維護性建議:")
    print("   1. 統一正則表達式風格")
    print("   2. 添加詳細註釋")
    print("   3. 定期測試和驗證")
    print("   4. 建立測試案例庫")
    print("   5. 監控性能指標")
    
    print(f"\n⚖️  平衡策略:")
    print("   1. 關鍵詞優先，正則表達式補充")
    print("   2. 複雜模式使用正則表達式")
    print("   3. 簡單匹配使用關鍵詞")
    print("   4. 動態選擇匹配策略")
    print("   5. 用戶反饋驅動優化")

if __name__ == "__main__":
    print("🚀 開始分析正則表達式的成本效益...")
    
    # 執行分析
    default_slots = load_default_slots()
    if default_slots:
        analyze_regex_patterns(default_slots)
        performance_analysis()
        accuracy_analysis()
        cost_benefit_analysis()
        optimization_recommendations()
        
        print("\n📋 分析總結:")
        print("   正則表達式在default_slots.json中的使用:")
        print("   ✅ 優點: 提高匹配精度和靈活性")
        print("   ⚠️  成本: 增加計算複雜度和維護難度")
        print("   💡 建議: 採用混合策略，平衡性能和準確性")
    else:
        print("❌ 無法載入default_slots.json")
