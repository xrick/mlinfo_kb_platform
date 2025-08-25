<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# please translate the uploaded pdf into markdown file

我無法直接存取或導出你上傳的 PDF 檔為可下載的 Markdown 檔案，但我可以把檔案內容轉寫為結構化的 Markdown 文字供你複製使用。以下是將你提供的 PDF 內容完整轉換為 Markdown 的版本。

# 多輪引導漏斗框架：目標導向對話式 AI 的架構藍圖

## 第一部分：引導漏斗的概念架構

對話式 AI 從簡單的反應式聊天機器人發展為複雜的目標導向代理，這代表了人機交互的典範轉移。對於商業應用，特別是在銷售和客戶服務領域，目標不再僅僅是回答問題，而是主動引導用戶向特定且有價值的結果前進。這需要一個能夠管理結構化多輪對話的架構，以類似傳統銷售漏斗的方式逐步縮小對話範圍。本節為這樣的系統建立理論基礎，將以商業為中心的銷售漏斗概念轉換為強健的對話式 AI 架構。它解構了問題並將其映射到對話系統設計中已建立和新興的模式，為實用且強大的實現奠定基礎。

### 1.1 從銷售漏斗到對話流程：新典範

「對話漏斗」的核心概念是將傳統營銷和銷售漏斗直接轉換到自動化對話領域。¹ 在經典銷售模型中，潛在客戶會經歷不同階段——從初始認知到最終購買和保留。² 對話漏斗旨在在聊天介面的限制內複製這個旅程，將 AI 代理從被動的資訊儲存庫轉變為主動的策略指南。這種方法基於這樣的理解：自動化對話不應該是漫無目的的，而必須與商業目標整合並由其驅動。

典型銷售漏斗的階段為對話流程提供了清晰的藍圖。這些階段包括認知、興趣、評估、參與、行動和保留。² 精心設計的對話代理可以系統性地引導用戶經歷這些階段。例如，初始互動可以透過歡迎用戶並介紹品牌目的來建立認知，就像人類代理會做的那樣。³ 隨著對話的進展，代理可以透過提出針對性問題來發掘用戶需求和痛點，從而引起興趣。在評估階段，代理提供具體資訊，比較選項，並幫助用戶評估產品的適合性。接下來是參與階段，代理可能提供演示或特殊促銷。行動階段是漏斗的高潮，代理直接在聊天視窗內促進購買或註冊過程。最後，購買後的互動可以透過收集回饋或提供支援來促進保留。²

這種漏斗的實施帶來顯著的商業優勢，包括提高潛在客戶轉換率、改善銷售效率和更高的客戶參與度。¹ 透過自動化資格審查和培育過程，銷售團隊可以專注於高價值活動，導致更快的交易完成和大幅的成本節約。¹

這個模型需要對話代理設計理念的根本轉變——從反應式協助轉向主動引導。在許多商業環境中常見的標準 Retrieval-Augmented Generation (RAG) 應用採用「拉取」模型；它們等待用戶查詢並檢索相關答案。用戶完全控制對話方向。然而，「引導對話走向真正需求」的商業要求需要「推送」模型，代理主動將對話導向預定目標。對話漏斗的研究一致強調這種主動性，使用諸如「引導潛在客戶」、「發起互動」和「培育潛在客戶」等動詞。¹ 簡單的輸入 -> LLM -> 輸出循環在架構上對這項任務是不足的。它缺乏維持持續目標、制定逐輪策略和根據用戶反應調整方法的機制。因此，需要更複雜的架構，包含強健的狀態管理和深思熟慮的多步推理過程，以有效執行對話漏斗。

### 1.2 Dialogue Manager：系統的認知核心

任何先進的任務導向對話系統的核心都是 Dialogue Manager (DM)。DM 是負責管理狀態和控制對話流程的中央元件，作為系統的認知核心。⁵ 它協調整個互動，接收語意輸入，與外部知識庫（如產品目錄）介接，追蹤對話進展，並決定系統的下一個行動。⁵ DM 的職責可以分解為兩個主要的相互關聯任務：Dialogue State Tracking (DST) 和 Dialogue Control。

