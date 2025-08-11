# MGFD 人類可自定義資料整合使用說明

## 概述

本目錄包含 MGFD (Multi-turn Guided Funnel Dialogue) 系統中所有可由人類自定義的配置檔案。這些檔案允許系統管理員和開發者根據具體需求調整系統的對話行為、個性化配置和回應模板。

## 檔案結構

```
libs/mgfd_cursor/humandata/
├── personality_profiles.json      # 個性化配置
├── conversation_styles.json       # 對話風格配置
├── response_templates.json        # 回應模板配置
├── slot_synonyms.json             # 槽位同義詞映射（人類可擴充）
├── error_handling.json            # 錯誤處理配置
├── think_prompts.json             # Think 階段提示詞
├── act_prompts.json               # Act 階段提示詞
└── integration_usages.md          # 本說明文件
```

## 各配置檔案詳細說明

### 1. personality_profiles.json - 個性化配置

**用途**：定義系統的對話個性化類型，包括專業型、友善型、專家型和輕鬆型。

**主要配置項**：
- `personalities`: 定義各種個性化類型
- `default_personality`: 預設個性化類型
- `personality_selection_rules`: 個性化選擇規則

**自定義方法**：
```json
{
  "personalities": {
    "your_custom_personality": {
      "name": "自定義個性化",
      "description": "您的描述",
      "greeting_style": "您的問候語",
      "response_tone": "您的語調",
      "closing_style": "您的結束語",
      "language_features": {
        "formality": "high/medium/low",
        "technical_level": "basic/medium/advanced",
        "detail_level": "simple/concise/comprehensive/detailed"
      }
    }
  }
}
```

**使用場景**：
- 根據用戶群體調整對話風格
- 適應不同的業務場景
- 提供多樣化的用戶體驗

### 2. conversation_styles.json - 對話風格配置

**用途**：定義不同的對話風格，包括正式、輕鬆、技術和簡潔風格。

**主要配置項**：
- `conversation_styles`: 定義各種對話風格
- `style_adaptation_rules`: 風格適應規則
- `style_transition_rules`: 風格轉換規則

**自定義方法**：
```json
{
  "conversation_styles": {
    "your_custom_style": {
      "name": "自定義風格",
      "description": "風格描述",
      "features": ["特徵1", "特徵2"],
      "suitable_for": ["適用場景1", "適用場景2"],
      "language_patterns": {
        "greeting": "問候語",
        "closing": "結束語",
        "politeness": "禮貌用語",
        "formality": "正式程度"
      }
    }
  }
}
```

**使用場景**：
- 根據用戶專業程度調整風格
- 適應不同的對話上下文
- 提供個性化的對話體驗

### 3. response_templates.json - 回應模板配置

**用途**：定義各種對話場景的回應模板，包括問候、槽位詢問、產品推薦等。

**主要配置項**：
- `response_templates`: 各種回應模板
- `template_variables`: 模板變數說明
- `context_adaptations`: 上下文適應規則

**自定義方法**：
```json
{
  "response_templates": {
    "your_custom_category": {
      "templates": [
        "模板1",
        "模板2",
        "模板3"
      ],
      "variables": ["變數1", "變數2"],
      "context_adaptations": {
        "context_key": "適應文本"
      }
    }
  }
}
```
### 4. slot_synonyms.json - 槽位同義詞映射

**用途**：集中管理槽位的口語同義詞，避免硬編碼，讓抽取更貼近人類語言並可持續擴充。

**結構**：每個槽位是一個字典：標準化值 -> 同義詞列表。

```json
{
  "usage_purpose": {
    "business": ["工作", "商務", "辦公"],
    "gaming": ["遊戲", "電競"]
  },
  "budget_range": {
    "budget": ["便宜", "入門"],
    "premium": ["高端", "高級"]
  }
}
```

系統在啟動時自動合併預設詞庫與此檔案，並去重；即使缺檔也能以預設運行。

**使用場景**：
- 調整系統回應的語言風格
- 增加回應的多樣性
- 適應特定的業務需求

### 4. error_handling.json - 錯誤處理配置

**用途**：定義系統錯誤處理策略，包括重試機制、回退策略和錯誤回應。

**主要配置項**：
- `slot_extraction`: 槽位提取錯誤處理
- `llm_failures`: LLM 失敗處理
- `context_limits`: 上下文限制處理
- `recovery_strategies`: 恢復策略

