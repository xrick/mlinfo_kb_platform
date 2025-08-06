User approved Claude's plan:
  ⎿ 🎯 Multi-round Funnel Conversation 開發計畫

    📝 核心概念

    當系統遇到模糊查詢時，不直接進入詳細問卷，而是先通過精準的分岔追問來幫助用戶明
    確需求類型，然後進入對應的對話流程。

    🏗️ 系統架構設計

    第一階段：需求類型識別器 (Intent Classifier)

    目標: 將模糊查詢分類為兩大主要類型
    - 類型A: 系列比較查詢 (Series Comparison)
    - 類型B: 特定用途推薦查詢 (Purpose-based Recommendation)

    第二階段：分岔追問機制 (Funnel Questions)

    實現方式: 
    1. 檢測到模糊查詢時，生成2-3個精準的分岔問題
    2. 用戶選擇後，系統進入對應的專業對話流程
    3. 避免用戶面對冗長的通用問卷

    🔧 技術實現計畫

    1. 新增 FunnelConversationManager 類別

    位置: libs/services/sales_assistant/multichat/funnel_manager.py

    主要功能:
    - classify_ambiguous_query(): 模糊查詢分類
    - generate_funnel_questions(): 生成分岔問題
    - process_funnel_choice(): 處理用戶選擇
    - route_to_specialized_flow(): 路由到專業流程

    2. 更新現有觸發邏輯

    修改: MultichatManager.should_activate_multichat()
    - 新增中間層：遇到模糊查詢時先觸發 Funnel 模式
    - 明確查詢直接執行，模糊查詢進入 Funnel

    3. 建立分岔問題模板

    配置文件: funnel_questions.json
    {
      "series_vs_purpose": {
        "question": "為了更好地幫助您，請選擇您的需求類型：",
        "options": [
          {
            "id": "series_comparison",
            "text": "我想比較某個系列（如958系列）內所有機型的規格差異",
            "route": "series_comparison_flow"
          },
          {
            "id": "purpose_recommendation", 
            "text": "我想找到適合特定用途（如遊戲、辦公）的筆電推薦",
            "route": "purpose_recommendation_flow"
          }
        ]
      }
    }

    4. 專業化對話流程

    系列比較流程:
    - Step 1: 確認要比較的系列 (819/839/958)
    - Step 2: 確認比較重點 (規格/性能/價格)
    - Step 3: 直接執行系列內比較

    用途推薦流程:
    - Step 1: 確認使用場景 (遊戲/辦公/學習)
    - Step 2: 重要特性偏好 (3-4個關鍵問題)
    - Step 3: 生成個性化推薦

    5. 前端界面調整

    新增組件: FunnelQuestionCard
    - 顯示分岔問題和選項按鈕
    - 支持快速選擇和路由
    - 美化的卡片式界面設計

    📊 用戶體驗流程

    場景1: 模糊的系列比較

    用戶: "比較958系列哪款筆記型電腦更適合遊戲？"
    ↓
    系統: "請選擇您的需求："
    1. 比較958系列所有機型的遊戲性能規格
    2. 根據遊戲需求推薦最適合的958系列機型
    ↓
    用戶選擇 → 進入對應專業流程

    場景2: 模糊的用途查詢

    用戶: "推薦一台商務筆電"
    ↓
    系統: "請選擇您的需求："
    1. 比較各系列中適合商務的機型差異
    2. 根據商務使用習慣推薦最適合的機型
    ↓
    用戶選擇 → 進入對應專業流程

    🎯 預期效果

    - 減少用戶困惑: 2-3個選擇 vs 10+個詳細問題
    - 提高回答精確度: 專業化流程針對性更強
    - 改善用戶體驗: 快速明確需求，避免疲勞
    - 保持系統靈活性: 仍支持現有的詳細問卷模式

    🚀 開發階段

    1. Phase 1: 實現 FunnelConversationManager 核心邏輯
    2. Phase 2: 整合到現有 service.py 觸發流程
    3. Phase 3: 建立配置文件和問題模板
    4. Phase 4: 前端界面開發和測試
    5. Phase 5: 完整系統測試和優化