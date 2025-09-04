│ 後端JSON回應傳送到前端瀏覽器的程式位置分析                                                           │ │
│ │                                                                                                      │ │
│ │ 通過分析代碼，我已找到後端將JSON描述的結果傳送給前端瀏覽器的關鍵程式位置：                           │ │
│ │                                                                                                      │ │
│ │ 🎯 主要JSON傳送位置                                                                                  │ │
│ │                                                                                                      │ │
│ │ 1. API路由層 - 直接JSON回應                                                                          │ │
│ │                                                                                                      │ │
│ │ 檔案: /api/mgfd_routes.py                                                                            │ │
│ │ - 第55-88行: /chat 端點 - 標準JSON回應                                                               │ │
│ │ - 第80行: return ChatResponse(**result) - 將結果包裝成JSON回應                                       │ │
│ │                                                                                                      │ │
│ │ 2. API路由層 - 串流JSON回應                                                                          │ │
│ │                                                                                                      │ │
│ │ 檔案: /api/mgfd_routes.py                                                                            │ │
│ │ - 第91-139行: /chat/stream 端點 - Server-Sent Events格式                                             │ │
│ │ - 第116行: yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"              │ │
│ │ - 第119行: yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"                               │ │
│ │ - 第122行: yield f"data: {json.dumps({'type': 'end', 'session_id': session_id})}\n\n"                │ │
│ │                                                                                                      │ │
│ │ 3. 核心系統層 - 回應格式化                                                                           │ │
│ │                                                                                                      │ │
│ │ 檔案: /libs/MGFDKernel.py                                                                            │ │
│ │ - 第584-643行: _format_frontend_response() 方法                                                      │ │
│ │ - 第601-643行: 根據不同狀態格式化JSON結構:                                                           │ │
│ │   - funnel_start (第602-607行)                                                                       │ │
│ │   - funnel_question (第608-618行)                                                                    │ │
│ │   - recommendation (第619-627行)                                                                     │ │
│ │   - elicitation (第628-635行)                                                                        │ │
│ │   - general (第637-643行)                                                                            │ │
│ │                                                                                                      │ │
│ │ 4. 回應生成層 - 前端格式適配                                                                         │ │
│ │                                                                                                      │ │
│ │ 檔案: /libs/ResponseGenHandler/ResponseGenHandler.py                                                 │ │
│ │ - 第481-530行: _adapt_frontend_format() 方法                                                         │ │
│ │ - 第492-527行: 適配不同回應類型到前端期望格式                                                        │ │
│ │                                                                                                      │ │
│ │ 5. 主應用程式層 - 全域JSON編碼器                                                                     │ │
│ │                                                                                                      │ │
│ │ 檔案: /main.py                                                                                       │ │
│ │ - 第35-46行: NumpyJSONEncoder 類別 - 處理numpy類型                                                   │ │
│ │ - 第68-75行: CustomJSONResponse 類別 - 自定義JSON回應                                                │ │
│ │ - 第71-75行: json.dumps() 調用，設定 ensure_ascii=False 和自定義編碼器                               │ │
│ │ - 第78行: 設定為應用程式預設回應類別                                                                 │ │
│ │                                                                                                      │ │
│ │ 🔄 JSON傳送流程                                                                                      │ │
│ │                                                                                                      │ │
│ │ 1. 用戶請求 → API路由 (mgfd_routes.py)                                                               │ │
│ │ 2. 業務處理 → MGFDKernel (MGFDKernel.py)                                                             │ │
│ │ 3. 回應生成 → ResponseGenHandler (ResponseGenHandler.py)                                             │ │
│ │ 4. 格式適配 → _format_frontend_response() / _adapt_frontend_format()                                 │ │
│ │ 5. JSON編碼 → CustomJSONResponse (main.py)                                                           │ │
│ │ 6. 傳送到瀏覽器 → HTTP回應/SSE串流                                                                   │ │
│ │                                                                                                      │ │
│ │ 📋 關鍵JSON格式                                                                                      │ │
│ │                                                                                                      │ │
│ │ 一般回應格式:                                                                                        │ │
│ │ {                                                                                                    │ │
│ │   "success": true,                                                                                   │ │
│ │   "type": "general",                                                                                 │ │
│ │   "message": "回應內容",                                                                             │ │
│ │   "session_id": "會話ID",                                                                            │ │
│ │   "timestamp": "時間戳"                                                                              │ │
│ │ }                                                                                                    │ │
│ │                                                                                                      │ │
│ │ 串流回應格式:                                                                                        │ │
│ │ data: {"type": "start", "session_id": "xxx"}                                                         │ │
│ │ data: {"success": true, "type": "general", "message": "內容"}                                        │ │
│ │ data: {"type": "end", "session_id": "xxx"}                                                           │ │
│ │                                                                                                      │ │
│ │ 所有JSON回應都使用 ensure_ascii=False 確保中文字符正確顯示。
