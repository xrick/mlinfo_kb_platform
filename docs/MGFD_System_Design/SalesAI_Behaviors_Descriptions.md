###業務AI系統行為描述

1. 請**務必了解及完全遵守**一個客戶跟系統進行互動時最基本原因：
   1.1.收集客戶的需求，也就是我們所稱的槽位值，然後依照這些槽位值在我們自己的產品(內部)資料進行搜尋，並把較為符合客戶需求的產品推薦(各個槽位值比較接近客戶的需求)給客戶。
   我用一個簡單的flow圖來圖式化這個過程：
   round-1
   user-input -> sales-ai -> [user-input+prompt] -> LLM -> response to user for collecting user requirements -> user give one requirement value which is the actually slot value our system need.
   [check whether have collected enough data for search product]
   a. yes, perform internal data search for customer.
   b. no, create new question to ask user for another requirements values
   sales-ai -> [llm-generated-prompt according to next customer requirement] -> LLM -> generate question to user for collecting another requirement -> user give one requirement value which is the actually slot value our system need.
   [check whether have collected enough data for search product]
   ..........
   we can see it is necessary for system to have multi-turn chats with customer for the requirements(slots) values collections.
   1.2.以目前我們應用的筆電銷售領域，我們要預設一些基本的槽位:

   * 用途
   * CPU等級
   * GPU等級
   * 是否好攜帶、重量
   * 價格區間
   * 螢幕尺寸
   * 品牌

   這些資料目前在libs/mgfd_cursor/humandata/slot_synonyms.json已有一些記錄，請AI將上述我提到的幾項，如果沒有，請補齊，並進行分析目前的slot_synonyms.json的架構對於槽位的取得是否有需要增強的地方，例如加入regular expression，取代語義類似的比對，效能可能更好，請進行思考。
2. 請重新分析目前整個實作在libs/mgfd_cursor中的架構，以主要模組為中心來描述資料流，從使用者輸入資料，到系統產生回應給使用者，其中所有一切詳盡的、完整的，並且用簡單的例子、比喻式寫法來描述資料流在系統中被處理的過程、最後回應如何產生的過程，請把分析寫入到WorkSync/mgfd_sys_reports/mgfd_sys_report_202508161102.md
