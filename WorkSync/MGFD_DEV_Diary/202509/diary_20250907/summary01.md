我會先定位並閱讀 `libs/MGFDKernel.py` 中 `_process_message_internal` 的完整實作，以及 `api/mgfd_routes.py` 的串流處理端點，以準確分析流程與模組呼叫鏈。接著我會彙整出前端到後端五大模組的實際路徑表格。

[2 tools called]

[MODE: RESEARCH]

### 對 `_process_message_internal` 的嚴格分析（可行性／穩定性／容錯／除錯／效能）

- 可行性

  - 目前流程雛形清楚：建 context → 解析輸入（UserInputHandler）→ 決定狀態（StateManager）→ 知識查詢（KnowledgeManager）→ 回應生成（ResponseGenHandler/暫以手動回傳）。
  - 但存在幾處實作風險：
    - 變數生命週期：`slot_metadata` 僅在 `if self.user_input_handler:` 區塊內賦值，若無 handler 或丟例外，後續 `slot_metadata.get(...)` 會 NameError（穩定性不足）。
    - 查詢重複與接口不一致：在 DB 查詢段落，先呼叫 `self.knowledge_manager.search_product_data(message)`，緊接著又呼叫 `self.search_product_data(message)`（Kernel 內無此方法或語義不明），且兩次結果賦值至同一 `_product_data`，容易邏輯混亂（正確性與可維護性風險）。
    - Prompt 重複 format：第 561 與 568 再次 format `self.SysPrompt`，屬重複操作，且若 `_product_data` 未定義或為 None 會潛在錯誤（邏輯穩定性風險）。
    - 回應路由未啟用：真正的 `response_generator.generate` 被註解，當前以手動回傳 `_product_data`，缺少標準化回應格式管線（功能未完成風險）。
- 穩定性／容錯性

  - 缺少 try/except 包裹整體步驟；一旦 `parse_keyword`、DB 查詢、Prompt format、或 dict 鍵訪問出錯，會直接泡到上層（已觀測到 KeyError ifDBSearch 類事件）。
  - 對 slot 與 metadata 預設值建議：
    - 若 `parse_keyword` 返回空，應明確設置 `slot_name = None`、`slot_metadata = {}`；並在後續分支時以 `.get("ifDBSearch", True)` 取值，避免 KeyError／NameError。
  - `_product_data` 的存在性：
    - 若未進行 DB 查詢（例如 `ifDBSearch=False`），後續 Step 5 仍使用 `_product_data`，會 NameError；需在 DB 查詢外預設 `_product_data = {"status":"skipped"}` 或調整控制流。
- 除錯建議（立即可用）

  - 統一每步的結構化日誌：至少包含 `session_id`、`state`、`slot_name`、`ifDBSearch`、`matched_keys`、`result_status`、耗時、錯誤堆疊（`exc_info=True`）。
  - 在關鍵分支後印出上下文摘要（避免大量資料）：`context` 僅列印 keys 和關鍵 metrics。
  - 加入步驟計時器（perf counters）：每步 Start/End log + elapsed ms。
  - 啟用 Request ID／Trace ID 串聯前後端日誌。
- 效能評估（瓶頸與量測）

  - 潛在瓶頸：
    - 向量檢索（Milvus）與嵌入計算（SentenceTransformer.encode）為 CPU／IO 密集。
    - DuckDB 查詢（同步）於 asyncio 事件迴圈，可能阻塞；建議包裝至執行緒池或保持服務不共用 loop（目前仍可接受但需關注）。
  - 建議量測指標：
    - t_total、t_parse、t_state、t_vector_search、t_duckdb、t_prompt、t_generate。
    - 命中率：語義結果數、matched_keys 數量、DB 命中筆數、回傳筆數。
    - 錯誤比率：各步驟異常百分比與 Top-N 錯誤類型。
  - 壓測建議：
    - 以 10/50/100 並發測 on `/chat/stream`，觀測 P95、P99 延遲與 CPU／Mem。
    - 以不同查詢類型（有結果／無結果／大量結果）混合測試。

