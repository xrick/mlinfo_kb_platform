# MGFD Cursor 系統 JSON 檔案分析報告

## 概述

本報告詳細分析了 `libs/mgfd_cursor/humandata/` 目錄中的所有 JSON 配置檔案，以及它們與 MGFD 系統中各個程式模組的關聯關係。這些 JSON 檔案是 MGFD (Multi-Guided Funnel Dialogue) 系統的核心配置，負責定義對話行為、提示詞模板、錯誤處理策略等關鍵功能。

## 系統架構概覽

MGFD 系統採用模組化設計，主要包含以下核心組件：

### 核心程式模組列表

1. **MGFDSystem** (`mgfd_system.py`) - 系統主控制器
   - **用途**: 整合所有模組並提供統一的接口
   - **功能**: 協調整個對話流程，管理系統初始化

2. **ConfigLoader** (`config_loader.py`) - 配置載入器
   - **用途**: 載入和管理所有 JSON 配置檔案
   - **功能**: 提供統一的配置訪問接口，實現配置緩存

3. **LLMManager** (`llm_manager.py`) - LLM 管理器
   - **用途**: 管理大語言模型的調用和提示詞生成
   - **功能**: 處理 Think 和 Act 階段的提示詞組裝

4. **ActionExecutor** (`action_executor.py`) - 動作執行器
   - **用途**: 執行具體的對話動作
   - **功能**: 處理信息收集、產品推薦、澄清等動作

5. **ResponseGenerator** (`response_generator.py`) - 回應生成器
   - **用途**: 生成格式化的回應內容
   - **功能**: 格式化回應並添加前端渲染信息

6. **DialogueManager** (`dialogue_manager.py`) - 對話管理器
   - **用途**: 管理對話狀態和會話流程
   - **功能**: 實現 Think 步驟的邏輯

7. **UserInputHandler** (`user_input_handler.py`) - 用戶輸入處理器
   - **用途**: 處理和解析用戶輸入
   - **功能**: 槽位提取和輸入驗證

8. **RedisStateManager** (`redis_state_manager.py`) - 狀態管理器
   - **用途**: 管理對話狀態的持久化
   - **功能**: 會話狀態的存儲和檢索

9. **KnowledgeBase** (`knowledge_base.py`) - 知識庫
   - **用途**: 管理產品數據和搜索功能
   - **功能**: 產品搜索、過濾和推薦

10. **StateMachine** (`state_machine.py`) - 狀態機
    - **用途**: 管理對話流程和狀態轉換
    - **功能**: 實現 Act 步驟的邏輯

## JSON 檔案詳細分析

### 1. think_prompts.json

#### 檔案內容結構
```json
{
  "think_prompts": {
    "slot_analysis": {
      "name": "槽位分析提示詞",
      "description": "分析用戶輸入，識別和提取相關槽位信息",
      "template": "你是一個專業的筆電購物助手...",
      "variables": ["user_input", "filled_slots", "conversation_history"]
    },
    "action_decision": {
      "name": "行動決策提示詞",
      "description": "基於當前狀態決定下一步行動",
      "template": "你是一個智能對話管理器...",
      "variables": ["conversation_history", "filled_slots", "user_input", "missing_slots"]
    },
    "context_understanding": {
      "name": "上下文理解提示詞",
      "description": "理解對話上下文和用戶意圖",
      "template": "請分析以下對話的上下文和用戶意圖...",
      "variables": ["conversation_history", "user_input", "user_profile"]
    },
    "error_diagnosis": {
      "name": "錯誤診斷提示詞",
      "description": "診斷和分類錯誤類型",
      "template": "請診斷以下對話中可能存在的問題...",
      "variables": ["user_input", "system_response", "error_message", "conversation_context"]
    },
    "personality_selection": {
      "name": "個性化選擇提示詞",
      "description": "根據用戶特徵選擇合適的個性化配置",
      "template": "請根據用戶特徵選擇最合適的對話個性化配置...",
      "variables": ["expertise_level", "conversation_style", "usage_context", "time_constraint", "language_preference"]
    }
  }
}
```

