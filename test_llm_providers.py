#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 LLM 提供商可用性和功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from libs.mgfd_cursor.llm_manager import MGFDLLMManager

def test_llm_provider_imports():
    """測試 LLM 提供商導入狀態"""
    print("=== 測試 LLM 提供商導入狀態 ===\n")
    
    try:
        from libs.mgfd_cursor.llm_manager import (
            OLLAMA_AVAILABLE, OPENAI_AVAILABLE, ANTHROPIC_AVAILABLE, LANGCHAIN_AVAILABLE
        )
        
        print(f"Ollama 可用: {'✓' if OLLAMA_AVAILABLE else '✗'}")
        print(f"OpenAI 可用: {'✓' if OPENAI_AVAILABLE else '✗'}")
        print(f"Anthropic 可用: {'✓' if ANTHROPIC_AVAILABLE else '✗'}")
        print(f"LangChain 整體可用: {'✓' if LANGCHAIN_AVAILABLE else '✗'}")
        
        return LANGCHAIN_AVAILABLE
        
    except Exception as e:
        print(f"✗ 導入測試失敗: {e}")
        return False

def test_ollama_provider():
    """測試 Ollama 提供商"""
    print("\n=== 測試 Ollama 提供商 ===")
    
    try:
        # 創建 Ollama LLM 管理器
        llm_manager = MGFDLLMManager(
            provider="ollama",
            model_name="deepseek-r1:7b",
            temperature=0.1
        )
        
        # 檢查狀態
        status = llm_manager.get_status()
        print(f"Provider: {status['provider']}")
        print(f"Model: {status['model_name']}")
        print(f"LLM Available: {'✓' if status['llm_available'] else '✗'}")
        print(f"Provider Availability: {status['provider_availability']}")
        
        # 測試調用
        if status['llm_available']:
            try:
                response = llm_manager.invoke("請用一句話回應: 你好")
                print(f"✓ Ollama 回應: {response[:100]}...")
                return True
            except Exception as e:
                print(f"✗ Ollama 調用失敗: {e}")
                return False
        else:
            print("✗ Ollama LLM 不可用")
            return False
            
    except Exception as e:
        print(f"✗ Ollama 測試失敗: {e}")
        return False

def test_openai_provider():
    """測試 OpenAI 提供商 (不需要 API key，只測試導入)"""
    print("\n=== 測試 OpenAI 提供商 (導入測試) ===")
    
    try:
        # 創建 OpenAI LLM 管理器 (不提供 API key，預期會失敗但導入成功)
        llm_manager = MGFDLLMManager(
            provider="openai",
            model_name="gpt-3.5-turbo",
            temperature=0.1
        )
        
        # 檢查狀態
        status = llm_manager.get_status()
        print(f"Provider: {status['provider']}")
        print(f"Model: {status['model_name']}")
        print(f"OpenAI 套件可用: {'✓' if status['provider_availability']['openai'] else '✗'}")
        
        # 不測試實際調用，因為需要 API key
        print("📝 注意: 實際調用需要 OpenAI API key")
        return status['provider_availability']['openai']
        
    except Exception as e:
        print(f"✗ OpenAI 測試失敗: {e}")
        return False

def test_anthropic_provider():
    """測試 Anthropic 提供商 (不需要 API key，只測試導入)"""
    print("\n=== 測試 Anthropic 提供商 (導入測試) ===")
    
    try:
        # 創建 Anthropic LLM 管理器 (不提供 API key，預期會失敗但導入成功)
        llm_manager = MGFDLLMManager(
            provider="anthropic",
            model_name="claude-3-sonnet-20240229",
            temperature=0.1
        )
        
        # 檢查狀態
        status = llm_manager.get_status()
        print(f"Provider: {status['provider']}")
        print(f"Model: {status['model_name']}")
        print(f"Anthropic 套件可用: {'✓' if status['provider_availability']['anthropic'] else '✗'}")
        
        # 不測試實際調用，因為需要 API key
        print("📝 注意: 實際調用需要 Anthropic API key")
        return status['provider_availability']['anthropic']
        
    except Exception as e:
        print(f"✗ Anthropic 測試失敗: {e}")
        return False

def test_mock_fallback():
    """測試模擬回應機制"""
    print("\n=== 測試模擬回應機制 ===")
    
    try:
        # 創建一個不存在的提供商來觸發模擬模式
        llm_manager = MGFDLLMManager(provider="invalid_provider")
        
        # 測試模擬回應
        response = llm_manager.invoke("測試提示詞")
        print(f"✓ 模擬回應: {response}")
        
        # 測試槽位分析模擬
        mock_slot_response = llm_manager.classify_slot("分析槽位的提示詞")
        print(f"✓ 模擬槽位分類: {mock_slot_response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ 模擬回應測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🔍 LLM 提供商綜合測試\n")
    
    # 測試結果收集
    results = {
        "imports": False,
        "ollama": False,
        "openai": False,
        "anthropic": False,
        "mock_fallback": False
    }
    
    # 執行各項測試
    results["imports"] = test_llm_provider_imports()
    results["ollama"] = test_ollama_provider()
    results["openai"] = test_openai_provider()
    results["anthropic"] = test_anthropic_provider()
    results["mock_fallback"] = test_mock_fallback()
    
    # 總結報告
    print("\n" + "="*50)
    print("📊 測試結果總結")
    print("="*50)
    
    for test_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name.ljust(15)}: {status}")
    
    # 整體評估
    critical_tests = ["imports", "ollama", "mock_fallback"]
    critical_passed = all(results[test] for test in critical_tests)
    
    print(f"\n🎯 關鍵功能狀態: {'✅ 正常' if critical_passed else '❌ 異常'}")
    
    if critical_passed:
        print("🎉 LLM 系統已準備就緒！")
        print("💡 Ollama 可正常使用，OpenAI/Anthropic 需要相應 API keys")
    else:
        print("⚠️  LLM 系統存在問題，請檢查配置")
    
    return critical_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)