- Dialogue State Tracking (DST)：在任何給定時刻維護對話狀態的結構化表示。⁷ 這個狀態包括用戶意圖、已收集的具體資訊片段（實體或 slots）以及對話歷史。⁷ 實質上，DST 是 DM 的記憶。它允許系統理解當前語境與之前一切的關係，這對生成連貫且相關的回應是必要的。⁷ 對我們的對話漏斗來說，狀態會追蹤用戶處於哪個漏斗階段以及目前為止從他們那裡收集了什麼資訊。
- Dialogue Control：DM 的決策能力。基於當前對話狀態，控制機制決定系統應該採取的下一個行動。⁵ 這可能是提出澄清問題、提供建議、查詢資料庫，甚至將對話升級給人類代理。在引導漏斗中，對話控制政策至關重要；它體現了推動對話前進的商業邏輯。

歷史上，DM 通常實現為嚴格的基於規則的系統，如 Finite-State Machines (FSMs)，對話只能沿著預定義的路徑進行。⁸ 雖然可預測，但這些系統很脆弱，難以處理人類語言的自然變異性。Large Language Models (LLMs) 的出現允許新方法：使用 LLM 本身作為靈活的機率 Dialogue Manager。然而，在單一的整體 prompt 中委託 LLM 所有 DM 功能可能不可靠且不透明，特別是當必須嚴格執行複雜商業邏輯時。⁹ LLM 可能會偏離軌道、忘記關鍵步驟，或「幻想」出偏離預期漏斗的對話路徑。

更強健的架構模式將 DM 的核心功能分離為不同的 LLM 驅動步驟。這是用戶要求的兩層 prompt 系統的基礎。這個「Think, Then Act」循環是 DM 傳統「Track State -> Decide Control -> Generate Response」循環的直接 LLM 原生實現。

1) Dialogue Control（Think 步驟）：第一個 LLM 調用（prompt-lvl1）充當 Dialogue Control 模組。它接收當前對話狀態（歷史、收集的資訊）和最新的用戶輸入。其唯一目的是分析這個語境並決定推動漏斗前進所需的下一個策略行動。輸出不是面向用戶的句子，而是結構化命令（例如，特定指令或 JSON 物件）。這是作為推理引擎運行的 LLM 調用。
2) Natural Language Generation（Act 步驟）：第二個 LLM 調用（prompt-lvl2）充當 Natural Language Generation (NLG) 模組。它接收「Think」步驟決定的策略行動，並將其轉換為優雅的、語境適當的、面向用戶的回應。
3) Dialogue State Tracking（框架的角色）：將使用 LangGraph 等工具實現的總體應用框架負責 DST。它明確地儲存、更新並在轉換間傳遞 DialogueState 物件，確保「Think」步驟始終具有完美的最新對話記憶。

透過這樣構建系統，我們不僅僅是「prompting an LLM」。我們正在架構一個由 LLM 驅動的 Dialogue Manager，它利用模型強大的語言和推理能力，同時施加可靠執行目標導向對話漏斗所需的結構和控制。這種方法以 LLMs 的靈活性取代舊 FSMs 的僵化，而不犧牲商業應用所需的可預測性。

### 1.3 Slot Filling：漏斗進展的引擎

Slot filling 是驅動對話漏斗前進的主要機械過程。它是對話式 AI 中用於從用戶收集特定必需資訊片段以完成任務或意圖的技術。¹⁰ 在引導漏斗的語境中，slots 是代理在能夠成功提出產品建議之前需要收集的基本數據點的預定義佔位符。¹¹ 每個填滿的 slot 代表深入漏斗的一步，將用戶從一般查詢移向特定的可行偏好集。

概念上，slots 可以被視為函數的參數，其中函數是最終商業目標——例如，recommend_coffee(taste_profile, caffeine_level, brew_method)。¹¹ 如果用戶的初始輸入沒有提供所有必要的「參數」，系統必須主動參與未填充 slots 澄清的過程。¹¹ 這是代理「引導」本質最明顯的地方。系統查詢其狀態，識別下一個必需但目前空白的 slot，並生成針對性問題以從用戶那裡引出那個特定資訊片段。¹¹ 這種逐輪資訊收集系統性地縮小可能結果範圍，確保最終建議高度相關且個人化。

設計強健的 slot-filling 系統需要清晰的架構來定義每個要收集的資訊片段。每個 slot 的關鍵參數包括¹¹：

- Name：slot 的唯一識別符（例如，taste_profile）。
- Entity：slot 期望的資訊類型，通常連結到預定義值列表或更複雜的實體識別器（例如，咖啡風味筆記的自定義實體）。
- Required：布林旗標，指示 slot 是否為完成任務的必要項。這個旗標至關重要，因為它決定了對話控制政策。系統必須繼續澄清過程直到所有必需 slots 都被填滿。
- Is Array：指示 slot 是否可以接受多個值的旗標（例如，用戶可能同時喜歡「fruity」和「chocolatey」口味特徵）。

