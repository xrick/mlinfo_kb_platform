#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 Prompt 管理系統
"""

import sys
import os
from pathlib import Path

# 添加專案根目錄到 Python 路徑
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_prompt_management_system():
    """測試 Prompt 管理系統"""
    print("🧪 測試 Prompt 管理系統...")
    
    try:
        # 導入 Prompt 管理系統
        from libs.PromptManagementHandler import (
            PromptManager, get_global_prompt_manager,
            get_prompt, get_multiple_prompts, list_available_prompts,
            get_ai_coder_initialization_prompt, get_mgfd_principal_prompt,
            get_combined_prompt, get_cache_stats
        )
        
        print("✅ 成功導入 Prompt 管理系統")
        
        # 測試 1: 獲取全域管理器
        print("\n🔧 測試 1: 獲取全域管理器")
        manager = get_global_prompt_manager()
        print(f"✅ 全域管理器類型: {type(manager).__name__}")
        print(f"✅ 基礎路徑: {manager.base_path}")
        
        # 測試 2: 列出可用 Prompt
        print("\n🔧 測試 2: 列出可用 Prompt")
        available_prompts = list_available_prompts()
        print(f"✅ 可用 Prompt 數量: {len(available_prompts)}")
        print(f"✅ 可用 Prompt: {available_prompts}")
        
        # 測試 3: 獲取 AI Coder 提示
        print("\n🔧 測試 3: 獲取 AI Coder 提示")
        ai_coder_prompt = get_ai_coder_initialization_prompt()
        if ai_coder_prompt:
            print(f"✅ AI Coder 提示載入成功")
            print(f"📄 提示大小: {len(ai_coder_prompt)} 字符")
            print(f"📝 提示前100字符: {ai_coder_prompt[:100]}...")
        else:
            print("❌ AI Coder 提示載入失敗")
            return False
        
        # 測試 4: 獲取 MGFD 主提示
        print("\n🔧 測試 4: 獲取 MGFD 主提示")
        mgfd_prompt = get_mgfd_principal_prompt()
        if mgfd_prompt:
            print(f"✅ MGFD 主提示載入成功")
            print(f"📄 提示大小: {len(mgfd_prompt)} 字符")
            print(f"📝 提示前100字符: {mgfd_prompt[:100]}...")
        else:
            print("❌ MGFD 主提示載入失敗")
            return False
        
        # 測試 5: 批量獲取多個 Prompt
        print("\n🔧 測試 5: 批量獲取多個 Prompt")
        multiple_prompts = get_multiple_prompts(["ai_coder_initialization", "mgfd_principal"])
        print(f"✅ 批量獲取成功，獲取到 {len(multiple_prompts)} 個 Prompt")
        for name, content in multiple_prompts.items():
            print(f"  - {name}: {len(content)} 字符")
        
        # 測試 6: 組合 Prompt
        print("\n🔧 測試 6: 組合 Prompt")
        combined_prompt = get_combined_prompt(["mgfd_principal", "ai_coder_initialization"])
        if combined_prompt:
            print(f"✅ Prompt 組合成功")
            print(f"📄 組合後大小: {len(combined_prompt)} 字符")
            print(f"📝 組合後前100字符: {combined_prompt[:100]}...")
        else:
            print("❌ Prompt 組合失敗")
            return False
        
        # 測試 7: 緩存統計
        print("\n🔧 測試 7: 緩存統計")
        cache_stats = get_cache_stats()
        print(f"✅ 緩存統計: {cache_stats}")
        
        # 測試 8: 測試自定義 Prompt 路徑
        print("\n🔧 測試 8: 測試自定義 Prompt 路徑")
        test_prompt_path = "HumanData/PromptsHub/MGFD_Principal_Prompts/ai_coder_indepnedent_initialization_prompt.txt"
        custom_prompt = get_prompt(test_prompt_path)
        if custom_prompt:
            print(f"✅ 自定義路徑 Prompt 載入成功")
            print(f"📄 自定義 Prompt 大小: {len(custom_prompt)} 字符")
        else:
            print("❌ 自定義路徑 Prompt 載入失敗")
        
        # 測試 9: 測試不存在的 Prompt
        print("\n🔧 測試 9: 測試不存在的 Prompt")
        non_existent_prompt = get_prompt("non_existent_prompt")
        if non_existent_prompt is None:
            print("✅ 正確處理不存在的 Prompt")
        else:
            print("❌ 錯誤處理不存在的 Prompt")
            return False
        
        print("\n🎉 所有測試通過！Prompt 管理系統正常工作。")
        return True
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prompt_manager_direct():
    """直接測試 PromptManager 類"""
    print("\n🧪 直接測試 PromptManager 類...")
    
    try:
        from libs.PromptManagementHandler import PromptManager
        
        # 創建新的管理器實例
        manager = PromptManager()
        
        # 測試基本功能
        print("✅ 創建 PromptManager 實例成功")
        
        # 測試獲取 Prompt
        ai_coder_prompt = manager.get_prompt("ai_coder_initialization")
        if ai_coder_prompt:
            print("✅ 直接管理器獲取 Prompt 成功")
        else:
            print("❌ 直接管理器獲取 Prompt 失敗")
            return False
        
        # 測試緩存功能
        print("🔧 測試緩存功能...")
        cached_prompts = manager.list_cached_prompts()
        print(f"✅ 已緩存的 Prompt: {cached_prompts}")
        
        # 測試重新載入
        print("🔧 測試重新載入功能...")
        reload_success = manager.reload_prompt("ai_coder_initialization")
        if reload_success:
            print("✅ 重新載入 Prompt 成功")
        else:
            print("❌ 重新載入 Prompt 失敗")
            return False
        
        print("✅ 直接測試 PromptManager 成功")
        return True
        
    except Exception as e:
        print(f"❌ 直接測試 PromptManager 失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 開始測試 Prompt 管理系統...")
    
    # 測試全域 API
    success1 = test_prompt_management_system()
    
    # 測試直接管理器
    success2 = test_prompt_manager_direct()
    
    if success1 and success2:
        print("\n🎉 所有測試通過！Prompt 管理系統完全正常。")
        sys.exit(0)
    else:
        print("\n❌ 部分測試失敗，請檢查系統配置。")
        sys.exit(1)
