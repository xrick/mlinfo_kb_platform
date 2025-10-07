#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
單元測試：LLMInitializer Singleton Pattern 實現
測試執行緒安全、單例保證、配置管理等功能
"""

import sys
from pathlib import Path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

import threading
import time
from libs.RAG.LLM.LLMInitializer import LLMInitializer


class TestLLMSingleton:
    """LLMInitializer Singleton Pattern 測試套件"""

    def setup_method(self):
        """每個測試前重置單例實例"""
        LLMInitializer.reset_instance()

    def teardown_method(self):
        """每個測試後清理"""
        LLMInitializer.reset_instance()

    def test_singleton_same_instance(self):
        """
        測試：多次調用返回同一實例
        驗證 Singleton Pattern 的核心功能
        """
        instance1 = LLMInitializer.get_instance()
        instance2 = LLMInitializer.get_instance()
        instance3 = LLMInitializer()

        # 所有實例應該相同
        assert instance1 is instance2, "get_instance() 應返回同一實例"
        assert instance2 is instance3, "直接實例化應返回同一實例"
        assert instance1 is instance3, "不同調用方式應返回同一實例"

    def test_thread_safety(self):
        """
        測試：多執行緒環境下的單例保證
        驗證 Double-Checked Locking 的正確性
        """
        instances = []
        lock = threading.Lock()

        def create_instance():
            """在執行緒中創建實例"""
            instance = LLMInitializer.get_instance()
            with lock:
                instances.append(instance)

        # 創建 20 個執行緒同時獲取實例
        threads = [threading.Thread(target=create_instance) for _ in range(20)]

        # 啟動所有執行緒
        for t in threads:
            t.start()

        # 等待所有執行緒完成
        for t in threads:
            t.join()

        # 驗證所有實例相同
        assert len(instances) == 20, "應創建 20 個引用"
        assert all(inst is instances[0] for inst in instances), \
            "所有執行緒應獲取同一個實例"

    def test_initialization_once(self):
        """
        測試：初始化只執行一次
        驗證 _initialized flag 的正確性
        """
        # 首次創建
        instance1 = LLMInitializer.get_instance(
            model_name="gpt-oss:20b",
            temperature=0.5
        )
        original_llm = instance1.llm
        original_temp = instance1.temperature

        # 再次創建（不同參數）
        instance2 = LLMInitializer.get_instance(
            model_name="gpt-oss:20b",
            temperature=0.9  # 不同的 temperature
        )

        # 驗證實例相同且配置未變
        assert instance1 is instance2, "應返回同一實例"
        assert instance2.llm is original_llm, "LLM 實例不應重新創建"
        assert instance2.temperature == original_temp, \
            "後續調用不應改變原有配置"

    def test_reconfigure(self):
        """
        測試：動態重新配置
        驗證 reconfigure() 方法的正確性
        """
        # 創建實例
        instance = LLMInitializer.get_instance(temperature=0.3)
        original_llm = instance.llm

        assert instance.temperature == 0.3, "初始 temperature 應為 0.3"

        # 重新配置溫度
        instance.reconfigure(temperature=0.8)
        assert instance.temperature == 0.8, "temperature 應更新為 0.8"

        # 驗證 LLM 實例已重新創建
        assert instance.llm is not original_llm, \
            "reconfigure 後應創建新的 LLM 實例"

        # 驗證其他實例引用看到的是相同的配置
        instance2 = LLMInitializer.get_instance()
        assert instance2 is instance, "應返回同一實例"
        assert instance2.temperature == 0.8, "新引用應看到更新後的配置"

    def test_backward_compatibility(self):
        """
        測試：向後相容性
        驗證舊的調用方式仍然有效
        """
        # 方式 1: 直接實例化
        instance1 = LLMInitializer(model_name="gpt-oss:20b")

        # 方式 2: 使用 get_instance
        instance2 = LLMInitializer.get_instance(model_name="gpt-oss:20b")

        # 兩種方式應返回同一實例
        assert instance1 is instance2, "不同調用方式應返回同一實例"

    def test_reset_instance(self):
        """
        測試：重置實例功能
        驗證 reset_instance() 方法（僅測試用）
        """
        # 創建實例
        instance1 = LLMInitializer.get_instance(temperature=0.5)
        assert instance1.temperature == 0.5

        # 重置實例
        LLMInitializer.reset_instance()

        # 創建新實例（不同配置）
        instance2 = LLMInitializer.get_instance(temperature=0.9)

        # 驗證是新實例且配置不同
        assert instance2 is not instance1, "重置後應創建新實例"
        assert instance2.temperature == 0.9, "新實例應使用新配置"

    def test_concurrent_initialization(self):
        """
        測試：並發初始化的安全性
        模擬高並發場景下的實例創建
        """
        instances = []
        errors = []
        lock = threading.Lock()

        def concurrent_create():
            """並發創建實例"""
            try:
                time.sleep(0.001)  # 輕微延遲增加競爭條件
                instance = LLMInitializer.get_instance()
                with lock:
                    instances.append(instance)
            except Exception as e:
                with lock:
                    errors.append(e)

        # 創建 50 個執行緒模擬高並發
        threads = [threading.Thread(target=concurrent_create) for _ in range(50)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # 驗證無錯誤且所有實例相同
        assert len(errors) == 0, f"不應有錯誤發生: {errors}"
        assert len(instances) == 50, "應有 50 個引用"
        assert all(inst is instances[0] for inst in instances), \
            "高並發下所有實例應相同"

    def test_get_llm_method(self):
        """
        測試：get_llm() 方法正常工作
        驗證 Singleton 不影響原有功能
        """
        instance = LLMInitializer.get_instance()
        llm = instance.get_llm()

        # 驗證返回的是 LLM 實例
        assert llm is not None, "get_llm() 應返回 LLM 實例"
        assert llm is instance.llm, "get_llm() 應返回內部的 llm 屬性"

    def test_model_attributes(self):
        """
        測試：模型屬性正確設置
        驗證 Singleton 不影響屬性初始化
        """
        instance = LLMInitializer.get_instance(
            model_name="gpt-oss:20b",
            temperature=0.7,
            request_timeout=120
        )

        assert instance.model_name == "gpt-oss:20b"
        assert instance.temperature == 0.7
        assert instance.request_timeout == 120
        assert instance.max_context_tokens == 131072  # 根據 DEFAULT_CONTEXT_LIMITS


class TestLLMSingletonIntegration:
    """整合測試：驗證在實際使用場景中的行為"""

    def setup_method(self):
        """每個測試前重置"""
        LLMInitializer.reset_instance()

    def teardown_method(self):
        """每個測試後清理"""
        LLMInitializer.reset_instance()

    def test_multiple_modules_share_instance(self):
        """
        測試：模擬多個模組使用 LLM
        驗證記憶體共享效果
        """
        # 模組 1: MGFDKernel
        kernel_llm_init = LLMInitializer.get_instance(
            model_name="gpt-oss:20b",
            temperature=0.1
        )

        # 模組 2: KnowledgeManager
        km_llm_init = LLMInitializer.get_instance(
            model_name="gpt-oss:20b",
            temperature=0.1
        )

        # 模組 3: ResponseGenerator
        rg_llm_init = LLMInitializer.get_instance(
            model_name="gpt-oss:20b",
            temperature=0.1
        )

        # 驗證所有模組共享同一實例
        assert kernel_llm_init is km_llm_init, "MGFDKernel 和 KnowledgeManager 應共享實例"
        assert km_llm_init is rg_llm_init, "KnowledgeManager 和 ResponseGenerator 應共享實例"
        assert kernel_llm_init is rg_llm_init, "所有模組應共享同一個 LLM 實例"


def run_all_tests():
    """運行所有測試"""
    print("=" * 70)
    print("🧪 LLMInitializer Singleton Pattern 測試套件")
    print("=" * 70)
    print()

    test_suite = TestLLMSingleton()
    integration_suite = TestLLMSingletonIntegration()

    tests = [
        ("單例保證測試", test_suite.test_singleton_same_instance),
        ("執行緒安全測試", test_suite.test_thread_safety),
        ("初始化唯一性測試", test_suite.test_initialization_once),
        ("重新配置測試", test_suite.test_reconfigure),
        ("向後相容性測試", test_suite.test_backward_compatibility),
        ("重置實例測試", test_suite.test_reset_instance),
        ("並發初始化測試", test_suite.test_concurrent_initialization),
        ("get_llm 方法測試", test_suite.test_get_llm_method),
        ("模型屬性測試", test_suite.test_model_attributes),
        ("多模組共享測試", integration_suite.test_multiple_modules_share_instance),
    ]

    passed = 0
    failed = 0
    errors = []

    for test_name, test_func in tests:
        try:
            print(f"▶ 執行: {test_name}...", end=" ")

            # 測試前設置
            if hasattr(test_func, '__self__'):
                test_instance = test_func.__self__
                if hasattr(test_instance, 'setup_method'):
                    test_instance.setup_method()

            # 執行測試
            test_func()

            # 測試後清理
            if hasattr(test_func, '__self__'):
                test_instance = test_func.__self__
                if hasattr(test_instance, 'teardown_method'):
                    test_instance.teardown_method()

            print("✓ PASSED")
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED")
            failed += 1
            errors.append((test_name, str(e) if str(e) else "Assertion failed"))
        except Exception as e:
            print(f"✗ ERROR")
            failed += 1
            errors.append((test_name, f"Exception: {str(e)}"))

    # 測試總結
    print()
    print("=" * 70)
    print(f"測試結果: {passed} passed, {failed} failed")
    print("=" * 70)

    if errors:
        print("\n❌ 失敗的測試詳情:")
        for test_name, error in errors:
            print(f"\n  {test_name}:")
            print(f"    {error}")
    else:
        print("\n✅ 所有測試通過！Singleton Pattern 實現正確。")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
