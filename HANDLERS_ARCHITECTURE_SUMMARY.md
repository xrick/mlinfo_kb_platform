# Handler 架構總結

## 概述

在 `libs` 資料夾下建立了四個主要的 Handler 模組，每個模組負責特定的功能領域，提供模組化和可擴展的架構設計。

## 建立的 Handler 模組

### 1. ResponseGenHandler
**位置：** `libs/ResponseGenHandler/`

**功能：** 回應生成處理器
- 負責生成各種類型的回應（文本、JSON、HTML、Markdown）
- 提供錯誤處理和格式化功能
- 支援串流回應和組合回應

**核心組件：**
- `ResponseGenerator` - 回應生成器主類
- 支援多種輸出格式（文本、JSON、HTML、Markdown）
- 提供錯誤回應和成功回應生成
- 支援表格生成和格式化

### 2. KnowledgeManageHandler
**位置：** `libs/KnowledgeManageHandler/`

**功能：** 知識管理處理器
- 管理和處理各種知識庫（SQLite、向量存儲等）
- 提供查詢、搜索、備份功能
- 支援多種知識庫類型的統一管理

**核心組件：**
- `KnowledgeManager` - 知識管理器主類
- 支援 SQLite 知識庫查詢
- 提供語義搜索功能
- 支援知識庫統計和導出
- 提供備份和恢復功能

### 3. PromptManageHandler
**位置：** `libs/PromptManageHandler/`

**功能：** Prompt 管理處理器
- 動態載入和管理各種 Prompt
- 提供緩存機制和組合功能
- 支援按需載入，避免初始化時載入所有 Prompt

**核心組件：**
- `PromptManager` - Prompt 管理器主類
- 全域單例模式
- 智能緩存系統（TTL 機制）
- 支援批量獲取和組合 Prompt
- 提供便捷 API 接口

### 4. StateManageHandler
**位置：** `libs/StateManageHandler/`

**功能：** 狀態管理處理器
- 管理系統狀態和會話狀態
- 提供 Redis 基礎的狀態存儲
- 支援狀態備份和恢復

**核心組件：**
- `StateManager` - 狀態管理器主類
- Redis 基礎的狀態存儲
- 會話狀態管理
- 系統狀態管理
- 狀態備份和恢復

#### 4.1 KernelStatesManage
**位置：** `libs/StateManageHandler/KernelStatesManage/`

**功能：** 核心狀態管理
- 管理系統核心狀態（MGFD、LLM、知識庫等）
- 提供核心狀態的統一管理接口
- 支援系統健康監控

**核心組件：**
- `KernelStateManager` - 核心狀態管理器
- MGFD 系統狀態管理
- LLM 狀態管理
- Prompt 緩存狀態管理
- 知識庫狀態管理
- 用戶會話狀態管理
- 系統健康監控

## 架構特點

### 1. 模組化設計
- 每個 Handler 負責特定的功能領域
- 清晰的職責分離
- 易於維護和擴展

### 2. 統一接口
- 每個 Handler 都提供標準化的接口
- 一致的錯誤處理機制
- 統一的日誌記錄

### 3. 可配置性
- 支援配置文件驅動
- 可自定義參數和行為
- 靈活的初始化選項

### 4. 錯誤處理
- 完善的異常處理機制
- 詳細的錯誤日誌
- 優雅的降級處理

### 5. 性能優化
- 智能緩存機制
- 按需載入
- 資源管理優化

## 使用方式

### 1. 基本導入

```python
# 導入各個 Handler
from libs.ResponseGenHandler import ResponseGenerator
from libs.KnowledgeManageHandler import KnowledgeManager
from libs.PromptManageHandler import get_ai_coder_initialization_prompt
from libs.StateManageHandler import StateManager
from libs.StateManageHandler.KernelStatesManage import KernelStateManager
```

### 2. 初始化使用

```python
# 初始化各個管理器
response_gen = ResponseGenerator()
knowledge_mgr = KnowledgeManager()
state_mgr = StateManager()
kernel_state_mgr = KernelStateManager(state_mgr)
```

### 3. 功能使用

```python
# 生成回應
text_response = response_gen.generate_text_response("Hello World")

# 查詢知識庫
specs = knowledge_mgr.query_sales_specs(model_name="AG958")

# 獲取 Prompt
ai_coder_prompt = get_ai_coder_initialization_prompt()

# 保存狀態
state_mgr.save_session_state("session_123", {"user_id": "user_456"})

# 保存核心狀態
kernel_state_mgr.save_mgfd_system_state({"status": "running"})
```

## 文件結構

```
libs/
├── ResponseGenHandler/
│   ├── __init__.py
│   └── response_generator.py
├── KnowledgeManageHandler/
│   ├── __init__.py
│   └── knowledge_manager.py
├── PromptManageHandler/
│   ├── __init__.py
│   ├── prompt_manager.py
│   └── api.py
└── StateManageHandler/
    ├── __init__.py
    ├── state_manager.py
    └── KernelStatesManage/
        ├── __init__.py
        └── kernel_state_manager.py
```

## 依賴關係

### 1. 基礎依賴
- `redis` - 狀態存儲
- `pandas` - 數據處理
- `sqlite3` - 數據庫操作
- `pathlib` - 路徑處理

### 2. 內部依賴
- `StateManageHandler` 依賴於 Redis 連接
- `KernelStatesManage` 依賴於 `StateManageHandler`
- `KnowledgeManageHandler` 依賴於 SQLite 數據庫

### 3. 外部依賴
- 各個 Handler 可以獨立使用
- 支援可選依賴（如 Redis 不可用時的降級處理）

## 擴展性

### 1. 新增 Handler
- 可以輕鬆添加新的 Handler 模組
- 遵循現有的架構模式
- 提供標準化的接口

### 2. 功能擴展
- 每個 Handler 都可以獨立擴展功能
- 支援插件式架構
- 提供配置驅動的擴展

### 3. 集成能力
- 各個 Handler 可以相互集成
- 支援組合使用
- 提供統一的接口

## 最佳實踐

### 1. 初始化順序
```python
# 1. 初始化基礎管理器
state_mgr = StateManager()

# 2. 初始化依賴管理器
kernel_state_mgr = KernelStateManager(state_mgr)

# 3. 初始化功能管理器
response_gen = ResponseGenerator()
knowledge_mgr = KnowledgeManager()
```

### 2. 錯誤處理
```python
try:
    result = handler.some_function()
    if result is None:
        # 處理空結果
        pass
except Exception as e:
    # 記錄錯誤並進行降級處理
    logger.error(f"操作失敗: {e}")
```

### 3. 資源管理
```python
# 使用上下文管理器或確保資源釋放
with some_handler.get_resource() as resource:
    result = resource.process()
```

這個 Handler 架構提供了模組化、可擴展的設計，讓系統的各個組件可以獨立開發和維護，同時保持良好的集成能力。
