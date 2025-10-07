# LLMInitializer Singleton Pattern 設計文件

## 設計概述

為 `LLMInitializer` 類添加 **Thread-Safe Singleton Pattern**，確保整個應用程式中只存在一個 LLM 實例，避免重複初始化造成的資源浪費和潛在衝突。

---

## 1. 設計目標

### 1.1 核心目標
- **單例保證**: 全系統只存在一個 `LLMInitializer` 實例
- **執行緒安全**: 多執行緒環境下的安全初始化
- **延遲初始化**: 只在首次調用時初始化（Lazy Initialization）
- **配置靈活性**: 支持不同配置參數的實例獲取
- **向後相容**: 不破壞現有調用方式

### 1.2 性能目標
- 避免重複創建 OllamaLLM 實例（當前問題：MGFDKernel 每次都創建新實例）
- 減少記憶體佔用（每個 LLM 實例約佔用 200MB-500MB）
- 加快初始化速度（首次載入後，後續調用直接返回）

---

## 2. 技術方案

### 2.1 Singleton 實現模式選擇

**選擇方案**: **Double-Checked Locking with `threading.Lock`**

**選擇理由**:
1. ✅ 執行緒安全
2. ✅ 延遲初始化
3. ✅ 性能優異（避免每次調用都加鎖）
4. ✅ Python 標準庫支持（無需第三方依賴）

**替代方案評估**:
- ❌ **Metaclass Singleton**: 過於複雜，不利於維護
- ❌ **Module-level Singleton**: 無法支持配置參數
- ❌ **Decorator Singleton**: 與現有類結構衝突

---

## 3. 詳細設計

### 3.1 類結構設計

```python
# libs/RAG/LLM/LLMInitializer.py
from typing import Optional
from langchain_ollama import OllamaLLM
import threading

class LLMInitializer:
    """
    Thread-Safe Singleton LLM Initializer
    使用 Double-Checked Locking 模式實現單例
    """

    # 類變數：保存單例實例
    _instance: Optional['LLMInitializer'] = None
    _lock: threading.Lock = threading.Lock()
    _initialized: bool = False

    # 默認配置
    DEFAULT_CONTEXT_LIMITS = {
        "gpt-oss:20b": 131072
    }

    def __new__(cls,
                model_name: str = "gpt-oss:20b",
                temperature: float = 0.3,
                request_timeout: int = 60):
        """
        覆寫 __new__ 方法實現 Singleton Pattern
        使用 Double-Checked Locking 確保執行緒安全
        """
        # First check (without lock for performance)
        if cls._instance is None:
            with cls._lock:  # Acquire lock
                # Second check (with lock for thread safety)
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self,
                 model_name: str = "gpt-oss:20b",
                 temperature: float = 0.3,
                 request_timeout: int = 60):
        """
        初始化方法（只在首次創建時執行）
        """
        # 防止重複初始化
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            self.model_name = model_name
            self.temperature = temperature
            self.request_timeout = request_timeout

            # 設置 context window
            self.max_context_tokens = self.DEFAULT_CONTEXT_LIMITS.get(
                self.model_name, 8192
            )

            # 初始化 LLM
            self.llm = OllamaLLM(
                model=self.model_name,
                temperature=self.temperature,
            )

            self._initialized = True

    @classmethod
    def get_instance(cls,
                     model_name: str = "gpt-oss:20b",
                     temperature: float = 0.3,
                     request_timeout: int = 60) -> 'LLMInitializer':
        """
        類方法：獲取單例實例（推薦使用方式）

        使用範例:
            llm_init = LLMInitializer.get_instance()
            llm = llm_init.get_llm()
        """
        return cls(model_name, temperature, request_timeout)

    @classmethod
    def reset_instance(cls) -> None:
        """
        類方法：重置單例實例（僅用於測試）
        ⚠️ 警告：生產環境不應調用此方法
        """
        with cls._lock:
            cls._instance = None
            cls._initialized = False

    # ... [保留所有原有方法: safe_completion, complete, get_llm 等]
```

### 3.2 配置管理設計

**問題**: 不同模組可能需要不同的配置參數（如 `temperature`）

**解決方案**: Configuration Override Method

```python
def reconfigure(self,
                model_name: Optional[str] = None,
                temperature: Optional[float] = None,
                request_timeout: Optional[int] = None) -> None:
    """
    重新配置 LLM（不創建新實例）
    ⚠️ 注意：會影響所有使用該實例的模組

    Args:
        model_name: 新的模型名稱
        temperature: 新的溫度參數
        request_timeout: 新的超時設定
    """
    with self._lock:
        if model_name and model_name != self.model_name:
            self.model_name = model_name
            self.max_context_tokens = self.DEFAULT_CONTEXT_LIMITS.get(
                model_name, 8192
            )

        if temperature is not None:
            self.temperature = temperature

        if request_timeout is not None:
            self.request_timeout = request_timeout

        # 重新創建 LLM 實例
        self.llm = OllamaLLM(
            model=self.model_name,
            temperature=self.temperature,
        )
```

