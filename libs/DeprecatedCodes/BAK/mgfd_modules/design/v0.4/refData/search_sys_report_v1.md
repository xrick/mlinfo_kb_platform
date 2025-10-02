# MGFD 系統架構分析報告：服務與搜尋模組

本報告旨在深入分析 `mlinfo_kb_platform` 專案中，位於 `libs/services` 和 `libs/service_manager.py` 的核心服務架構與資料搜尋機制。

## 1. 總體架構 (Overall Architecture)

系統採用了**模組化**與**服務導向**的設計理念。其核心是一個 `ServiceManager`，扮演著服務註冊與調度中心的角色。

- **`ServiceManager` (`libs/service_manager.py`)**:
  - **動態服務發現**: 啟動時，`ServiceManager` 會自動掃描 `libs/services` 目錄下的所有子目錄。
  - **服務載入**: 它會尋找每個子目錄中一個名為 `service.py` 的檔案，並從中載入繼承自 `BaseService` 的類別，將其實例化並註冊到一個服務池中。
  - **統一入口**: 提供 `get_service(service_name)` 方法，讓系統的其他部分可以透過標準化接口獲取並使用特定的服務。

這種設計具有良好的**可擴展性**。未來若要新增功能（例如，一個新的`OrderProcessingService`），開發者只需在 `libs/services` 下建立一個新的子目錄，並遵循 `BaseService` 接口實現即可，無需修改現有核心代碼。

## 2. 模組功能分組 (Module Functional Groups)

`libs/services` 目錄下的程式碼可依據其職責劃分為以下幾個功能模組：

### 2.1. 核心服務介面 (Base Service Interface)

- **`base_service.py`**:
  - 定義了所有服務都必須遵守的抽象基礎類別 `BaseService`。
  - 核心方法 `chat_stream` 強制所有服務都必須以流式生成器（Generator）的方式處理聊天請求，這對於提升使用者體驗至關重要。

### 2.2. 銷售助理服務 (Sales Assistant Service)

這是目前系統最核心、功能最複雜的服務。

- **`service.py`**:
  - **主要服務入口**: 實現了 `SalesAssistantService` 類別，整合了所有銷售相關的功能。
  - **RAG 核心流程**: 包含了完整的檢索增強生成（RAG）流程，從意圖解析、資料庫查詢到最終的 LLM 回應生成。
  - **資料庫整合**: 同時與 `DuckDBQuery`（用於結構化資料的精確查詢）和 `MilvusQuery`（用於非結構化資料的向量/語意搜尋）互動。
  - **多輪對話整合**: 聚合了 `MultichatManager` 和 `FunnelConversationManager`，是複雜對話流程的總指揮。

### 2.3. 智慧對話管理 (Intelligent Conversation Management)

此模組專門處理複雜、模糊的使用者查詢，旨在透過引導式對話將模糊需求轉化為明確指令。

- **`multichat/`**:
  - **`multichat_manager.py` (`MultichatManager`)**:
    - **模糊查詢觸發器**: 透過關鍵字（如 "推薦"、"比較"、"適合"）判斷何時應啟動引導式對話，而不是直接查詢。
    - **場景化問卷**: 能夠根據查詢中的場景關鍵字（如 "遊戲"、"商務"）生成不同優先級的問卷（`ChatChain`）。
    - **需求收集**: 透過一系列預設問題（例如，關於預算、性能、便攜性等），逐步收集使用者的具體偏好。
    - **查詢增強**: 將收集到的偏好轉化為結構化的資料庫篩選條件（`db_filters`），或增強送往 LLM 的查詢字串，大幅提升搜尋精準度。
  - **`funnel_manager.py` (`FunnelConversationManager`)**:
    - **漏斗式分流**: 這是 `MultichatManager` 的前置步驟，專門處理最頂層的模糊查詢。例如，當使用者問「比較筆電」，它會先反問「您想比較**特定系列**的規格，還是想根據**特定用途**獲得推薦？」。
    - **意圖澄清**: 它的核心目標是將一個極度模糊的查詢分流到兩個或多個更清晰的處理流程中（如 `series_comparison_flow` 或 `purpose_recommendation_flow`）。
  - **`gen_chat.py` (`ChatGenerator`)**:
    - **對話鍊生成器**: 負責根據不同策略（隨機、基於優先級）動態生成多輪對話的問題順序（`ChatChain`）。

### 2.4. 語意理解與實體識別 (NLU & Entity Recognition)

- **`entity_recognition.py` (`EntityRecognitionSystem`)**:
  - **規則式實體識別**: 使用正則表達式（RegEx）從使用者查詢中提取結構化資訊，如 `MODEL_NAME` (筆電型號)、`SPEC_TYPE` (規格類型)、`COMPARISON_WORD` (比較詞彙) 等。
  - **意圖偵測**: 透過關鍵字匹配來初步判斷使用者的意圖（如 `comparison`, `specifications`）。
  - 這是系統進行精確查詢的基礎，能快速從自然語言中鎖定關鍵實體。

## 3. 資料搜尋思路與方法深度解析