雖然強大，slot filling 並非沒有挑戰。用戶輸入可能含糊不清（例如，「I like strong coffee」可能指咖啡因水平、烘焙程度或風味強度），理解正確含義往往需要深度語境意識。¹² 設計良好的系統必須能夠處理這種歧義，或許透過提出進一步的澄清問題或提供多選選項來消除用戶意圖的歧義。

對於我們的咖啡銷售範例，以下架構提供支撐代理資訊收集過程的決定性數據結構。此表格作為 DialogueState 的單一真實來源，將「推薦咖啡」的抽象目標轉換為將驅動對話的具體數據需求集。

表格：咖啡銷售 Slot 架構

- taste_profile
    - 數據類型：List（例如，"fruity", "chocolatey", "nutty"）
    - 目的：縮小風味偏好範圍（興趣/評估階段）
    - 必需：是
    - 範例澄清問題：為了幫我為您找到完美的咖啡，您能告訴我您通常喜歡什麼樣的風味嗎？例如，您喜歡 fruity、chocolatey，還是更 earthy 的口味？
- caffeine_level
    - 數據類型：String（"regular", "decaf", "half-caff"）
    - 目的：確定用戶的咖啡因需求（評估階段）
    - 必需：是
    - 範例澄清問題：您在尋找一般咖啡，還是比較偏好 decaf？
- brew_method
    - 數據類型：String（例如，"espresso", "drip", "pour-over", "french press"）
    - 目的：將咖啡豆研磨和類型與用戶設備匹配（評估階段）
    - 必需：否
    - 範例澄清問題：您有偏好的沖煮方法嗎，比如 espresso 或 drip coffee maker？這可以幫我縮小選擇範圍。
- budget_per_bag
    - 數據類型：Integer
    - 目的：確保建議在用戶價格範圍內（評估階段）
    - 必需：否
    - 範例澄清問題：您對一袋咖啡有特定的預算考量嗎？
- experience_level
    - 數據類型：String（"beginner", "intermediate", "expert"）
    - 目的：根據推薦咖啡和沖煮建議的複雜性進行調整（個人化）
    - 必需：否
    - 範例澄清問題：為了給出最好的建議，您認為自己是咖啡初學者還是更有經驗的家庭沖煮者？


### 1.4 "Think, Then Act" 循環：透過 Chaining 實現兩步 Prompting

用戶對兩層 prompt 系統的核心要求可以正式化為稱為「Think, Then Act」循環的架構模式。這個模式是 Prompt Chaining 的實際實現，這是一種將複雜任務分解為較小、相互連接的 prompts 序列的技術，其中一個 prompt 的輸出作為下一個的輸入。¹³ 與使用單一的整體 prompt 相比，這種方法顯著改善了 LLM 驅動應用的可靠性、可控性和透明度。¹⁵

「Think, Then Act」循環將每個對話轉換分為兩個不同階段：

1) Think 階段（分析和規劃）：鏈中的第一個 prompt（prompt-lvl1）不是設計來生成面向用戶的文本。其目的是對當前 DialogueState 執行策略分析。它接收對話歷史、當前已填充的 slots 和用戶最新訊息作為輸入。其任務是決定推動漏斗前進所需的下一個邏輯行動。這利用了 Dynamic Prompt Adaptation 的概念，系統分析語境以確定當前輪次的特定目標。¹⁶ 這個「Think」prompt 的輸出是結構化指令——例如，像 {"action":"ELICIT_SLOT","parameter":"taste_profile"} 這樣的 JSON 物件。這步驟純粹用於內部推理。
2) Act 階段（回應生成）：鏈中的第二個 prompt（prompt-lvl2）接收「Think」階段生成的結構化指令作為其主要輸入。其任務是將該指令轉換為自然、引人入勝且面向用戶的回應。例如，如果它接收到引出 taste_profile slot 的指令，它會生成像「我絕對可以幫助您！首先，您通常在咖啡中喜歡什麼樣的風味？」這樣的訊息。這步驟是更標準的專注生成任務。

這個架構是 Conditional Chaining 或 Dynamic Chaining 的一種形式。¹⁷ 流程不是簡單的線性序列。相反，「Think」步驟的輸出動態決定接下來應該執行哪個「Act」prompt 或邏輯。如果「Think」步驟決定行動是 RECOMMEND，將觸發與 ELICIT_SLOT 不同的「Act」prompt 和過程。這創造了靈活但受控的對話流程，可以在每個轉換中適應對話的需求。