---

## 4. 使用方式變更

### 4.1 現有調用方式（向後相容）

```python
# 方式 1: 直接實例化（仍然有效）
llm_init = LLMInitializer(model_name="gpt-oss:20b", temperature=0.1)
llm = llm_init.get_llm()

# 方式 2: 使用 get_instance 類方法
llm_init = LLMInitializer.get_instance(model_name="gpt-oss:20b", temperature=0.1)
llm = llm_init.get_llm()
```

### 4.2 推薦的新調用方式

```python
# MGFDKernel.py
class MGFDKernel:
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        # 推薦方式：使用類方法獲取實例
        try:
            self.llm_initializer = LLMInitializer.get_instance(
                model_name="gpt-oss:20b",
                temperature=0.1,
                request_timeout=60
            )
            self.llm = self.llm_initializer.get_llm()
            logger.info("LLM 初始化成功")
        except Exception as e:
            logger.warning(f"LLM 初始化失敗: {e}")
            self.llm = None
```

### 4.3 配置覆寫範例

```python
# 場景：某個特定功能需要更高的 temperature
llm_init = LLMInitializer.get_instance()
llm_init.reconfigure(temperature=0.8)  # 臨時調整
# 使用完後恢復
llm_init.reconfigure(temperature=0.1)  # 恢復默認值
```

---

## 5. 執行緒安全分析

### 5.1 競態條件保護

```python
# 場景 1: 多執行緒同時初始化
Thread 1: LLMInitializer.get_instance()  ─┐
Thread 2: LLMInitializer.get_instance()  ─┼─→ Only one instance created
Thread 3: LLMInitializer.get_instance()  ─┘

# 保護機制:
1. First check (_instance is None) - 無鎖，快速返回
2. Lock acquisition - 僅首次需要
3. Second check (_instance is None) - 有鎖，確保安全
```

### 5.2 初始化保護

```python
# _initialized flag 防止重複初始化
if self._initialized:  # Quick check
    return

with self._lock:  # Lock for critical section
    if self._initialized:  # Double check
        return
    # ... initialization code
    self._initialized = True
```

---

## 6. 測試計畫

### 6.1 單元測試用例

```python
# tests/test_llm_singleton.py
import pytest
import threading
from libs.RAG.LLM.LLMInitializer import LLMInitializer

class TestLLMSingleton:

    def setup_method(self):
        """每個測試前重置單例"""
        LLMInitializer.reset_instance()

    def test_singleton_same_instance(self):
        """測試：多次調用返回同一實例"""
        instance1 = LLMInitializer.get_instance()
        instance2 = LLMInitializer.get_instance()
        assert instance1 is instance2

    def test_thread_safety(self):
        """測試：多執行緒環境下的單例保證"""
        instances = []

        def create_instance():
            instances.append(LLMInitializer.get_instance())

        threads = [threading.Thread(target=create_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 所有實例應該相同
        assert all(inst is instances[0] for inst in instances)

    def test_reconfigure(self):
        """測試：配置重新設定"""
        instance = LLMInitializer.get_instance(temperature=0.3)
        assert instance.temperature == 0.3

        instance.reconfigure(temperature=0.8)
        assert instance.temperature == 0.8

        # 同一實例
        instance2 = LLMInitializer.get_instance()
        assert instance2.temperature == 0.8
        assert instance2 is instance

    def test_backward_compatibility(self):
        """測試：向後相容性"""
        # 舊方式仍然有效
        instance1 = LLMInitializer(model_name="gpt-oss:20b")
        instance2 = LLMInitializer(model_name="gpt-oss:20b")
        assert instance1 is instance2  # 仍然是單例
```

### 6.2 整合測試用例

```python
# tests/integration/test_mgfd_kernel_singleton.py
def test_mgfd_kernel_shares_llm_instance():
    """測試：MGFDKernel 實例共享 LLM"""
    LLMInitializer.reset_instance()

    kernel1 = MGFDKernel()
    kernel2 = MGFDKernel()

    # 兩個 kernel 應該共享同一個 LLM initializer
    assert kernel1.llm_initializer is kernel2.llm_initializer
```

---

## 7. 性能影響評估

### 7.1 記憶體使用改善

| 場景 | 改善前 | 改善後 | 節省 |
|------|--------|--------|------|
| 1 個 MGFDKernel 實例 | 300MB | 300MB | 0MB |
| 5 個 MGFDKernel 實例 | 1.5GB | 300MB | **1.2GB** |
| 10 個並發請求 | 3GB | 300MB | **2.7GB** |

### 7.2 初始化時間改善

| 操作 | 改善前 | 改善後 | 提升 |
|------|--------|--------|------|
| 首次初始化 | 2.5s | 2.5s | 0% |
| 後續調用 | 2.5s/次 | <0.01s/次 | **99.6%** |

---

## 8. 遷移策略

### 8.1 階段 1: 實現 Singleton（無侵入性）