#### 使用程式分析
- **主要使用者**: `LLMManager` (`llm_manager.py`)
- **使用方式**: 
  - 在 `build_think_prompt()` 方法中載入
  - 通過 `_select_think_template()` 方法選擇合適的模板
  - 用於 Think 階段的提示詞生成
- **使用目的**: 
  - 提供結構化的思考提示詞模板
  - 支持不同場景的槽位分析和決策制定
  - 實現動態提示詞選擇和變數替換

#### 程式關聯詳情
```python
# 在 llm_manager.py 中的使用
def build_think_prompt(self, instruction: str, context: Dict[str, Any]) -> str:
    self._ensure_config_loader()
    think_cfg = {}
    if self._config_loader:
        think_cfg = self._config_loader.get_think_prompts() or {}
    
    selected_template = self._select_think_template(instruction, context, think_cfg)
    # ... 組裝提示詞
```

### 2. act_prompts.json

#### 檔案內容結構
```json
{
  "act_prompts": {
    "elicit_slot": {
      "description": "信息收集提示詞",
      "template": "你是一個友善的筆電購物助手。請根據以下信息，生成一個自然、友善的問題來收集用戶的{target_slot}信息..."
    },
    "recommend_products": {
      "description": "產品推薦提示詞",
      "template": "你是一個專業的筆電購物助手。基於用戶的需求，請生成產品推薦回應..."
    },
    "clarify_input": {
      "description": "澄清輸入提示詞",
      "template": "你是一個友善的筆電購物助手。用戶的輸入可能不夠清晰，請生成一個友善的問題來澄清..."
    },
    "handle_interruption": {
      "description": "處理中斷提示詞",
      "template": "你是一個友善的筆電購物助手。用戶似乎想要中斷當前的對話流程，請友善地回應..."
    },
    "confirm_information": {
      "description": "確認信息提示詞",
      "template": "你是一個友善的筆電購物助手。請確認從用戶輸入中提取的信息..."
    }
  }
}
```

#### 使用程式分析
- **主要使用者**: `LLMManager` (`llm_manager.py`) 和 `ActionExecutor` (`action_executor.py`)
- **使用方式**:
  - 在 `build_action_decision_prompt()` 方法中載入
  - 通過 `_select_act_template()` 方法選擇模板
  - 用於 Act 階段的動作執行提示詞
- **使用目的**:
  - 提供不同動作類型的提示詞模板
  - 支持動態提示詞生成
  - 實現個性化的回應風格

#### 程式關聯詳情
```python
# 在 llm_manager.py 中的使用
def build_action_decision_prompt(self, instruction: str, context: Dict[str, Any]) -> str:
    self._ensure_config_loader()
    act_cfg = {}
    if self._config_loader:
        act_cfg = self._config_loader.get_act_prompts() or {}
    
    selected_template = self._select_act_template(instruction, context, act_cfg)
    # ... 組裝提示詞
```

### 3. conversation_styles.json