這種關注點分離不僅僅是實現細節；它是構建強健的目標導向代理的關鍵設計模式。LLMs 的主要失敗模式是它們傾向於「幻想」或偏離嚴格的基於規則的邏輯，特別是當給予複雜的多部分指令時。⁹ 商業漏斗的核心是一組規則（例如，「如果 taste_profile 缺失，您必須詢問它」）。嘗試使用單一大型 prompt 如「您是咖啡銷售代理。與用戶交談，遵循漏斗邏輯，並引導他們進行銷售」來執行這些規則給 LLM 太多創意自由。它可能忘記提出必需問題，被離題查詢分散注意力，或發明自己的對話路徑，打破漏斗邏輯。

「Think, Then Act」架構透過在每個步驟約束 LLM 任務來減輕這種風險。

- Think prompt 受到嚴重約束。它的指令不是聊天，而是執行分類任務：「基於對話狀態，從這個特定列表中選擇下一個行動：``。以 JSON 物件輸出您的選擇。」強制 LLM 產生像 JSON 這樣的結構化數據大幅減少其輸出空間並最小化對話漂移或創意幻想的機會。這是一種結構化知識融入形式，奠定模型推理的基礎。¹⁸
- Act prompt 接收更簡單、更專注的任務。例如：「系統的計劃是為 taste_profile 進行 ELICIT_SLOT。生成一個友好的問題向用戶詢問這個資訊。」這減少了任何單一生成步驟中模型的認知負載，增加了最終輸出的準確性和可靠性。

最終，這個兩步架構提供了執行漏斗基於狀態的商業邏輯的強大機制。它允許系統利用 LLM 細緻的語言理解進行決策，同時防止模型偏離核心任務，從而增強對話代理的整體控制和可預測性。¹⁴

## 第二部分：使用 Python 和 LangGraph 的實用框架實現

將引導漏斗框架的概念架構轉換為功能性應用需要仔細選擇技術棧和有條理的實現過程。本節提供使用 Python 構建咖啡銷售代理的詳細實用藍圖。它從理論轉向代碼，演示如何構建狀態管理、對話邏輯和動態 prompting 機制，使「Think, Then Act」循環生效。重點是創建完整、可工作的系統，作為第一部分討論原則的具體範例。

### 2.1 技術藍圖：Python、LangChain 和 LangGraph

技術選擇對於有效構建和擴展複雜對話代理至關重要。此實現選擇的技術棧是 Python、LangChain 和 LangGraph，每個都因其在開發 LLM 驅動應用中的特定優勢而被選擇。

- Python：作為 AI 和機器學習開發的事實標準語言，Python 提供豐富的函式庫生態系統、廣泛的社群支援和直接的語法，使其成為我們專案的理想基礎。
- LangChain：這個開源框架為使用 LLMs 構建應用提供了全面的工具和抽象集。¹⁹ 它透過提供用於 prompt 管理、模型互動、記憶和數據檢索的模組化元件來簡化許多常見任務。對於我們的代理，我們將利用幾個關鍵的 LangChain 元件¹⁹：
    - Chat Models：針對對話互動最佳化的各種 LLMs（例如來自 OpenAI、Anthropic、Google）的介面。
    - Prompt Templates：允許透過插入像聊天歷史和用戶輸入這樣的變數來動態構建 prompts 的可重複使用模板。
    - Memory：用於儲存和檢索對話歷史的元件，這對維持語境是必要的。
- LangGraph：雖然 LangChain 很適合構建線性操作序列（chains），引導漏斗框架需要更複雜的控制流程。對話不是直線；它是基於對話狀態的具有條件分支的循環。來自 LangChain 的簡單 ConversationChain 是不足的，因為它無法輕易容納「Think, Then Act」邏輯，其中必須在每個轉換做出決定以確定下一步。這正是 LangGraph 設計要解決的問題。²⁰ LangGraph 是 LangChain 的擴展，允許開發者透過將它們表示為圖形來構建有狀態的多代理應用。其關鍵特性使其成為我們架構的完美工具：
    - Stateful Graphs：LangGraph 允許定義中央狀態物件（我們的 DialogueState），該物件被明確傳遞給圖中的每個節點並由其更新。這提供了 Dialogue State Tracking 的強健機制。
    - Nodes and Edges：應用邏輯構建為由節點（函數或可執行物件）和邊緣（指導節點間流程）組成的圖。這允許我們為「Think」步驟（router）創建節點，為每個「Act」步驟（例如，elicit、recommend）創建單獨的節點。
    - Conditional Edging：LangGraph 允許動態決定控制流程。我們可以創建條件邊緣，根據我們「Think」（router）節點的輸出將對話路由到不同的「Act」節點。這直接實現了我們框架所需的條件和動態 chaining 模式。¹⁷
    - Cycles：它自然支援循環，這對對話是基本的。在「Act」節點生成回應後，流程可以循環回來等待下一個用戶輸入，然後重新進入「Think」節點開始下一輪。

