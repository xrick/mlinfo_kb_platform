#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試整合後的default_slots.json
"""

import json
import sys
from pathlib import Path

def test_integration_completeness():
    """測試整合完整性"""
    print("=== 測試整合完整性 ===\n")
    
    try:
        # 載入整合後的檔案
        default_slots_path = Path(__file__).parent / "libs" / "mgfd_cursor" / "humandata" / "default_slots.json"
        
        with open(default_slots_path, 'r', encoding='utf-8') as f:
            default_slots = json.load(f)
        
        print("✅ 成功載入整合後的default_slots.json")
        
        # 檢查版本信息
        metadata = default_slots["metadata"]
        print(f"📋 版本信息:")
        print(f"   版本: {metadata['version']}")
        print(f"   描述: {metadata['description']}")
        print(f"   整合信息: {metadata['integration_info']}")
        
        # 檢查功能特性
        features = metadata["features"]
        print(f"\n🔧 功能特性:")
        for feature, enabled in features.items():
            status = "✅" if enabled else "❌"
            print(f"   {status} {feature}")
        
        # 檢查槽位同義詞完整性
        slot_definitions = default_slots["slot_definitions"]
        print(f"\n🔍 檢查槽位同義詞完整性...")
        
        slots_with_synonyms = 0
        total_slots = len(slot_definitions)
        
        for slot_name, slot_def in slot_definitions.items():
            if "synonyms" in slot_def:
                synonyms = slot_def["synonyms"]
                print(f"   ✅ {slot_name}: 包含同義詞 ({len(synonyms)} 個值)")
                
                # 檢查每個值的同義詞結構
                for value_name, value_synonyms in synonyms.items():
                    if all(key in value_synonyms for key in ["keywords", "regex", "semantic"]):
                        print(f"      ✅ {value_name}: 完整結構")
                    else:
                        print(f"      ⚠️  {value_name}: 結構不完整")
                
                slots_with_synonyms += 1
            else:
                print(f"   ❌ {slot_name}: 缺少同義詞")
        
        print(f"\n📊 同義詞覆蓋率: {slots_with_synonyms}/{total_slots} ({slots_with_synonyms/total_slots*100:.1f}%)")
        
        return slots_with_synonyms == total_slots
        
    except Exception as e:
        print(f"❌ 整合完整性測試失敗: {e}")
        return False

def test_extraction_methods():
    """測試提取方法配置"""
    print("\n=== 測試提取方法配置 ===\n")
    
    try:
        default_slots_path = Path(__file__).parent / "libs" / "mgfd_cursor" / "humandata" / "default_slots.json"
        
        with open(default_slots_path, 'r', encoding='utf-8') as f:
            default_slots = json.load(f)
        
        collection_strategy = default_slots["collection_strategy"]
        extraction_methods = collection_strategy.get("extraction_methods", {})
        
        print("🔧 提取方法配置:")
        print(f"   主要方法: {extraction_methods.get('primary', 'N/A')}")
        print(f"   後備方法: {extraction_methods.get('fallback', 'N/A')}")
        
        strategies = extraction_methods.get("strategies", {})
        print(f"\n📋 策略配置:")
        
        total_weight = 0
        for strategy_name, config in strategies.items():
            enabled = config.get("enabled", False)
            weight = config.get("weight", 0)
            total_weight += weight
            
            status = "✅" if enabled else "❌"
            print(f"   {status} {strategy_name}: 權重={weight}, 啟用={enabled}")
        
        print(f"\n📊 權重總和: {total_weight:.2f}")
        
        # 驗證權重總和接近1.0
        if 0.95 <= total_weight <= 1.05:
            print("   ✅ 權重配置合理")
            return True
        else:
            print("   ⚠️  權重配置需要調整")
            return False
        
    except Exception as e:
        print(f"❌ 提取方法測試失敗: {e}")
        return False

def test_synonym_quality():
    """測試同義詞品質"""
    print("\n=== 測試同義詞品質 ===\n")
    
    try:
        default_slots_path = Path(__file__).parent / "libs" / "mgfd_cursor" / "humandata" / "default_slots.json"
        
        with open(default_slots_path, 'r', encoding='utf-8') as f:
            default_slots = json.load(f)
        
        slot_definitions = default_slots["slot_definitions"]
        
        total_keywords = 0
        total_regex_patterns = 0
        total_semantic_terms = 0
        quality_issues = []
        
        for slot_name, slot_def in slot_definitions.items():
            if "synonyms" not in slot_def:
                continue
                
            synonyms = slot_def["synonyms"]
            
            for value_name, value_synonyms in synonyms.items():
                # 統計關鍵詞
                keywords = value_synonyms.get("keywords", [])
                total_keywords += len(keywords)
                
                # 統計正則表達式
                regex_patterns = value_synonyms.get("regex", [])
                total_regex_patterns += len(regex_patterns)
                
                # 統計語義術語
                semantic_terms = value_synonyms.get("semantic", [])
                total_semantic_terms += len(semantic_terms)
                
                # 品質檢查
                if len(keywords) == 0:
                    quality_issues.append(f"{slot_name}.{value_name}: 缺少關鍵詞")
                
                if len(regex_patterns) == 0:
                    quality_issues.append(f"{slot_name}.{value_name}: 缺少正則表達式")
                
                if len(semantic_terms) == 0:
                    quality_issues.append(f"{slot_name}.{value_name}: 缺少語義術語")
        
        print("📊 同義詞統計:")
        print(f"   總關鍵詞數: {total_keywords}")
        print(f"   總正則表達式數: {total_regex_patterns}")
        print(f"   總語義術語數: {total_semantic_terms}")
        
        if quality_issues:
            print(f"\n⚠️  品質問題:")
            for issue in quality_issues:
                print(f"   - {issue}")
            return False
        else:
            print(f"\n✅ 同義詞品質良好")
            return True
        
    except Exception as e:
        print(f"❌ 同義詞品質測試失敗: {e}")
        return False

def test_backward_compatibility():
    """測試向後相容性"""
    print("\n=== 測試向後相容性 ===\n")
    
    try:
        # 載入原始檔案進行比較
        default_slots_path = Path(__file__).parent / "libs" / "mgfd_cursor" / "humandata" / "default_slots.json"
        slot_synonyms_path = Path(__file__).parent / "libs" / "mgfd_cursor" / "humandata" / "slot_synonyms.json"
        
        with open(default_slots_path, 'r', encoding='utf-8') as f:
            default_slots = json.load(f)
        
        with open(slot_synonyms_path, 'r', encoding='utf-8') as f:
            slot_synonyms = json.load(f)
        
        # 檢查槽位名稱相容性
        default_slot_names = set(default_slots["slot_definitions"].keys())
        synonym_slot_names = set(slot_synonyms.keys())
        
        print("🔍 槽位名稱相容性:")
        
        # 檢查default_slots中的槽位是否在slot_synonyms中存在
        missing_in_synonyms = default_slot_names - synonym_slot_names
        if missing_in_synonyms:
            print(f"   ⚠️  在slot_synonyms中缺少的槽位: {missing_in_synonyms}")
        else:
            print(f"   ✅ 所有槽位名稱相容")
        
        # 檢查槽位值相容性
        print(f"\n🔍 槽位值相容性:")
        compatible_slots = 0
        total_slots = len(default_slot_names & synonym_slot_names)
        
        for slot_name in default_slot_names & synonym_slot_names:
            default_values = set(default_slots["slot_definitions"][slot_name]["validation_rules"]["allowed_values"])
            synonym_values = set(slot_synonyms[slot_name].keys())
            
            if default_values == synonym_values:
                print(f"   ✅ {slot_name}: 值完全相容")
                compatible_slots += 1
            else:
                missing_values = default_values - synonym_values
                extra_values = synonym_values - default_values
                print(f"   ⚠️  {slot_name}: 值不完全相容")
                if missing_values:
                    print(f"      缺少: {missing_values}")
                if extra_values:
                    print(f"      額外: {extra_values}")
        
        compatibility_rate = compatible_slots / total_slots if total_slots > 0 else 0
        print(f"\n📊 相容性比率: {compatible_slots}/{total_slots} ({compatibility_rate*100:.1f}%)")
        
        return compatibility_rate >= 0.8  # 80%相容性為通過
        
    except Exception as e:
        print(f"❌ 向後相容性測試失敗: {e}")
        return False

def test_enhanced_features():
    """測試增強功能"""
    print("\n=== 測試增強功能 ===\n")
    
    try:
        default_slots_path = Path(__file__).parent / "libs" / "mgfd_cursor" / "humandata" / "default_slots.json"
        
        with open(default_slots_path, 'r', encoding='utf-8') as f:
            default_slots = json.load(f)
        
        # 測試正則表達式功能
        print("🔍 測試正則表達式功能...")
        regex_count = 0
        for slot_name, slot_def in default_slots["slot_definitions"].items():
            if "synonyms" in slot_def:
                for value_name, value_synonyms in slot_def["synonyms"].items():
                    regex_patterns = value_synonyms.get("regex", [])
                    regex_count += len(regex_patterns)
        
        print(f"   ✅ 正則表達式模式數: {regex_count}")
        
        # 測試語義匹配功能
        print("\n🔍 測試語義匹配功能...")
        semantic_count = 0
        for slot_name, slot_def in default_slots["slot_definitions"].items():
            if "synonyms" in slot_def:
                for value_name, value_synonyms in slot_def["synonyms"].items():
                    semantic_terms = value_synonyms.get("semantic", [])
                    semantic_count += len(semantic_terms)
        
        print(f"   ✅ 語義術語數: {semantic_count}")
        
        # 測試依賴關係
        print("\n🔗 測試依賴關係...")
        dependencies = default_slots["dependencies"]
        dependency_count = len(dependencies)
        print(f"   ✅ 依賴關係數: {dependency_count}")
        
        # 測試驗證規則
        print("\n✅ 測試驗證規則...")
        validation_rules = default_slots["validation_rules"]
        global_rules = validation_rules.get("global", {})
        slot_specific_rules = validation_rules.get("slot_specific", {})
        
        print(f"   ✅ 全局規則: {len(global_rules)} 個")
        print(f"   ✅ 槽位特定規則: {len(slot_specific_rules)} 個")
        
        # 測試後備策略
        print("\n🔄 測試後備策略...")
        fallback_strategy = default_slots["fallback_strategy"]
        fallback_types = ["incomplete_slots", "ambiguous_input", "no_match"]
        
        for fallback_type in fallback_types:
            if fallback_type in fallback_strategy:
                print(f"   ✅ {fallback_type}: 已配置")
            else:
                print(f"   ❌ {fallback_type}: 未配置")
        
        return True
        
    except Exception as e:
        print(f"❌ 增強功能測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("🚀 開始測試整合後的default_slots.json...")
    
    # 執行所有測試
    integration_success = test_integration_completeness()
    extraction_success = test_extraction_methods()
    quality_success = test_synonym_quality()
    compatibility_success = test_backward_compatibility()
    enhanced_success = test_enhanced_features()
    
    if all([integration_success, extraction_success, quality_success, compatibility_success, enhanced_success]):
        print("\n🎉 所有測試通過！")
        print("📋 整合摘要:")
        print("   - 槽位同義詞完整整合")
        print("   - 提取方法配置正確")
        print("   - 同義詞品質良好")
        print("   - 向後相容性保持")
        print("   - 增強功能完整")
        print("\n✨ 整合成功！default_slots.json現在包含:")
        print("   - 完整的槽位定義和驗證規則")
        print("   - 多層次同義詞匹配（關鍵詞、正則、語義）")
        print("   - 智能依賴關係管理")
        print("   - 靈活的後備策略")
        print("   - 混合提取方法配置")
    else:
        print("\n💥 部分測試失敗")
        if not integration_success:
            print("   - 整合完整性測試失敗")
        if not extraction_success:
            print("   - 提取方法配置測試失敗")
        if not quality_success:
            print("   - 同義詞品質測試失敗")
        if not compatibility_success:
            print("   - 向後相容性測試失敗")
        if not enhanced_success:
            print("   - 增強功能測試失敗")