#### 檔案內容結構
```json
{
  "conversation_styles": {
    "formal": {
      "name": "正式風格",
      "description": "使用敬語和完整句子的正式對話風格",
      "features": ["使用敬語", "完整句子", "專業術語", "禮貌用語"],
      "suitable_for": ["商務客戶", "技術人員", "正式場合", "專業諮詢"],
      "language_patterns": {
        "greeting": ["您好"],
        "closing": ["謝謝您的詢問"],
        "politeness": ["請", "麻煩", "謝謝"],
        "formality": "完整句子結構"
      }
    },
    "casual": {
      "name": "輕鬆風格",
      "description": "口語化表達的輕鬆對話風格",
      "features": ["口語化表達", "簡短句子", "親切稱呼", "表情符號"],
      "suitable_for": ["一般用戶", "年輕族群", "休閒場合", "日常諮詢"],
      "language_patterns": {
        "greeting": ["嗨", "哈囉"],
        "closing": ["掰掰", "下次見"],
        "politeness": ["謝謝", "感恩"],
        "formality": "簡短句子"
      }
    },
    "technical": {
      "name": "技術風格",
      "description": "詳細技術規格和性能分析的專業風格",
      "features": ["詳細規格", "技術參數", "性能分析", "專業術語"],
      "suitable_for": ["IT專業人士", "技術愛好者", "深度諮詢", "技術比較"]
    },
    "simple": {
      "name": "簡潔風格",
      "description": "簡潔明瞭的直觀表達風格",
      "features": ["簡潔表達", "重點突出", "易懂語言", "直接回答"],
      "suitable_for": ["快速諮詢", "時間有限", "簡單需求", "初次接觸"]
    }
  },
  "style_adaptation_rules": {
    "user_expertise_level": {
      "beginner": "casual",
      "intermediate": "formal",
      "expert": "technical",
      "unknown": "simple"
    },
    "conversation_context": {
      "first_contact": "casual",
      "product_comparison": "technical",
      "purchase_decision": "formal",
      "quick_question": "simple"
    }
  }
}
```

#### 使用程式分析
- **主要使用者**: `ConfigLoader` (`config_loader.py`) 和 `ResponseGenerator` (`response_generator.py`)
- **使用方式**:
  - 通過 `load_conversation_styles()` 方法載入
  - 用於動態調整對話風格
  - 根據用戶特徵和對話上下文選擇合適的風格
- **使用目的**:
  - 提供多種對話風格配置
  - 實現個性化的對話體驗
  - 支持動態風格切換

#### 程式關聯詳情
```python
# 在 config_loader.py 中的使用
def load_conversation_styles(self) -> Dict[str, Any]:
    cache_key = "conversation_styles"
    if cache_key in self._cache:
        return self._cache[cache_key]
    
    try:
        file_path = os.path.join(self.config_path, "conversation_styles.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._cache[cache_key] = data
                return data
```

### 4. slot_synonyms.json

#### 檔案內容結構
```json
{
  "usage_purpose": {
    "gaming": ["遊戲", "打遊戲", "電競", "gaming", "玩遊戲", "娛樂", "遊戲機"],
    "business": ["工作", "商務", "辦公", "business", "職場", "上班", "Office", "業務", "工作用", "辦公用途", "商務用途"],
    "student": ["學生", "學習", "上課", "作業", "student", "讀書", "研究", "學業", "學校", "課程"],
    "creative": ["創作", "設計", "剪輯", "creative", "繪圖", "藝術", "製作", "編輯", "創作工作"],
    "general": ["一般", "日常", "上網", "general", "普通", "文書", "基本", "一般用途", "日常使用"]
  },
  "budget_range": {
    "budget": ["便宜", "平價", "入門", "budget", "實惠", "經濟", "低價", "便宜一點", "預算有限"],
    "mid_range": ["中等", "中端", "mid", "中價位", "一般價位", "適中", "中等價位", "合理價格"],
    "premium": ["高端", "高級", "premium", "高價位", "高品質", "高檔", "高級一點"],
    "luxury": ["旗艦", "頂級", "豪華", "luxury", "最高級", "最頂級", "旗艦級", "豪華版"]
  },
  "brand_preference": {
    "asus": ["asus", "華碩", "ASUS"],
    "acer": ["acer", "宏碁", "Acer"],
    "lenovo": ["lenovo", "聯想", "Lenovo"],
    "hp": ["hp", "惠普", "HP", "Hewlett-Packard"],
    "dell": ["dell", "戴爾", "Dell"],
    "apple": ["apple", "蘋果", "mac", "macbook", "Apple", "MacBook"]
  },
  "performance_features": {
    "fast": ["快速", "快", "開機快", "啟動快", "開關機快", "快速開關機", "開機速度", "啟動速度"],
    "portable": ["輕便", "攜帶", "便攜", "輕巧", "攜帶方便", "輕便攜帶", "便於攜帶"],
    "performance": ["效能", "性能", "高效能", "高性能", "強勁", "強大", "效能好"]
  }
}
```