總結來說，LangChain 為與 LLMs 互動提供基本構件，而 LangGraph 提供將這些構件編排為我們引導漏斗代理的複雜、有狀態和循環邏輯所需的關鍵控制流程引擎。

### 2.2 定義 DialogueState 和咖啡架構

在構建對話邏輯之前，必須定義將管理代理記憶和知識的數據結構。這些結構形成系統的骨幹，為追蹤對話和存取產品資訊提供一致格式。

#### DialogueState

DialogueState 是代表代理在對話中任何時點記憶的中央物件。它將在我們的 LangGraph 應用中的節點間傳遞，確保系統的每個部分都能存取完整的對話語境。使用 Python typing 函式庫的 TypedDict 提供類型提示以提升清晰度和開發者體驗。

狀態將包含以下關鍵欄位：

- chat_history：BaseMessage 物件列表（來自 LangChain），儲存對話的逐輪歷史。這對向 LLM 提供語境至關重要。
- filled_slots：儲存從用戶收集資訊的字典。此字典的鍵將對應我們咖啡銷售 Slot 架構中的 Slot 名稱（例如，'taste_profile'），值將是用戶提供的資訊。
- recommendations：包含代理生成產品建議的字串列表，以避免重複建議。

Python 實現（片段）：

- from typing import TypedDict, List, Dict, Any
- from langchain_core.messages import BaseMessage
- class DialogueState(TypedDict):
    - chat_history: List
    - filled_slots: Dict[str, Any]
    - recommendations: List[str]


#### 咖啡產品架構和知識庫

代理做出相關建議的能力取決於其產品的結構化知識庫。假設咖啡數據儲存在 coffee_products.csv 的 CSV 檔案中。此檔案應包含產品名稱、描述、口味筆記、咖啡因水平、適合的沖煮方法、價格等欄位。

在應用啟動時載入這些數據。可用 Pandas 將 CSV 載入為字典列表，以便於篩選。

- import pandas as pd
- def load_coffee_knowledge_base(filepath: str = "coffee_products.csv") -> List:
    - 嘗試讀取 CSV 並轉換為 records 清單
    - FileNotFound 時回報錯誤
- coffee_knowledge_base = load_coffee_knowledge_base()

這個結構化的 DialogueState 和 coffee_knowledge_base 為構建代理邏輯提供必要基礎。狀態物件將在對話過程中更新，知識庫將在做建議時被查詢。

### 2.3 使用 LangGraph 構建狀態機

本節詳述使用 LangGraph 構建對話代理核心邏輯。代理被建模為狀態圖，其中節點代表處理步驟（「Think」和「Act」），邊緣指導對話流程。

#### 圖和狀態初始化

- from langgraph.graph import StateGraph, END
- workflow = StateGraph(DialogueState)


#### Router 節點（Think 步驟）

router 是圖中最關鍵的節點，體現「Think」部分。它的工作是分析當前 DialogueState 並決定接下來應該執行哪個「Act」節點。初版可用程式化邏輯，進階版可用 LLM。

範例程式化 route_action：

- required_slots = ["taste_profile", "caffeine_level"]
- 若缺少必需 slots -> "elicit_information_node"
- 否則 -> "recommend_product_node"


#### 功能節點（Act 步驟）

每個節點接收 DialogueState，執行行動（通常涉及 LLM），並回傳狀態更新。

- elicit_information_node：當缺少必需 slot 時觸發，為第一個缺失 slot 生成澄清問題，並把生成的 AI 訊息加入 chat_history。
- recommend_product_node：當所有必需 slots 已填滿時觸發，篩選目錄，生成有說服力的建議，更新 chat_history 與 recommendations。
- handle_user_input_node：從最新用戶訊息抽取 slot 值並更新 filled_slots。


#### 使用條件邊緣組裝圖

- 新增節點：handle_user_input_node、elicit_information_node、recommend_product_node
- 設定入口點為 handle_user_input_node
- add_conditional_edges 從 handle_user_input_node 經 route_action 路由到 elicit_information_node 或 recommend_product_node
- elicit/recommend 完成後連到 END，等待下一輪輸入
- app = workflow.compile()


