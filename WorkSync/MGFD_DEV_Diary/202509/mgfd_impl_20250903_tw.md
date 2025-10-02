# MGFD 實作狀態報告 - 2025-09-03

## 範圍
- main.py
- api/mgfd_routes.py
- libs/MGFDKernel.py
- libs/KnowledgeManageHandler/**（全部 .py）
- libs/PromptManagementHandler/**（全部 .py）
- libs/ResponseGenHandler/**（全部 .py）
- libs/StateManageHandler/**（全部 .py）
- libs/UserInputHandler/**（全部 .py）

---

## main.py
- FastAPI 應用 v2.0.0，已啟用 CORS；客製 JSONResponse 支援 numpy 型別。
- 已註冊路由：mgfd_routes、specs_routes、history_routes、import_data_routes。
- 根路徑 `/` 以 `index.html` 呈現。
- /health 與 /status 端點提供系統與 MGFD 狀態回報。
- 設置全域例外處理器與兩個中介層（處理時間、請求 ID）。
- 啟動／關閉日誌已設置。

風險／注意事項：
- 部分回應中的時間戳為硬編碼佔位。
- 部分路由（sales）目前被註解停用。

---

## api/mgfd_routes.py
- 初始化 Redis；若連線成功則建立全域 `mgfd_system = MGFDKernel(redis_client)`。
- 依賴注入 `get_mgfd_system` 確保 Kernel 實例存在。
- 端點：
  - POST /api/mgfd/chat → 呼叫 mgfd.process_message(...)
  - POST /api/mgfd/chat/stream → SSE；呼叫 mgfd.process_message(..., stream=True)
  - GET /api/mgfd/session/{session_id} → mgfd.get_session_state
  - POST /api/mgfd/session/{session_id}/reset → mgfd.reset_session
  - GET /api/mgfd/session/{session_id}/history → mgfd.get_chat_history
  - GET /api/mgfd/status → mgfd.get_system_status
  - GET /api/mgfd/health → 回報 Redis + MGFD 健康狀態
  - mgfd_cursor 相關：session/create、stats

風險／注意事項：
- 路由內對 Kernel 的呼叫多為同步方式（缺少 await），而 Kernel 方法為 async，可能造成不一致。

---

## libs/MGFDKernel.py
- 系統核心協調器。負責載入設定與槽位架構。
- 新增系統層屬性 `SysPrompt`（多行政策式提示）。
- 新增三層式提示變數 `product_data`、`prompt_using`、`answer`、`query` 及方法 `generate_three_tier_prompt()`。
- 五大模組以 None 佔位，提供 setter 進行注入：
  - user_input_handler、prompt_manager、knowledge_manager、response_generator、state_manager。
- 核心處理流程（`_process_message_internal`）：
  1) 建立 context
  2) user_input_handler.parse(message, context)
  3) state_manager.process_state(context)
  4) 若需要知識查詢 → knowledge_manager.search(context)
  5) response_generator.generate(context)
  6) state_manager.update_session(session_id, context)
  7) 前端回應格式化

缺口：
- user_input_handler 為必要；其餘模組可選。
- Kernel 期望 `knowledge_manager.search(context)`，但 KnowledgeManager 未提供此統一介面。
- Kernel 期望 `state_manager.get_session`、`update_session`，但 StateManagementHandler 未實作。

---

## libs/KnowledgeManageHandler
檔案：
- knowledge_manager.py：提供 KnowledgeManager（支援 SQLite／語義／Polars），包含多個同步查詢方法（如 query_sales_specs、search_semantic_knowledge_base、query_polars_data），但無統一的 async `search(context)`。
- polars_helper.py：提供 PolarsHelper；含 async connect_data_source/execute_query，並有記憶體與最佳化輔助。
- __init__.py：輸出 KnowledgeManager 與可選的 PolarsHelper。
- examples/polars_usage_example.py：非核心範例（async）。

狀態：
- 已整合 Polars 並採設定驅動；仍缺少對 Kernel 的 `async def search(context)->dict` 薄層介面。

---

## libs/PromptManagementHandler
檔案：
- prompt_manager.py：PromptManager 具快取；以檔案為基礎的 `get_prompt/get_multiple_prompts`。
- api.py、__init__.py：基本輸出。

狀態：
- 介面清晰，但尚未接入 Kernel 流程。

---

## libs/ResponseGenHandler
檔案：
- ResponseGenHandler.py：主類別，提供 `async def generate(context)->dict`（策略工廠多為樣板／待補）。
- ResponseStrategyFactory.py：策略註冊／挑選雛型。
- ResponseStrategy.py：策略基底型別。
- response_generator_deprecated.py、__init__.py。

狀態：
- 對 Kernel 的 `generate(context)` 已到位；策略大多為佔位／未完整。

---

## libs/StateManageHandler
核心：
- StateManagementHandler.py：
  - 主要入口 `async def process_state(context)->dict`。
  - 初始化簡化 DSM：SimplifiedStateMachine、StateFlowController、LinearFlowExecutor；並包含 action_hub FlowExecutor/Validator。
  - 缺少 Kernel 期望的 `get_session(session_id)` 與 `update_session(session_id, context)`。
- StateTransitionsConfig.py：具大量符合動作合約的 async 函式；表驅動配置；並提供 DSM 簡化設定函式。
- simplified_dsm/：線性流程執行器、控制器、狀態列舉、簡化狀態機（8 狀態線性化）。
- action_hub/：流程定義 JSON、驗證器、執行器、除錯器。
- 其他：EventStore／Validator／TransitionPredictor／StateTransition 等基礎設施。

狀態：
- 合約函式已在配置中提供；引擎部件已加入；但會話持久化相關方法仍缺。

---

## libs/UserInputHandler
檔案：
- UserInputHandler.py：`UserInputHandler` 類別具 `async def parse(message, context)->dict`；負責槽位／關鍵字載入、意圖、槽位抽取、控制與驗證。
- ref_impl/user_input_handler_impl_v1_clause.py：參考實作。
- CheckUtils.py：工具函式。

狀態：
- 與 Kernel 對接的 `parse(message, context)` 已到位。

---

## 跨模組一致性檢視
- 標準動作合約（def action(context)->dict）：
  - 在 StateTransitionsConfig.py 中（多為 async 版本）已具備。
  - 其他模組未提供模組層的合約函式轉接；Kernel 目前依賴類方法（`parse`、`generate`、預期的 `search`）。
- v0.4.4「異質函式簽名」：
  - 目前引擎假設動作皆為帶 context 參數；對「零參數且需回傳資料」的動作尚未在執行期支援。

---

## 風險與缺口總結
- FastAPI 路由與 Kernel 的 async/sync 呼叫不一致。
- KnowledgeManager 缺少 Kernel 期望的統一 async `search(context)`。
- StateManagementHandler 缺少 `get_session`／`update_session`（Kernel 依賴）。
- PromptManager 尚未導入 Kernel 流程。
- DSM JSON 流程存在但 Kernel 未啟用呼叫。

---

## 建議（不影響既有邏輯的前提）
- 加入薄層轉接（不改動核心）：
  - KnowledgeManager：新增 `async def search(context)->dict`，內部路由至既有具體查詢方法。
  - StateManagementHandler：新增 `async def get_session(...)`、`async def update_session(...)`，以 Redis/EventStore 支撐。
  - mgfd_routes：對 Kernel 的 async 方法加上 `await`。
- 逐步導入 PromptManager（例如向 ResponseGenHandler 提供模板）。

---

產生時間：2025-09-03