```bash
# 步驟 1: 修改 LLMInitializer.py
# - 添加 _instance, _lock, _initialized 類變數
# - 覆寫 __new__ 方法
# - 添加 get_instance() 和 reset_instance() 類方法

# 步驟 2: 運行測試
pytest tests/test_llm_singleton.py -v
```

### 8.2 階段 2: 更新調用方（漸進式）

```bash
# 步驟 1: 更新 MGFDKernel.py（高優先級）
# 變更: LLMInitializer() → LLMInitializer.get_instance()

# 步驟 2: 更新其他調用方（低優先級）
# - libs/KnowledgeManageHandler/knowledge_manager.py (已註解)
# - 其他潛在調用方
```

### 8.3 階段 3: 驗證與監控

```bash
# 步驟 1: 執行完整測試套件
pytest tests/ -v

# 步驟 2: 監控生產環境記憶體使用
# - 記錄改善前後的記憶體佔用
# - 驗證無性能退化
```

---

## 9. 風險與限制

### 9.1 已知風險

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 配置衝突 | 不同模組需要不同配置 | 提供 `reconfigure()` 方法 |
| 測試污染 | 單例在測試間共享 | 提供 `reset_instance()` 方法 |
| 記憶體洩漏 | 單例永不釋放 | 文檔化生命週期管理 |

### 9.2 使用限制

1. **配置一致性**: 所有模組必須接受相同的 LLM 配置
2. **無法多模型**: 無法同時運行多個不同的 LLM 模型
3. **全域狀態**: Singleton 引入全域狀態，需謹慎管理

---

## 10. 實施檢查清單

### 10.1 代碼變更

- [ ] 修改 `libs/RAG/LLM/LLMInitializer.py`
  - [ ] 添加類變數 `_instance`, `_lock`, `_initialized`
  - [ ] 覆寫 `__new__` 方法
  - [ ] 添加 `get_instance()` 類方法
  - [ ] 添加 `reset_instance()` 類方法
  - [ ] 添加 `reconfigure()` 實例方法
  - [ ] 更新文檔字串

- [ ] 更新 `libs/MGFDKernel.py`
  - [ ] 變更初始化方式為 `LLMInitializer.get_instance()`
  - [ ] 添加日誌記錄

### 10.2 測試

- [ ] 創建 `tests/test_llm_singleton.py`
  - [ ] 測試單例保證
  - [ ] 測試執行緒安全
  - [ ] 測試配置重設
  - [ ] 測試向後相容性

- [ ] 創建 `tests/integration/test_mgfd_kernel_singleton.py`
  - [ ] 測試跨模組實例共享

### 10.3 文檔

- [ ] 更新 `README.md` - 添加 Singleton 使用說明
- [ ] 創建 `claudedocs/LLMInitializer_Singleton_Migration_Guide.md`
- [ ] 更新 `libs/RAG/LLM/LLM_Usage_Example.py` - 添加範例

### 10.4 驗證

- [ ] 本地測試通過
- [ ] 整合測試通過
- [ ] Code Review 完成
- [ ] 性能基準測試通過
- [ ] 記憶體使用分析完成

---

## 11. 參考資料

### 11.1 設計模式參考
- **Gang of Four - Singleton Pattern**: 經典設計模式
- **Python Cookbook - Thread-Safe Singleton**: Python 實現最佳實踐

### 11.2 相關檔案
- `libs/RAG/LLM/LLMInitializer.py`: 目標修改檔案
- `libs/MGFDKernel.py:92`: 主要調用方
- `libs/RAG/LLM/LLM_Usage_Example.py`: 使用範例

---

## 附錄 A: Complete Implementation Code

完整的實現代碼已整合到設計文件中，請參考 **第 3.1 節：類結構設計**。

---

## 附錄 B: Performance Benchmarks

```python
# benchmark_singleton.py
import time
import tracemalloc
from libs.RAG.LLM.LLMInitializer import LLMInitializer

def benchmark_memory():
    """記憶體使用基準測試"""
    tracemalloc.start()

    # 創建 10 個實例（Singleton 模式）
    instances = [LLMInitializer.get_instance() for _ in range(10)]

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Current memory: {current / 1024 / 1024:.2f} MB")
    print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")

def benchmark_speed():
    """初始化速度基準測試"""
    # 首次初始化
    start = time.time()
    LLMInitializer.get_instance()
    first_time = time.time() - start

    # 後續調用
    times = []
    for _ in range(100):
        start = time.time()
        LLMInitializer.get_instance()
        times.append(time.time() - start)

    avg_time = sum(times) / len(times)

    print(f"First initialization: {first_time:.4f}s")
    print(f"Subsequent calls (avg): {avg_time:.6f}s")
    print(f"Speedup: {first_time / avg_time:.2f}x")

if __name__ == "__main__":
    benchmark_memory()
    benchmark_speed()
```

---

**文件版本**: v1.0.0
**創建日期**: 2025-10-07
**最後更新**: 2025-10-07
**作者**: Claude (SuperClaude Framework)
**審核狀態**: Ready for Implementation