### 2.4 實現動態 Prompt 模板

「Think, Then Act」循環的有效性依賴於每個階段使用的 prompt 模板的品質與動態性。模板會以 DialogueState 的資訊動態填充，實現 Dynamic Prompt Adaptation。¹⁶

#### Router Prompt（Think 步驟，基於 LLM 的版本）

- 接收 filled_slots 與 user_input
- 嚴格限制輸出為有效 action 名稱（可用結構化輸出/tool calling）

範例元素：

- ChatPromptTemplate：系統訊息列出已填 slot 與必需 slots，要求選擇下一行動
- 使用 pydantic 模型 Route(action=...) 強制結構化輸出


#### 引導 Prompt（Act 步驟）

- elicit_information_node 的 prompt 接收 slot_to_elicit 與 slot_schema 對應的 example_question，生成自然提問
- 將 chat_history 提供作為語境，讓語氣一致、上下文連貫

這個兩步 prompting 機制確保策略理性與自然表達的結合。

## 第三部分：進階考量和生產準備

將對話代理從原型推向生產，需要處理真實世界的複雜性：用戶不可預測、系統會失敗、需求會演變。本部分聚焦錯誤處理、RAG 提升品質，以及長期記憶實作。

### 3.1 優雅錯誤處理和對話修復

高品質對話設計的核心原則是系統必須為出錯做好準備。²²

- 對話修復（repair）：當 slot 抽取失敗時，避免重複同樣提問，改用：
    - 重新表述：換句話說明目標與選項。
    - 提供選項：從開放式改為多選（如 1/2/3），降低使用者負擔。²²
- 處理中斷：支援用戶改變主意或跳出流程。基於 LLM 的 router 較能辨識中斷語意，並導向 handle_off_topic_node 再嘗試回引漏斗。
- 升級人類代理：設定觸發條件（連續多次失敗、強烈負面情緒），禮貌提供人工支援移交。²³


### 3.2 使用 Retrieval-Augmented Generation (RAG) 增強建議

將 recommend_product_node 從簡單篩選升級為 RAG 流程：

1) 語意查詢構建：將 filled_slots 合成語意豐富的查詢（如「適合初學者的輕體、酸味、果香咖啡」）。
2) 向量檢索：將產品描述/評論/筆記/指南編入向量庫（FAISS、Chroma），以語意相似度檢索 top-k 文件。¹⁹
3) 增強生成：把檢索文檔與偏好一起注入 prompt，要求引用具體細節並給出匹配理由。

優勢：

- 降低幻想風險。¹⁵
- 建議更豐富、具體、有說服力。
- 可擴展性佳：新增產品只需更新向量庫。


### 3.3 為長期記憶和個人化持久化狀態

LLMs 無狀態，但我們的架構可持有狀態。為達成跨會話個人化，可在對話結束時將 DialogueState 儲存至外部資料庫（如 Redis/SQL），以用戶 ID 作鍵。回訪時載入，解鎖：

- 個人化問候（歡迎回來，稱名）。
- 語境連續（引用上次購買或偏好）。
- 主動建議（根據歷史偏好跳過部分漏斗）。
- 建立信任與忠誠。¹

LangGraph Platform 等提供狀態持久化與檢查點能力，簡化部署。²⁰

## 結論

多輪引導漏斗框架代表商業對話式 AI 的重大架構演進。透過超越反應式問答，該模型使得主動引導用戶達成商業目標的代理成為可能。核心在於以 prompt chaining 實現的「Think, Then Act」循環：先分析狀態決策，再生成用戶回應。這兼顧複雜商業邏輯的可執行性與 LLM 的語言能力。

使用 Python、LangChain 與 LangGraph 的實作證明其可行。特別是 LangGraph，適合管理有狀態、循環、條件分支的目標導向對話。透過明確的 DialogueState、router 控制流程與動態 prompts，開發者可按此藍圖構建系統。

同時，納入錯誤處理、RAG 增強與狀態持久化，標誌從原型到生產的關鍵步驟。最終，代理不僅是銷售工具，更是智能、可靠、引人入勝的品牌代表。該框架提供將 LLM 力量與企業目標結合的結構化方法，為更有效且精緻的對話體驗鋪路。

<div style="text-align: center">⁂</div>

[^1]: ZH_Main_Guided-Funnel-Dialogue-Framework.pdf