#### 使用程式分析
- **主要使用者**: `ConfigLoader` (`config_loader.py`) 和 `UserInputHandler` (`user_input_handler.py`)
- **使用方式**:
  - 通過 `load_slot_synonyms()` 方法載入
  - 用於槽位提取和同義詞匹配
  - 支持多語言和同義詞識別
- **使用目的**:
  - 提供槽位值的同義詞映射
  - 增強槽位提取的準確性
  - 支持多種表達方式的識別

#### 程式關聯詳情
```python
# 在 config_loader.py 中的使用
def load_slot_synonyms(self) -> Dict[str, List[str]]:
    cache_key = "slot_synonyms"
    if cache_key in self._cache:
        return self._cache[cache_key]
    
    try:
        file_path = os.path.join(self.config_path, "slot_synonyms.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._cache[cache_key] = data
                return data
```

### 5. error_handling.json

#### 檔案內容結構
```json
{
  "error_handling": {
    "error_types": {
      "slot_extraction_failure": {
        "description": "槽位提取失敗",
        "severity": "medium",
        "user_message": "抱歉，我沒有完全理解您的需求。能否請您再說得具體一些？",
        "system_action": "CLARIFY_INPUT"
      },
      "llm_failure": {
        "description": "LLM調用失敗",
        "severity": "high",
        "user_message": "系統暫時無法處理您的請求，請稍後再試。",
        "system_action": "RETRY"
      },
      "validation_error": {
        "description": "輸入驗證失敗",
        "severity": "low",
        "user_message": "請檢查您的輸入格式是否正確。",
        "system_action": "CLARIFY_INPUT"
      },
      "no_products_found": {
        "description": "找不到合適產品",
        "severity": "medium",
        "user_message": "抱歉，目前沒有找到完全符合您需求的產品。讓我們調整一下搜索條件。",
        "system_action": "ELICIT_SLOT"
      },
      "session_expired": {
        "description": "會話過期",
        "severity": "low",
        "user_message": "您的會話已過期，我們重新開始吧。",
        "system_action": "RESET_SESSION"
      },
      "redis_connection_error": {
        "description": "Redis連接錯誤",
        "severity": "high",
        "user_message": "系統暫時無法保存對話狀態，請稍後再試。",
        "system_action": "CONTINUE_WITHOUT_SAVE"
      }
    },
    "messages": {
      "slot_extraction_failure": "抱歉，我沒有完全理解您的需求。能否請您再說得具體一些？",
      "llm_failure": "系統暫時無法處理您的請求，請稍後再試。",
      "validation_error": "請檢查您的輸入格式是否正確。",
      "no_products_found": "抱歉，目前沒有找到完全符合您需求的產品。讓我們調整一下搜索條件。",
      "session_expired": "您的會話已過期，我們重新開始吧。",
      "redis_connection_error": "系統暫時無法保存對話狀態，請稍後再試。",
      "unknown_error": "發生未知錯誤，請稍後再試。",
      "timeout_error": "請求超時，請稍後再試。",
      "network_error": "網絡連接問題，請檢查您的網絡連接。"
    },
    "retry_strategies": {
      "llm_failure": {
        "max_retries": 3,
        "retry_delay": 1,
        "backoff_factor": 2
      },
      "redis_connection_error": {
        "max_retries": 2,
        "retry_delay": 0.5,
        "backoff_factor": 1.5
      }
    },
    "fallback_responses": {
      "default": "抱歉，我遇到了一些問題。讓我們重新開始對話吧。",
      "technical_issue": "系統遇到技術問題，請稍後再試。",
      "maintenance": "系統正在維護中，請稍後再試。"
    }
  },
  "logging": {
    "error_levels": {
      "critical": "系統崩潰或無法恢復的錯誤",
      "error": "影響功能的錯誤",
      "warning": "可能影響功能的警告",
      "info": "一般信息",
      "debug": "調試信息"
    },
    "error_categories": {
      "user_input": "用戶輸入相關錯誤",
      "system_internal": "系統內部錯誤",
      "external_service": "外部服務錯誤",
      "database": "數據庫錯誤",
      "network": "網絡錯誤"
    }
  }
}
```

