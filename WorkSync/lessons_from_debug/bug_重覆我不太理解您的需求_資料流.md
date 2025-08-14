 
  1. 🔄 BUG 資料流傳遞分析

  完整數據流追蹤

  [用戶輸入] "我想買一台筆電..."
      ↓
  [API路由] POST /api/mgfd_cursor/chat
      ↓
  [MGFDSystem.process_message()] 主控制器
      ↓
  [步驟1] UserInputHandler.process_user_input()
      ├─ 調用: enhanced_extractor.extract_slots_with_classification()
      ├─ 傳統關鍵詞匹配: 失敗 → {}
      ├─ LLM智能分類: 無明確槽位 → {}
      └─ 結果: extracted_slots = {} ❌
      ↓
  [步驟2] DialogueManager.route_action()
      ├─ 檢查缺失槽位: usage_purpose, budget_range (必要槽位)
      ├─ 決策: 需要收集信息
      └─ 返回: DialogueAction(action_type="elicit_information", target_slot="usage_purpose")
      ↓
  [步驟3] ActionExecutor.execute_action()
      ├─ 接收: command = {"action": "elicit_information", ...}
      ├─ 查找處理器: action_handlers["elicit_information"] ✅ (修復後)
      ├─ 調用: _handle_elicit_slot()
      └─ 返回: {"action_type": "elicitation", "target_slot": "usage_purpose", ...}
      ↓
  [步驟4] ResponseGenerator.generate_response()
      ├─ 接收: action_type = "elicitation"
      ├─ 調用: _format_funnel_question_response() ✅ (新功能)
      ├─ 生成: 完整的funnel_question JSON結構
      └─ 返回: 結構化的選項界面JSON
      ↓
  [前端接收] 智能格式檢測 ✅ (已修復)
      ├─ 檢測: data.type = "funnel_question"
      ├─ 調用: renderFunnelQuestion()
      └─ 渲染: 互動式選項按鈕界面