本系統的搜尋機制是其核心亮點，採用了**混合策略**，結合了多種方法以應對不同類型的使用者查詢。

### 3.1. 雙重搜尋策略 (Dual Search Strategy)

系統並行使用了兩種主要的搜尋方法：

1.  **精確/結構化搜尋 (Precise/Structured Search)**:
    - **實現者**: `DuckDBQuery`，由 `SalesAssistantService` 直接調用。
    - **方法**: 當使用者查詢包含明確的實體（如 `AG958` 型號或 `958` 系列）時，系統會觸發此搜尋。`EntityRecognitionSystem` 首先識別出這些實體，然後系統會構建精確的 SQL 查詢語句（`SELECT * FROM specs WHERE modelname = ?` 或 `... WHERE modeltype = ?`）在 DuckDB 中進行快速、準確的資料檢索。
    - **優點**: 速度快、結果精準、可靠性高。
    - **適用場景**: 使用者知道自己在找什麼，例如查詢特定型號的規格。

2.  **語意/向量搜尋 (Semantic/Vector Search)**:
    - **實現者**: `MilvusQuery`，由 `SalesAssistantService` 調用。
    - **方法**: 系統會將產品規格等文字資料轉換為向量（Embeddings）並儲存在 Milvus 向量資料庫中。當使用者提出較為主觀或模糊的問題時（例如「哪款筆電的散熱比較好？」），系統會將這個問題同樣轉換為向量，並在 Milvus 中搜尋語意上最接近的資料片段。
    - **優點**: 能理解自然語言的深層含義，處理模糊和概念性查詢。
    - **適用場景**: 使用者不確定具體型號，而是根據功能、特性或用途進行查詢。

### 3.2. 智慧分流與引導 (Intelligent Funneling & Guidance)

這是系統處理**模糊查詢**的核心機制，也是最複雜的部分。

1.  **漏斗式對話 (`FunnelConversationManager`)**:
    - **第一道防線**: 當一個查詢既不明確（沒有具體型號）又很模糊（如「幫我找筆電」）時，此模組會被觸發。
    - **澄清意圖**: 它不會立即搜尋，而是先提出一個高層次的分流問題，迫使使用者明確自己的**查詢類型**（是想「比較」還是想「推薦」）。這是避免無效搜尋、提升互動效率的關鍵第一步。

2.  **多輪問卷式對話 (`MultichatManager`)**:
    - **第二道防線**: 在漏斗分流之後，或當查詢意圖是「推薦」時，此模組會接手。
    - **收集需求**: 它會啟動一個預設的「問卷」，透過多個問題（關於用途、預算、性能等）來收集使用者的具體需求。
    - **結構化轉換**: 最關鍵的一步是，它將使用者的回答（如選擇了「遊戲」用途）直接轉化為後端資料庫可以理解的**篩選條件**（`db_filters`），例如 `{"gpu_performance": {"$gte": 8}}`。
    - **從模糊到精確**: 這個過程完美地將一個非常模糊的自然語言查詢（「推薦一台打遊戲的筆電」）轉化成了一個高度精確的結構化資料庫查詢，極大地提升了推薦的相關性。

### 3.3. 核心流程圖 (High-level Flow)

一個典型的模糊查詢處理流程如下：

```
User Query ("推薦一台適合打遊戲的筆電")
      │
      ▼
[FunnelConversationManager] -> 判斷為模糊查詢，但意圖明確（推薦），跳過漏斗問題
      │
      ▼
[MultichatManager] -> 觸發多輪對話
      │
      ▼
System -> 返回一個包含多個問題的「問卷」(關於預算、螢幕大小、儲存等)
      │
      ▼
User -> 提交問卷答案
      │
      ▼
[MultichatManager] -> 將答案轉換為 DB Filters (e.g., {"gpu": "high", "price": "<50000"})
      │
      ▼
[SalesAssistantService] -> 使用 Filters 查詢 DuckDB，獲取候選筆電列表
      │
      ▼
[SalesAssistantService] -> 將候選列表和原始需求送入 LLM 進行最終總結和推薦
      │
      ▼
System -> 返回格式化的最終答案（包含摘要和比較表格）
```

## 4. 總結

該系統的服務與搜尋架構設計精良，展現了現代智慧問答系統的典型特徵：

- **優點**:
  - **混合式搜尋**: 結合了關鍵字精確搜尋和向量語意搜尋的優點，適用範圍廣。
  - **主動式引導**: 透過漏斗和多輪對話，能有效處理模糊查詢，將被動的問答轉化為主動的需求探尋。
  - **高度模組化**: `ServiceManager` 和 `BaseService` 的設計使得系統易於維護和擴展。
  - **關注使用者體驗**: 流式回應（`chat_stream`）和美化的表格輸出都體現了對前端體驗的重視。

- **潛在挑戰**:
  - **複雜度高**: 規則（`EntityRecognition`）、漏斗、多輪對話和 RAG 流程交織在一起，使得除錯和維護具有一定挑戰性。
  - **配置依賴**: 系統的表現高度依賴於各種配置檔案（如 `funnel_questions.json`, `nb_features.json`），配置的準確性至關重要。
