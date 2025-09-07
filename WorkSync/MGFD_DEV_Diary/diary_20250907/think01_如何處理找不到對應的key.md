[MODE: INNOVATE]

當 input query 找不到對應 key（無法判定槽位/意圖）時，系統應切入「引導式澄清問句」模式，目標是最小步驟地收集決策所需關鍵槽位，並維持使用者的對話流暢度與低負擔。以下是多種可行方向與其折衷，對應五大模組與 `MGFDKernel.py` 的必要變動。

一、核心策略與思路

- 問句生成策略分層
  - 最小化澄清：優先詢問「一個最關鍵槽位」（如用途/預算/尺寸），若答覆後仍不足，再進一步追問。
  - 自適應式澄清：根據當前上下文與缺口，動態調整下一題（避免固定流程造成疲乏）。
  - 選項式對話：以2-4個短選項輔助決策，降低輸入成本（如「主要用途？」→ 文書/遊戲/商務/繪圖）。
- 問句素材來源
  - 預先定義的揀問模板（PromptManagement），按槽位綁定問題集與優先級。
  - 根據近似語意與熱門路徑（KnowledgeManager可提供「常見需求→必問槽位」的啟發式）。
- 決策門檻
  - 當 parse_keyword 的信心值/匹配分數 < 門檻，或無對應 key 時，觸發澄清模式。
  - 保留出口：若使用者表示「不知道/跳過」，採用保守既定預設並持續往下。

二、五大模組與 Kernel 的變動點

1) UserInputHandler（輸入解析/槽位）

- 新增輸出：信心分數、缺失槽位清單、已知槽位摘要。
- 若無 key：回傳 `needed_slots`（按優先級排序）與 `clarify_suggestions`（建議問句主題）。
- 同義詞/正則/語意近似並用，加一層「低信心的候選」供 StateManager 決策是否追問或試探。

2) StateManageHandler（狀態機/對話策略）

- 新增狀態：`OnClarify`（澄清中）、`OnCollectSlot`（收集槽位中）。
- 轉移規則：當 `needed_slots` 非空或信心不足→ 轉 `OnClarify`；槽位補齊 → 轉 `OnDataQuery`；多輪仍不足 → 轉 `OnGenFunnelChat`（提供泛建議/教學式引導）。
- 風險控制：限制最大澄清輪數（如2-3輪），避免糾纏；提供「直接看建議」的捷徑。

3) KnowledgeManageHandler（知識檢索/建議）

- 若無 key：提供「常見需求對應必要槽位」的建議表（如文書→ CPU等級/記憶體/重量/價格）。
- 可回傳「流行選型單」摘要（不進行硬性檢索），作為 ResponseGen 的背景，生成更自然的澄清問句。
- 埋點：記錄使用者在澄清中選擇的選項，回饋改進流程。

4) ResponseGenHandler（回應生成）

- 新增兩類輸出：
  - ClarifyQuestion：精煉單題、提供 2-4 選項；若使用者偏好自由文本亦允許。
  - ClarifySummary：在已收集部分槽位後，回饋「已知條件小結」與「還缺少 X、Y」，降低心智負擔。
- 問句生成規則：
  - 來源模板 + 口吻一致性 + 上下文調整（避免重覆問已回答項）。
  - 根據語言（繁中）輸出，簡短、具體、避免專有名詞干擾。

5) PromptManagementHandler（提示管理）

- 模板化問句與選項：每個槽位對應多個風格模板（簡短版/禮貌版/選項版）。
- 問句選擇策略：按槽位優先級與當前上下文自動挑選最合適模板。
- 版本化與A/B：支持不同問句版本的實驗與回饋迭代。

6) MGFDKernel.py（協調/容錯/遷移）

- 在 `_process_message_internal`：
  - 當 `slot_metadata` 缺失或信心低 → 設 `state=OnClarify`，呼叫 ResponseGen 生成 ClarifyQuestion。
  - 保底變數：確保 `slot_metadata`、`_product_data` 在任何分支都有安全預設。
  - 統一回傳格式：在 ClarifyQuestion 時返回 `{type: "funnel_question", current_question, question_options, ...}`，前端可直接渲染。
- 日誌與除錯：
  - 打點：`phase`, `needed_slots`, `asked_slot`, `user_choice`, `round_index`。
  - 超時與重試：澄清輪次上限、使用者跳過後的預設策略可在 Kernel 層統一處理。

三、不同方案的折衷

- 簡單方案（低變更）
  - 僅在 Kernel 判斷「無 key」時，呼叫 ResponseGen 用固定模板問「主要用途？」。
  - 優點：交付快；缺點：引導粗糙、維護不佳。
- 中等方案（建議）
  - UserInputHandler 回傳 `needed_slots` 與信心值；State 導入 `OnClarify`；ResponseGen 使用模板庫；KnowledgeManager提供常見需求→槽位映射；Kernel 串接。
  - 優點：體驗佳、可擴展；缺點：需多模組協作。
- 進階方案（可選未來）
  - LLM 驅動動態問句生成（以模板為 safety net）、多輪策略學習、A/B 自動優選。
  - 優點：效果最佳；缺點：成本與風險較高。

四、前端配合（簡述）

- 支援 `funnel_question` 類型渲染：單選/多選按鈕；顯示「已知條件」摘要；提供「跳過」「直接看建議」按鈕。
- 上報選項事件：將結構化選擇回傳後端，更新槽位。

五、觀測與評估

- 指標：澄清成功率（進入查詢的比率）、平均澄清輪數、用戶中止率、最終滿意度代理（如跟進點擊）。
- 記錄：問句被選中比例、選項分佈、落地轉換到查詢的比例。

總結

- 關鍵在於：UserInputHandler 回傳「需要的槽位」與信心；State 加入 `OnClarify`；ResponseGen 用模板生成簡潔問句；Kernel 串接與保底；KnowledgeManager提供常識映射輔助。這能在找不到 key 時，平滑切入引導式澄清，維持體驗並快速收斂到可檢索條件。