#### 使用程式分析
- **主要使用者**: `ConfigLoader` (`config_loader.py`) 和所有錯誤處理相關模組
- **使用方式**:
  - 通過 `load_error_handling()` 方法載入
  - 用於統一的錯誤處理和用戶友好的錯誤消息
  - 提供重試策略和降級處理
- **使用目的**:
  - 定義各種錯誤類型和處理策略
  - 提供用戶友好的錯誤消息
  - 實現系統的容錯和恢復機制

#### 程式關聯詳情
```python
# 在 config_loader.py 中的使用
def load_error_handling(self) -> Dict[str, Any]:
    cache_key = "error_handling"
    if cache_key in self._cache:
        return self._cache[cache_key]
    
    try:
        file_path = os.path.join(self.config_path, "error_handling.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._cache[cache_key] = data
                return data

def get_error_message(self, error_type: str) -> str:
    error_config = self.load_error_handling()
    return error_config.get("messages", {}).get(error_type, "發生未知錯誤")
```

### 6. response_templates.json

#### 檔案內容結構
```json
{
  "response_templates": {
    "greeting": {
      "templates": [
        "您好！我是您的筆電購物助手，很高興為您服務。",
        "歡迎來到筆電選購中心！我是您的專屬顧問。",
        "您好，我是專業的筆電顧問，讓我幫您找到最適合的產品。",
        "嗨！我是您的筆電小幫手，有什麼可以協助您的嗎？"
      ],
      "variables": ["user_name", "time_of_day", "previous_interaction", "personality_type"],
      "context_adaptations": {
        "returning_user": "歡迎回來！{user_name}，很高興再次為您服務。",
        "first_time": "您好！我是您的筆電購物助手，讓我為您介紹我們的服務。",
        "morning": "早安！{greeting_template}",
        "evening": "晚安！{greeting_template}"
      }
    },
    "slot_elicitation": {
      "usage_purpose": {
        "templates": [
          "為了幫您找到最適合的筆電，請問您主要會用它來做什麼呢？",
          "了解您的使用需求很重要，您打算用這台筆電進行什麼工作呢？",
          "讓我為您推薦最合適的筆電，首先請告訴我您的使用目的。",
          "請告訴我您主要會用筆電做什麼，這樣我才能給您最好的建議。"
        ],
        "context_adaptations": {
          "has_brand_preference": "考慮到您對{brand}的偏好，",
          "has_budget": "在您的預算範圍內，",
          "is_returning_user": "根據您之前的偏好，",
          "has_previous_purchase": "基於您之前的購買經驗，"
        }
      },
      "budget_range": {
        "templates": [
          "您的預算大概在哪個範圍呢？",
          "為了給您最適合的建議，請告訴我您的預算範圍。",
          "您希望花多少錢購買筆電呢？",
          "請告訴我您的預算，我會為您推薦最划算的選擇。"
        ],
        "context_adaptations": {
          "has_usage_purpose": "考慮到您的{usage_purpose}需求，",
          "has_brand_preference": "針對您喜歡的{brand}品牌，"
        }
      }
    },
    "product_recommendation": {
      "templates": [
        "根據您的需求，我為您推薦以下筆電：",
        "基於您的使用場景，這些產品最適合您：",
        "考慮到您的預算和需求，我建議您看看這些選擇：",
        "以下是我為您精心挑選的筆電："
      ],
      "product_format": {
        "name": "**{product_name}**",
        "specs": "- {spec_name}: {spec_value}",
        "description": "特色：{description}",
        "price": "價格：{price}",
        "recommendation_reason": "推薦理由：{reason}"
      }
    },
    "error_handling": {
      "slot_extraction_failed": {
        "templates": [
          "抱歉，我沒有完全理解您的需求。讓我換個方式詢問：",
          "為了更好地幫助您，請您用不同的方式描述一下：",
          "讓我重新確認一下，您是指：",
          "我可能需要更多資訊，請您詳細說明一下："
        ]
      }
    },
    "confirmation": {
      "slot_extraction_success": {
        "templates": [
          "好的，我了解了。您需要{usage_purpose}用途的筆電，預算在{budget_range}範圍內。",
          "明白了！您的需求是{usage_purpose}，預算{budget_range}。",
          "收到！{usage_purpose}用途，{budget_range}預算，我來為您推薦。"
        ]
      }
    },
    "closing": {
      "templates": [
        "希望我的建議對您有幫助！如有其他問題，歡迎隨時詢問。",
        "感謝您的諮詢！如果還有任何問題，請隨時聯繫我。",
        "很高興能協助您！有其他需要請隨時告訴我。",
        "祝您購物愉快！如需進一步協助，請隨時詢問。"
      ]
    }
  }
}
```

