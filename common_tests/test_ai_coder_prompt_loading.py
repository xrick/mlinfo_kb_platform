#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 AI Coder 提示載入功能
"""

import sys
import os
from pathlib import Path

# 添加專案根目錄到 Python 路徑
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_ai_coder_prompt_loading():
    """測試 AI Coder 提示載入功能"""
    print("🧪 測試 AI Coder 提示載入功能...")
    
    # 測試文件路徑
    prompt_path = Path(__file__).parent / 'HumanData' / 'PromptsHub' / 'MGFD_Principal_Prompts' / 'ai_coder_indepnedent_initialization_prompt.txt'
    
    print(f"📁 檢查提示文件路徑: {prompt_path}")
    
    if prompt_path.exists():
        print("✅ 提示文件存在")
        
        # 讀取文件內容
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"📄 文件大小: {len(content)} 字符")
            print(f"📝 文件前100字符: {content[:100]}...")
            print("✅ 文件讀取成功")
        except Exception as e:
            print(f"❌ 文件讀取失敗: {e}")
            return False
    else:
        print("❌ 提示文件不存在")
        return False
    
    # 測試 LLM 管理器中的載入功能
    print("\n🔧 測試 LLM 管理器載入功能...")
    
    try:
        from libs.mgfd_cursor_currently_deprecated.llm_manager import MGFDLLMManager
        
        # 創建 LLM 管理器實例
        llm_manager = MGFDLLMManager()
        
        # 獲取 AI Coder 提示
        ai_coder_prompt = llm_manager.get_ai_coder_prompt()
        
        if ai_coder_prompt:
            print(f"✅ AI Coder 提示載入成功")
            print(f"📄 載入的提示大小: {len(ai_coder_prompt)} 字符")
            print(f"📝 載入的提示前100字符: {ai_coder_prompt[:100]}...")
        else:
            print("❌ AI Coder 提示載入失敗")
            return False
        
        # 測試狀態獲取
        status = llm_manager.get_status()
        if status.get('ai_coder_prompt_loaded', False):
            print("✅ 狀態顯示 AI Coder 提示已載入")
        else:
            print("❌ 狀態顯示 AI Coder 提示未載入")
            return False
            
    except Exception as e:
        print(f"❌ LLM 管理器測試失敗: {e}")
        return False
    
    # 測試 mgfd_modules 中的載入功能
    print("\n🔧 測試 mgfd_modules LLM 管理器載入功能...")
    
    try:
        from libs.mgfd_modules.llm_manager import MGFDLLMManager as MGFDModulesLLMManager
        
        # 創建 LLM 管理器實例
        llm_manager = MGFDModulesLLMManager()
        
        # 獲取 AI Coder 提示
        ai_coder_prompt = llm_manager.get_ai_coder_prompt()
        
        if ai_coder_prompt:
            print(f"✅ mgfd_modules AI Coder 提示載入成功")
            print(f"📄 載入的提示大小: {len(ai_coder_prompt)} 字符")
        else:
            print("❌ mgfd_modules AI Coder 提示載入失敗")
            return False
        
        # 測試狀態獲取
        status = llm_manager.get_status()
        if status.get('ai_coder_prompt_loaded', False):
            print("✅ mgfd_modules 狀態顯示 AI Coder 提示已載入")
        else:
            print("❌ mgfd_modules 狀態顯示 AI Coder 提示未載入")
            return False
            
    except Exception as e:
        print(f"❌ mgfd_modules LLM 管理器測試失敗: {e}")
        return False
    
    print("\n🎉 所有測試通過！AI Coder 提示載入功能正常工作。")
    return True

if __name__ == "__main__":
    success = test_ai_coder_prompt_loading()
    if success:
        print("\n✅ 測試完成：AI Coder 提示載入功能正常")
        sys.exit(0)
    else:
        print("\n❌ 測試完成：AI Coder 提示載入功能有問題")
        sys.exit(1)