**自定義方法**：
```json
{
  "error_handling": {
    "your_custom_error_type": {
      "max_retries": 3,
      "retry_strategies": ["策略1", "策略2"],
      "fallback_actions": ["回退動作1", "回退動作2"],
      "fallback_responses": ["回應1", "回應2"]
    }
  }
}
```

**使用場景**：
- 調整錯誤處理的嚴格程度
- 自定義錯誤回應內容
- 優化系統的容錯能力

### 5. think_prompts.json - Think 階段提示詞

**用途**：定義 Think 階段的各種提示詞模板，用於分析用戶輸入和決策。

**主要配置項**：
- `think_prompts`: 各種思考提示詞
- `prompt_variables`: 提示詞變數
- `output_formats`: 輸出格式要求

**自定義方法**：
```json
{
  "think_prompts": {
    "your_custom_analysis": {
      "name": "自定義分析",
      "description": "分析描述",
      "template": "您的提示詞模板 {variable}",
      "variables": ["variable1", "variable2"]
    }
  }
}
```

**使用場景**：
- 調整系統的分析邏輯
- 增加新的分析維度
- 優化決策過程

### 6. act_prompts.json - Act 階段提示詞

**用途**：定義 Act 階段的各種提示詞模板，用於生成回應。

**主要配置項**：
- `act_prompts`: 各種行動提示詞
- `prompt_variables`: 提示詞變數
- `output_requirements`: 輸出要求

**自定義方法**：
```json
{
  "act_prompts": {
    "your_custom_action": {
      "name": "自定義行動",
      "description": "行動描述",
      "template": "您的提示詞模板 {variable}",
      "variables": ["variable1", "variable2"]
    }
  }
}
```

**使用場景**：
- 調整回應生成邏輯
- 增加新的回應類型
- 優化回應品質

## 配置變數說明

### 通用變數
- `{user_name}`: 用戶姓名
- `{time_of_day}`: 時間段 (morning/afternoon/evening/night)
- `{personality_type}`: 個性化類型
- `{conversation_style}`: 對話風格
- `{response_tone}`: 回應語調

### 槽位相關變數
- `{usage_purpose}`: 使用目的
- `{budget_range}`: 預算範圍
- `{brand}`: 品牌名稱
- `{target_slot}`: 目標槽位
- `{filled_slots}`: 已填寫槽位

### 產品相關變數
- `{product_name}`: 產品名稱
- `{spec_name}`: 規格名稱
- `{spec_value}`: 規格數值
- `{description}`: 產品描述
- `{price}`: 價格

### 錯誤處理變數
- `{error_type}`: 錯誤類型
- `{error_description}`: 錯誤描述
- `{retry_count}`: 重試次數

## 最佳實踐建議

### 1. 配置管理
- 定期備份配置檔案
- 使用版本控制管理配置變更
- 測試配置變更的影響

### 2. 個性化配置
- 根據目標用戶群體調整個性化類型
- 考慮不同場景的適用性
- 保持配置的一致性

### 3. 錯誤處理
- 設定合理的重試次數
- 提供友好的錯誤回應
- 監控錯誤發生頻率

### 4. 回應模板
- 保持回應的自然性
- 避免重複和單調
- 考慮上下文適應

### 5. 提示詞優化
- 明確指定輸出格式
- 提供足夠的上下文信息
- 定期評估和調整

## 配置驗證

在修改配置檔案後，請確保：

1. **JSON 格式正確**：使用 JSON 驗證工具檢查語法
2. **變數引用正確**：確保所有變數都在系統中定義
3. **邏輯一致性**：檢查配置之間的邏輯關係
4. **功能測試**：在測試環境中驗證配置效果

## 故障排除

### 常見問題
1. **JSON 語法錯誤**：檢查括號、逗號和引號
2. **變數未定義**：確認變數名稱拼寫正確
3. **配置衝突**：檢查不同配置檔案之間的一致性
4. **性能問題**：避免過於複雜的配置邏輯

### 調試方法
1. 檢查系統日誌中的錯誤信息
2. 使用配置驗證工具
3. 逐步測試配置變更
4. 對比正常和異常配置

## 更新日誌

- **2025-08-11**: 初始版本，包含基礎配置檔案
- 後續更新將在此記錄

---

*此文件將持續更新，以反映系統的最新功能和配置選項*