#### 使用程式分析
- **主要使用者**: `ResponseGenerator` (`response_generator.py`) 和 `ActionExecutor` (`action_executor.py`)
- **使用方式**:
  - 通過 `load_response_templates()` 方法載入
  - 用於生成各種類型的回應內容
  - 支持模板變數替換和上下文適應
- **使用目的**:
  - 提供標準化的回應模板
  - 實現個性化的回應生成
  - 支持多種對話場景的回應

#### 程式關聯詳情
```python
# 在 response_generator.py 中的使用
def _format_elicitation_response(self, response_object: Dict[str, Any]) -> Dict[str, Any]:
    content = response_object.get("content", "")
    target_slot = response_object.get("target_slot", "")
    suggestions = response_object.get("suggestions", [])
    
    return {
        "type": "elicitation",
        "content": content,
        "target_slot": target_slot,
        "suggestions": suggestions,
        "timestamp": datetime.now().isoformat(),
        "confidence": response_object.get("confidence", 0.8)
    }
```

### 7. personality_profiles.json

#### 檔案內容結構
```json
{
  "personalities": {
    "professional": {
      "name": "專業型",
      "description": "正式、專業的對話風格",
      "greeting_style": "您好，我是您的筆電購物助手",
      "response_tone": "專業、客觀、詳細",
      "closing_style": "如有其他問題，歡迎隨時詢問",
      "language_features": {
        "formality": "high",
        "technical_level": "medium",
        "detail_level": "comprehensive"
      }
    },
    "friendly": {
      "name": "友善型",
      "description": "親切、輕鬆的對話風格",
      "greeting_style": "嗨！我是你的筆電小幫手",
      "response_tone": "親切、活潑、易懂",
      "closing_style": "還有什麼想了解的嗎？",
      "language_features": {
        "formality": "low",
        "technical_level": "basic",
        "detail_level": "concise"
      }
    },
    "expert": {
      "name": "專家型",
      "description": "技術導向、深度分析的對話風格",
      "greeting_style": "您好，我是筆電技術顧問",
      "response_tone": "專業、技術性、深入",
      "closing_style": "如需更詳細的技術諮詢，請聯繫我們的技術團隊",
      "language_features": {
        "formality": "high",
        "technical_level": "advanced",
        "detail_level": "detailed"
      }
    },
    "casual": {
      "name": "輕鬆型",
      "description": "隨意、自然的對話風格",
      "greeting_style": "哈囉！我是你的筆電夥伴",
      "response_tone": "輕鬆、自然、親近",
      "closing_style": "有其他問題就問我吧！",
      "language_features": {
        "formality": "very_low",
        "technical_level": "basic",
        "detail_level": "simple"
      }
    }
  },
  "default_personality": "professional",
  "personality_selection_rules": {
    "user_expertise": {
      "beginner": "friendly",
      "intermediate": "professional",
      "expert": "expert"
    },
    "conversation_context": {
      "first_contact": "friendly",
      "product_comparison": "expert",
      "purchase_decision": "professional",
      "casual_chat": "casual"
    },
    "user_preference": {
      "formal": "professional",
      "technical": "expert",
      "friendly": "friendly",
      "casual": "casual"
    }
  }
}
```

