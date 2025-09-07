[MODE: RESEARCH]

我已完整讀取前後端訊息與堆疊，400 的直接原因很明確：在 `MGFDKernel._process_message_internal` 內把一個同步函式用 `await` 呼叫，導致 TypeError。

關鍵錯誤與根因

- 直接根因

  - TypeError: object dict can't be used in 'await' expression
  - 位置：`libs/MGFDKernel.py:556`
  - 內容：`_product_data = await self.knowledge_manager.search_product_data(message)`
  - 說明：`KnowledgeManager.search_product_data` 是同步函式（def），不可用 `await`。正確用法是直接呼叫，或將其改為 async。
- 伴隨問題（同一區塊）

  - 重複/錯誤呼叫：在呼叫 `self.knowledge_manager.search_product_data(message)` 後，又出現一行 `self.search_product_data(message)`。`MGFDKernel` 內並沒有 `search_product_data` 方法，這行會造成 AttributeError 或覆蓋先前結果，是邏輯錯誤。
  - 變數穩定性：
    - `slot_metadata` 只在 `if self.user_input_handler:` 區塊被賦值，若沒有 handler 或發生例外，後續 `slot_metadata.get("ifDBSearch", True)` 會 NameError。
    - `_product_data` 在 `ifDBSearch` 分支外仍被用於 Step 5 的 `SysPrompt.format`，若分支未進（或先前發生錯誤），會 NameError。
  - Prompt 重複 format：`self.SysPrompt = self.SysPrompt.format(...)` 被連續執行兩次（第 561 與 568 附近），屬重複操作，也增加錯誤風險。

建議修正方向（不實作，純分析）

- 修正同步/非同步誤用

  - 把 `_product_data = await self.knowledge_manager.search_product_data(message)` 改為同步呼叫：`_product_data = self.knowledge_manager.search_product_data(message)`。
  - 或把 `KnowledgeManager.search_product_data` 改為 async，且內部所有 DB 呼叫以非阻塞方式處理。但以最小變更為原則，建議改呼叫端。
- 刪除錯誤且重複的呼叫

  - 移除 `self.search_product_data(message)` 這行（Kernel 無此方法）。
- 強化變數保底與分支穩定性

  - 在 Step 2 前先宣告：
    - `slot_metadata = {}` 以避免 NameError。
    - `_product_data = None`（或一個明確預設結構），避免後續未賦值時被使用。
  - 若 `ifDBSearch` 為 False，後續 Prompt format 應使用替代上下文（例如空資料或摘要），不可使用未定義的 `_product_data`。
- 移除重複 format

  - 保留一次 `self.SysPrompt = self.SysPrompt.format(product_data=_product_data, query=context["user_message"])`，避免重複執行。
- 回傳穩定性

  - 保持目前先行的簡化回傳：
    - `{"type": "general", "message": _product_data, "success": True}`
  - 當 `_product_data` 為 None 或 `status` 非 "success" 時，應給予一致的錯誤回傳結構，避免路由以 400 結束（可依您既有規格回傳 `success=False` 與 `error`）。

後續建議的除錯/驗證步驟

- 以「請介紹輕便、容易攜帶的筆電」重測：
  - 預期：不再出現 TypeError；KnowledgeManager 以 `modeltype IN (...)` 查詢 DuckDB，成功回傳 `success` 結構，前端不再 400。
- 加保底日誌：
  - 記錄 `slot_name`、`slot_metadata.get("ifDBSearch", True)`、`matched_keys`、DB 命中筆數、回傳 status。
- 風險提示：
  - `KnowledgeManager.search_product_data` 現為同步，DuckDB 查詢在事件迴圈中同步執行；短期可接受，但長期建議將 DB 查詢移入執行緒池或改為 async 包裝以避免阻塞。

若您同意，我可進入 PLAN/EXECUTE，精確提出與實作以下最小變更：

- 將 await 移除（同步呼叫）
- 移除錯誤的 `self.search_product_data(...)` 行
- 為 `slot_metadata`、`_product_data` 提供安全預設
- 合併重複的 `SysPrompt.format` 呼叫

請回覆「ENTER PLAN MODE」或直接指示我「ENTER EXECUTE MODE」以便立即套用修正。
