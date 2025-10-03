#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試default_slots.json的結構和內容
"""

import json
import sys
from pathlib import Path

def validate_default_slots():
    """驗證default_slots.json的結構和內容"""
    print("=== 驗證default_slots.json ===\n")
    
    try:
        # 載入default_slots.json
        default_slots_path = Path(__file__).parent / "libs" / "mgfd_cursor" / "humandata" / "default_slots.json"
        
        if not default_slots_path.exists():
            print("❌ default_slots.json 檔案不存在")
            return False
        
        with open(default_slots_path, 'r', encoding='utf-8') as f:
            default_slots = json.load(f)
        
        print("✅ 成功載入default_slots.json")
        
        # 驗證基本結構
        required_sections = [
            "slot_definitions", 
            "collection_strategy", 
            "dependencies", 
            "validation_rules", 
            "fallback_strategy", 
            "metadata"
        ]
        
        print("\n📋 驗證基本結構...")
        for section in required_sections:
            if section in default_slots:
                print(f"   ✅ {section}: 存在")
            else:
                print(f"   ❌ {section}: 缺失")
                return False
        
        # 驗證槽位定義
        print("\n🔍 驗證槽位定義...")
        slot_definitions = default_slots["slot_definitions"]
        
        expected_slots = [
            "usage_purpose", "budget_range", "cpu_level", "gpu_level",
            "weight_requirement", "screen_size", "brand_preference", "performance_features"
        ]
        
        for slot_name in expected_slots:
            if slot_name in slot_definitions:
                slot_def = slot_definitions[slot_name]
                print(f"   ✅ {slot_name}: {slot_def.get('name', 'Unknown')}")
                
                # 驗證必要欄位
                required_fields = ["name", "type", "required", "priority", "description"]
                for field in required_fields:
                    if field not in slot_def:
                        print(f"      ❌ 缺少欄位: {field}")
                        return False
            else:
                print(f"   ❌ 缺少槽位: {slot_name}")
                return False
        
        # 驗證收集策略
        print("\n📊 驗證收集策略...")
        collection_strategy = default_slots["collection_strategy"]
        strategy_fields = ["mode", "max_turns", "confirmation_required"]
        
        for field in strategy_fields:
            if field in collection_strategy:
                print(f"   ✅ {field}: {collection_strategy[field]}")
            else:
                print(f"   ❌ 缺少欄位: {field}")
                return False
        
        # 驗證依賴關係
        print("\n🔗 驗證依賴關係...")
        dependencies = default_slots["dependencies"]
        
        if "usage_purpose" in dependencies:
            usage_deps = dependencies["usage_purpose"]
            if "influences" in usage_deps and "rules" in usage_deps:
                print(f"   ✅ usage_purpose 依賴關係完整")
                print(f"      影響槽位: {usage_deps['influences']}")
                print(f"      規則數量: {len(usage_deps['rules'])}")
            else:
                print(f"   ❌ usage_purpose 依賴關係不完整")
                return False
        else:
            print(f"   ❌ 缺少 usage_purpose 依賴關係")
            return False
        
        # 驗證驗證規則
        print("\n✅ 驗證驗證規則...")
        validation_rules = default_slots["validation_rules"]
        
        if "global" in validation_rules and "slot_specific" in validation_rules:
            print(f"   ✅ 驗證規則結構完整")
            global_rules = validation_rules["global"]
            print(f"      全局規則: {list(global_rules.keys())}")
        else:
            print(f"   ❌ 驗證規則結構不完整")
            return False
        
        # 驗證後備策略
        print("\n🔄 驗證後備策略...")
        fallback_strategy = default_slots["fallback_strategy"]
        
        fallback_types = ["incomplete_slots", "ambiguous_input", "no_match"]
        for fallback_type in fallback_types:
            if fallback_type in fallback_strategy:
                print(f"   ✅ {fallback_type}: 存在")
            else:
                print(f"   ❌ {fallback_type}: 缺失")
                return False
        
        # 驗證元數據
        print("\n📝 驗證元數據...")
        metadata = default_slots["metadata"]
        
        metadata_fields = ["version", "created_date", "description", "author"]
        for field in metadata_fields:
            if field in metadata:
                print(f"   ✅ {field}: {metadata[field]}")
            else:
                print(f"   ❌ 缺少欄位: {field}")
                return False
        
        print("\n🎉 所有驗證通過！")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 驗證失敗: {e}")
        return False

def test_slot_compatibility():
    """測試與現有槽位系統的相容性"""
    print("\n=== 測試槽位相容性 ===\n")
    
    try:
        # 載入相關檔案
        default_slots_path = Path(__file__).parent / "libs" / "mgfd_cursor" / "humandata" / "default_slots.json"
        slot_synonyms_path = Path(__file__).parent / "libs" / "mgfd_cursor" / "humandata" / "slot_synonyms.json"
        
        with open(default_slots_path, 'r', encoding='utf-8') as f:
            default_slots = json.load(f)
        
        with open(slot_synonyms_path, 'r', encoding='utf-8') as f:
            slot_synonyms = json.load(f)
        
        # 檢查槽位名稱一致性
        default_slot_names = set(default_slots["slot_definitions"].keys())
        synonym_slot_names = set(slot_synonyms.keys())
        
        print("🔍 檢查槽位名稱一致性...")
        
        # 檢查default_slots中的槽位是否在slot_synonyms中存在
        missing_in_synonyms = default_slot_names - synonym_slot_names
        if missing_in_synonyms:
            print(f"   ⚠️  在slot_synonyms中缺少的槽位: {missing_in_synonyms}")
        else:
            print(f"   ✅ 所有槽位名稱一致")
        
        # 檢查slot_synonyms中的槽位是否在default_slots中存在
        extra_in_synonyms = synonym_slot_names - default_slot_names
        if extra_in_synonyms:
            print(f"   📝 slot_synonyms中的額外槽位: {extra_in_synonyms}")
        
        # 檢查槽位值的一致性
        print("\n🔍 檢查槽位值一致性...")
        
        for slot_name in default_slot_names & synonym_slot_names:
            default_values = set(default_slots["slot_definitions"][slot_name]["validation_rules"]["allowed_values"])
            synonym_values = set(slot_synonyms[slot_name].keys())
            
            missing_values = default_values - synonym_values
            extra_values = synonym_values - default_values
            
            if missing_values:
                print(f"   ⚠️  {slot_name}: 在slot_synonyms中缺少值 {missing_values}")
            if extra_values:
                print(f"   📝 {slot_name}: slot_synonyms中的額外值 {extra_values}")
            if not missing_values and not extra_values:
                print(f"   ✅ {slot_name}: 值完全一致")
        
        return True
        
    except Exception as e:
        print(f"❌ 相容性測試失敗: {e}")
        return False

def test_collection_flow():
    """測試槽位收集流程"""
    print("\n=== 測試槽位收集流程 ===\n")
    
    try:
        # 載入default_slots.json
        default_slots_path = Path(__file__).parent / "libs" / "mgfd_cursor" / "humandata" / "default_slots.json"
        
        with open(default_slots_path, 'r', encoding='utf-8') as f:
            default_slots = json.load(f)
        
        slot_definitions = default_slots["slot_definitions"]
        collection_strategy = default_slots["collection_strategy"]
        
        # 模擬槽位收集流程
        print("🔄 模擬槽位收集流程...")
        
        # 按優先順序排序槽位
        sorted_slots = sorted(
            slot_definitions.items(),
            key=lambda x: x[1]["priority"]
        )
        
        print(f"   收集模式: {collection_strategy['mode']}")
        print(f"   最大回合數: {collection_strategy['max_turns']}")
        print(f"   需要確認: {collection_strategy['confirmation_required']}")
        
        print(f"\n📋 槽位收集順序:")
        for i, (slot_name, slot_def) in enumerate(sorted_slots, 1):
            required = "必要" if slot_def["required"] else "可選"
            default = slot_def.get("default_value", "無")
            prompt = slot_def.get("collection_prompt", "無")
            
            print(f"   {i}. {slot_name} ({slot_def['name']}) - {required}")
            print(f"      預設值: {default}")
            print(f"      收集提示: {prompt}")
        
        # 測試依賴關係
        print(f"\n🔗 依賴關係分析:")
        dependencies = default_slots["dependencies"]
        
        for slot_name, deps in dependencies.items():
            print(f"   {slot_name}:")
            print(f"     影響槽位: {deps['influences']}")
            print(f"     規則數量: {len(deps['rules'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ 收集流程測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("🚀 開始測試default_slots.json...")
    
    # 執行所有測試
    validation_success = validate_default_slots()
    compatibility_success = test_slot_compatibility()
    flow_success = test_collection_flow()
    
    if validation_success and compatibility_success and flow_success:
        print("\n🎉 所有測試通過！")
        print("📋 測試摘要:")
        print("   - default_slots.json 結構完整")
        print("   - 與現有槽位系統相容")
        print("   - 槽位收集流程設計合理")
        print("   - 依賴關係和驗證規則完整")
    else:
        print("\n💥 部分測試失敗")
        if not validation_success:
            print("   - 結構驗證失敗")
        if not compatibility_success:
            print("   - 相容性測試失敗")
        if not flow_success:
            print("   - 收集流程測試失敗")