#### 使用程式分析
- **主要使用者**: `ConfigLoader` (`config_loader.py`) 和 `ResponseGenerator` (`response_generator.py`)
- **使用方式**:
  - 通過 `load_personality_profiles()` 方法載入
  - 用於動態選擇對話個性
  - 根據用戶特徵和對話上下文調整回應風格
- **使用目的**:
  - 提供多種對話個性配置
  - 實現個性化的對話體驗
  - 支持動態個性切換

#### 程式關聯詳情
```python
# 在 config_loader.py 中的使用
def load_personality_profiles(self) -> Dict[str, Any]:
    cache_key = "personality_profiles"
    if cache_key in self._cache:
        return self._cache[cache_key]
    
    try:
        file_path = os.path.join(self.config_path, "personality_profiles.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._cache[cache_key] = data
                return data

def get_personality_profile(self, profile_name: str = "professional") -> Dict[str, Any]:
    profiles = self.load_personality_profiles()
    return profiles.get("profiles", {}).get(profile_name, {})
```

## 程式與 JSON 檔案的關聯總結

### 配置載入流程

1. **系統初始化階段**:
   - `MGFDSystem` 創建 `ConfigLoader` 實例
   - `ConfigLoader` 載入所有 JSON 配置檔案
   - 配置被緩存在記憶體中以提高性能

2. **配置使用階段**:
   - 各個模組通過 `ConfigLoader` 獲取配置
   - 配置用於動態生成提示詞和回應
   - 支持實時配置更新和重新載入

### 關鍵關聯關係

| JSON 檔案 | 主要使用程式 | 使用目的 | 關鍵方法 |
|-----------|-------------|----------|----------|
| think_prompts.json | LLMManager | Think 階段提示詞生成 | build_think_prompt() |
| act_prompts.json | LLMManager, ActionExecutor | Act 階段動作執行 | build_action_decision_prompt() |
| conversation_styles.json | ResponseGenerator | 對話風格調整 | load_conversation_styles() |
| slot_synonyms.json | UserInputHandler | 槽位提取和同義詞匹配 | load_slot_synonyms() |
| error_handling.json | 所有模組 | 統一錯誤處理 | get_error_message() |
| response_templates.json | ResponseGenerator | 回應模板生成 | load_response_templates() |
| personality_profiles.json | ResponseGenerator | 個性化回應 | get_personality_profile() |

### 配置管理特點

1. **緩存機制**: 所有配置都通過 `ConfigLoader` 緩存，避免重複讀取
2. **錯誤處理**: 配置載入失敗時提供默認值，確保系統穩定性
3. **動態更新**: 支持配置的重新載入和更新
4. **類型安全**: 使用 TypedDict 確保配置數據的類型安全
5. **模組化**: 每個 JSON 檔案負責特定的功能領域

## 系統架構優勢

1. **可配置性**: 通過 JSON 檔案實現高度可配置的對話行為
2. **可擴展性**: 新增配置項目只需修改 JSON 檔案，無需修改程式碼
3. **可維護性**: 配置與邏輯分離，便於維護和調試
4. **個性化**: 支持多種對話風格和個性配置
5. **容錯性**: 完善的錯誤處理和降級機制

## 未來改進建議

1. **配置驗證**: 添加 JSON Schema 驗證，確保配置格式正確
2. **配置版本管理**: 實現配置的版本控制和回滾機制
3. **動態配置**: 支持運行時配置更新，無需重啟系統
4. **配置監控**: 添加配置使用情況的監控和統計
5. **多語言支持**: 擴展配置以支持多語言對話

---

*本報告完成於 2024年，詳細記錄了 MGFD 系統中 JSON 配置檔案與程式模組的完整關聯關係。*