### 以「請介紹輕便、攜帶方便的筆電」為例的模組與函式路徑表

| 階段                    | 模組                                         | 具體函式/端點                                                                     | 主要工作                                                                                                   | 備註/風險                                             |
| ----------------------- | -------------------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| 前端送出                | 前端 `mgfd_ai.js`                          | sendMessage → fetch `/api/mgfd/chat/stream`                                    | 發送 SSE 請求（JSON: message, session_id, stream=true）                                                    | 需處理 400/503/500 狀態顯示                           |
| 後端路由                | `api/mgfd_routes.py`                       | `@router.post("/chat/stream")` → `chat_stream`                               | 產生 `session_id`、呼叫 `mgfd.process_message(..., stream=True)`，包裝 SSE                             | 失敗時拋 400/500                                      |
| 核心入口                | `libs/MGFDKernel.MGFDKernel`               | `process_message(session_id, message, stream)`                                  | 外層 try/except、呼叫 `_process_message_internal`                                                        | 此函式未展示，但從日誌可見                            |
| 內部流程 Step 1         | `MGFDKernel`                               | `_process_message_internal` 建立 `context`                                    | 建基本欄位、狀態                                                                                           | `previous_answer` 設為型別 `str` 而非值，建議檢視 |
| 內部流程 Step 2         | `UserInputHandler`                         | `user_input_handler.parse_keyword(message)`                                     | 解析意圖/槽位，回傳 `slot_name, slot_metadata`                                                           | 回傳空時要有預設 `{}`                               |
| 內部流程 Step 3         | `StateManageHandler`（邏輯在 Kernel 直判） | `if slot_metadata.get("ifDBSearch", True):` → 設定 `context["state"]`        | 決定是否進行資料查詢                                                                                       | `slot_metadata` 未定義時可能 NameError              |
| 內部流程 Step 4         | `KnowledgeManageHandler`                   | `knowledge_manager.search_product_data(message)`                                | Milvus 語義檢索 → 取得 product_id（對應 `modeltype`）→ DuckDB `spec_data_960` 查詢 → 回傳 JSON 結構 | 此處已修正為以 `modeltype IN (...)` 查詢            |
| 內部流程 Step 4（疑點） | `MGFDKernel`                               | `self.search_product_data(message)`                                             | 目前 Kernel 內無明確該方法定義，疑似錯誤或重複呼叫                                                         | 易造成 AttributeError 或結果覆蓋                      |
| 內部流程 Step 5         | `MGFDKernel`                               | `self.SysPrompt = self.SysPrompt.format(product_data=_product_data, query=...)` | 以資料與查詢生成 System Prompt                                                                             | 執行兩次 format，且 `_product_data` 未定義會錯      |
| 內部流程 Step 6         | `ResponseGenHandler`（暫未啟用）           | （被註解）`response_generator.generate(context)`                                | 產生回應文本或流程訊息                                                                                     | 當前以手動回傳 `_product_data`                      |
| 串流輸出                | `api/mgfd_routes.py`                       | `StreamingResponse(generate_stream())`                                          | SSE start → data(result) → end                                                                           | 回傳結構依 Kernel result                              |

上述路徑符合五大模組接觸面：UserInputHandler（槽位解析）、StateManage（狀態）、KnowledgeManage（檢索/資料）、ResponseGen（回應生成，尚未啟用）、（PromptManagement：在 Kernel 以 `SysPrompt` 內嵌生成，對應到 Prompt 管理職能）。

小結與風險清單（不做修改，只標註）

- 風險點：`slot_metadata` 未保底、`self.search_product_data` 呼叫可疑、`SysPrompt` format 重複、`_product_data` 作用域與預設值。
- 除錯與觀測：加入每步耗時、關鍵欄位與分支路徑日誌；強化錯誤分類與回傳標準格式（目前路由會將非 success 視為 400/500）。
- 效能：Milvus/embedding、DuckDB 同步查詢為主要成本；短期以計時與並發壓測評估；必要時將 DB 查詢 offload 至執行緒池。
