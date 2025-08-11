# SalesRAG系統完整分析文檔

## 目錄
1. [系統概述與隱喻](#系統概述與隱喻)
2. [完整數據流程分析](#完整數據流程分析)
3. [函數數據轉換詳細分析](#函數數據轉換詳細分析)
4. [關鍵資源文件分析](#關鍵資源文件分析)
5. [核心組件運作原理](#核心組件運作原理)
6. [技術架構與依賴關係](#技術架構與依賴關係)

---

## 系統概述與隱喻

### 🏢 系統整體隱喻：智能筆電推薦的中央指揮中心

想像這個SalesRAG系統就像一個高科技的筆電推薦中心，由以下幾個部門組成：

- **🏪 接待大廳 (Frontend)**：用戶與系統的第一接觸點
- **📞 調度中心 (API Layer)**：負責接收請求並分發到合適部門
- **👥 專家顧問團 (Service Layer)**：具備專業知識的AI顧問
- **📚 知識庫房 (Database Layer)**：存儲所有筆電規格和歷史資料
- **🧠 智能大腦 (LLM)**：能夠理解和生成自然語言的AI引擎

### 系統核心功能
1. **智能對話諮詢**：透過自然語言與用戶互動
2. **多輪需求收集**：系統性地了解用戶需求
3. **規格比較分析**：提供詳細的筆電規格對比
4. **個性化推薦**：根據用戶偏好提供量身定制建議

---

## 完整數據流程分析

### 🔄 從用戶輸入到瀏覽器輸出的完整旅程

#### 第一階段：用戶界面交互 (Frontend)
```
用戶輸入查詢 → templates/index.html → static/js/sales_ai.js
```

**數據格式轉換：**
- **輸入**：用戶原始文字（如："我想要一台適合遊戲的筆電"）
- **處理**：JavaScript事件處理和表單驗證
- **輸出**：JSON格式的HTTP請求

```javascript
// 實際數據範例
{
  "query": "我想要一台適合遊戲的筆電",
  "service_name": "sales_assistant"
}
```

#### 第二階段：API路由處理 (Backend Entry)
```
HTTP Request → main.py → api/sales_routes.py
```

**關鍵路由端點：**
- `/api/sales/chat-stream`：即時對話流
- `/api/sales/multichat`：多輪對話處理
- `/api/sales/multichat-all`：一次性問卷提交

**數據處理流程：**
```
sales_routes.py:chat_stream() → ServiceManager → SalesAssistantService
```

#### 第三階段：服務協調層 (Service Management)
```
ServiceManager → libs/service_manager.py → SalesAssistantService
```

**隱喻說明**：ServiceManager就像是一個智能的客服主管，能夠：
- 識別用戶查詢的類型
- 分配給最合適的專家顾问
- 協調不同服務之間的合作

#### 第四階段：核心業務邏輯處理 (Core Service)
```
SalesAssistantService → libs/services/sales_assistant/service.py
```

**數據處理步驟：**

1. **實體識別階段**
   ```python
   # 輸入：原始查詢
   query = "我想要一台適合遊戲的筆電"
   
   # entity_recognition.py 處理
   entities = {
     "PERFORMANCE_WORD": ["遊戲"],
     "SPEC_TYPE": ["筆電"],
     "USAGE_INTENT": "gaming"
   }
   ```

2. **多輪對話判定階段**
   ```python
   # 檢查是否觸發多輪對話
   if is_vague_query(query):
       return multichat_start_response()
   ```

3. **數據檢索階段**
   ```python
   # 並行查詢兩個數據庫
   duckdb_results = duckdb_query.query(sql)  # 結構化數據
   milvus_results = milvus_query.search(vector)  # 向量相似度搜索
   ```

#### 第五階段：數據庫查詢層 (Database Layer)

**DuckDB查詢流程：**
```
SQL Query → libs/RAG/DB/DuckDBQuery.py → db/sales_specs.db
```

**數據轉換範例：**
```python
# 輸入SQL
sql = "SELECT * FROM specs WHERE gpu LIKE '%RTX%' ORDER BY modelname"

# 數據庫返回（元組列表）
results = [
    ('AG958', 'RTX 3060', '16GB', '512GB SSD', ...),
    ('APX958', 'RTX 3070', '32GB', '1TB SSD', ...)
]

# 轉換為結構化數據
structured_data = [
    {
        'modelname': 'AG958',
        'gpu': 'RTX 3060',
        'memory': '16GB',
        'storage': '512GB SSD'
    },
    # ...
]
```

**Milvus向量查詢流程：**
```
Query Vector → libs/RAG/DB/MilvusQuery.py → Milvus Collection
```

#### 第六階段：LLM推理處理 (AI Processing)
```
Structured Data → libs/RAG/LLM/LLMInitializer.py → Ollama (DeepSeek-R1)
```

**數據轉換過程：**
```python
# 輸入：結構化數據 + 用戶查詢
prompt_data = {
    "user_query": "我想要一台適合遊戲的筆電",
    "retrieved_data": structured_data,
    "context": "gaming laptop recommendation"
}

# LLM處理
llm_response = {
    "type": "multichat_start",
    "message": "我將通過幾個問題來了解您的遊戲需求...",
    "session_id": "uuid-string"
}
```

#### 第七階段：回應流式傳輸 (Response Streaming)
```
LLM Response → Server-Sent Events → Frontend JavaScript
```

**SSE數據格式：**
```
data: {"type": "multichat_start", "message": "...", "session_id": "..."}

data: {"type": "multichat_question", "question": "...", "options": [...]}

data: {"type": "multichat_complete", "recommendations": "..."}
```

#### 第八階段：前端渲染 (Frontend Rendering)

**JavaScript處理流程：**
```javascript
// static/js/sales_ai.js 中的處理
async function sendMessage() {
    // 接收SSE流
    const reader = response.body.getReader();
    
    // 解析JSON數據
    const jsonData = JSON.parse(dataString);
    
    // 根據類型渲染
    renderMessageContent(container, jsonData);
}
```

**渲染數據轉換：**
```javascript
// 輸入：LLM返回的表格數據
const tableData = [
    {feature: "CPU", AG958: "Intel i7-12700H", APX958: "AMD Ryzen 7 6800H"},
    {feature: "GPU", AG958: "RTX 3060", APX958: "RTX 3070"}
];

// 轉換為Markdown表格
const markdown = `
| 規格項目 | AG958 | APX958 |
|----------|-------|--------|
| CPU | Intel i7-12700H | AMD Ryzen 7 6800H |
| GPU | RTX 3060 | RTX 3070 |
`;

// 最終HTML輸出
const html = parseMarkdownTable(markdown);
```

---

## 函數數據轉換詳細分析

### 🔍 實體識別函數 (Entity Recognition)

**位置：** `libs/services/sales_assistant/entity_recognition.py`

**輸入數據格式：**
```python
query = "我想比較AG958和APX958的差異"
```

**處理過程：**
```python
def extract_entities(query):
    # 使用entity_patterns.json中的正則表達式
    patterns = {
        "MODEL_NAME": r"[A-Z]{2,3}\d{3}(?:-[A-Z]+)?",
        "COMPARISON_WORD": r"\b(比較|compare|差異|vs)\b"
    }
    
    # 匹配結果
    entities = {
        "MODEL_NAME": ["AG958", "APX958"],
        "COMPARISON_WORD": ["比較", "差異"],
        "intent": "comparison"
    }
    return entities
```

**輸出數據格式：**
```python
{
    "MODEL_NAME": ["AG958", "APX958"],
    "COMPARISON_WORD": ["比較", "差異"],
    "SPEC_TYPE": [],
    "intent": "comparison",
    "confidence": 0.95
}
```

**隱喻說明：** 這個函數就像是一位經驗豐富的「文字偵探」，能夠從用戶的話語中找出關鍵線索，識別出型號名稱、規格類型、比較意圖等重要信息。

### 🗄️ 數據庫查詢函數 (Database Query)

**位置：** `libs/RAG/DB/DuckDBQuery.py`

**輸入數據：**
```python
sql_query = """
SELECT modelname, cpu, gpu, memory, storage 
FROM specs 
WHERE modelname IN ('AG958', 'APX958')
ORDER BY modelname
"""
```

**內部處理：**
```python
def query(self, sql_query: str):
    try:
        # DuckDB連接和查詢
        connection = duckdb.connect(self.db_file, read_only=True)
        results = connection.execute(sql_query).fetchall()
        return results
    except Exception as e:
        logging.error(f"查詢失敗: {e}")
        return None
```

**輸出數據：**
```python
[
    ('AG958', 'Intel i7-12700H', 'RTX 3060', '16GB DDR5', '512GB SSD'),
    ('APX958', 'AMD Ryzen 7 6800H', 'RTX 3070', '32GB DDR5', '1TB SSD')
]
```

**隱喻說明：** DuckDB就像是一個高效的「資料檔案管理員」，能夠快速從龐大的規格檔案櫃中精確找出所需的筆電規格資料。

### 🤖 LLM推理函數 (LLM Processing)

**位置：** `libs/RAG/LLM/LLMInitializer.py`

**輸入數據準備：**
```python
prompt = f"""
用戶查詢：{user_query}
檢索到的數據：{retrieved_data}
請生成結構化的比較分析。
"""
```

**LLM處理過程：**
```python
def invoke(self, prompt: str) -> str:
    try:
        # 調用Ollama DeepSeek-R1模型
        response = self.llm.invoke(prompt)
        return response
    except Exception as e:
        raise ConnectionError("LLM服務不可用") from e
```

**輸出數據結構：**
```python
{
    "type": "comparison_response",
    "answer_summary": "兩款筆電的主要差異在於處理器和顯卡配置...",
    "comparison_table": [
        {"feature": "CPU", "AG958": "Intel i7-12700H", "APX958": "AMD Ryzen 7 6800H"},
        {"feature": "GPU", "AG958": "RTX 3060", "APX958": "RTX 3070"},
        {"feature": "Memory", "AG958": "16GB DDR5", "APX958": "32GB DDR5"}
    ],
    "conclusion": "APX958在圖形處理和記憶體容量方面更優秀..."
}
```

**隱喻說明：** LLM就像是一位「AI專家顧問」，能夠閱讀和理解大量技術資料，然後用通俗易懂的語言為客戶提供專業的分析和建議。

### 📊 多輪對話管理函數 (Multichat Management)

**位置：** `libs/services/sales_assistant/multichat/multichat_manager.py`

**輸入：** 用戶的模糊查詢
```python
query = "我想要一台適合我的筆電"
```

**處理流程：**
```python
def process_multichat_query(query):
    # 1. 檢測是否為模糊查詢
    if is_vague_query(query):
        # 2. 初始化多輪對話會話
        session_id = generate_session_id()
        
        # 3. 載入問題模板
        questions = load_questions_from_config()
        
        # 4. 返回第一個問題
        return {
            "type": "multichat_start",
            "session_id": session_id,
            "message": "我將通過幾個問題來了解您的需求"
        }
```

**nb_features.json數據結構使用：**
```python
# 從配置文件讀取問題結構
features_config = {
    "cpu": {
        "feature_id": "cpu",
        "name": "處理器(CPU)偏好",
        "question_template": "請問您對處理器(CPU)有什麼偏好嗎？",
        "options": [
            {
                "option_id": "high_performance",
                "label": "🚀 高效能處理器",
                "description": "適合遊戲、創作、多工處理",
                "db_filter": {"cpu_tier": "high", "cpu_cores": ">=6"}
            }
        ]
    }
}
```

**隱喻說明：** 多輪對話管理器就像是一位「專業的銷售顧問」，會系統性地詢問客戶的需求，從處理器偏好、顯卡需求、記憶體大小等各個維度收集信息，最終提供最合適的推薦。

### 🎨 前端渲染函數 (Frontend Rendering)

**位置：** `static/js/sales_ai.js`

**表格數據渲染：**
```javascript
function renderMessageContent(container, content) {
    // 輸入：來自後端的JSON數據
    const tableData = content.comparison_table;
    
    // 轉換為Markdown格式
    let markdown = generateMarkdownTable(tableData);
    
    // 使用marked.js或自定義解析器渲染
    const html = renderMarkdownContent(markdown);
    
    // 更新DOM
    container.innerHTML = html;
}
```

**自定義表格解析：**
```javascript
function parseMarkdownTable(markdownText) {
    // 輸入Markdown表格
    const input = `
| 規格項目 | AG958 | APX958 |
|----------|-------|--------|
| CPU | Intel i7-12700H | AMD Ryzen 7 6800H |
`;
    
    // 解析過程
    const lines = markdownText.trim().split('\n');
    const headerCells = lines[0].split('|').map(cell => cell.trim()).filter(cell => cell);
    
    // 生成HTML表格
    let html = '<table>\n<thead>\n<tr>\n';
    headerCells.forEach(header => {
        html += `<th>${header}</th>\n`;
    });
    html += '</tr>\n</thead>\n<tbody>\n';
    
    // 處理數據行...
    
    return html;
}
```

**隱喻說明：** 前端渲染函數就像是一位「網頁設計師」，負責將後端提供的結構化數據轉換成用戶友好的視覺化表格和界面元素。

---

## 關鍵資源文件分析

### 📋 多輪對話配置 (nb_features.json)

**文件位置：** `libs/services/sales_assistant/multichat/nb_features.json`

**數據結構詳解：**
```json
{
  "nb_features": {
    "cpu": {
      "feature_id": "cpu",
      "feature_type": "cpu", 
      "name": "處理器(CPU)偏好",
      "description": "選擇適合您使用需求的處理器類型",
      "question_template": "請問您對處理器(CPU)有什麼偏好嗎？",
      "response_type": "single_choice",
      "keywords": ["CPU", "處理器", "運算", "Intel", "AMD"],
      "priority": 1,
      "required": true,
      "options": [...]
    }
  },
  "feature_priorities": {
    "gaming": ["gpu", "cpu", "memory", "storage", "price", "size", "weight"],
    "business": ["weight", "cpu", "price", "size", "memory", "storage", "gpu"]
  },
  "trigger_keywords": {
    "vague_queries": ["最適合", "推薦", "幫我選", "不知道選哪個"]
  }
}
```

**使用場景分析：**
1. **問題生成**：系統根據用戶類型動態生成相關問題
2. **選項過濾**：每個選項都包含`db_filter`用於後續數據庫查詢
3. **優先級排序**：不同使用場景（遊戲、商務）有不同的問題優先級

**隱喻說明：** 這個文件就像是「銷售手冊」，包含了銷售顧問需要詢問的所有標準問題以及針對不同客戶類型的溝通策略。

### 🔍 實體識別規則 (entity_patterns.json)

**文件位置：** `libs/services/sales_assistant/prompts/entity_patterns.json`

**正則表達式規則：**
```json
{
  "entity_patterns": {
    "MODEL_NAME": {
      "patterns": [
        "[A-Z]{2,3}\\d{3}(?:-[A-Z]+)?(?:\\s*:\\s*[A-Z]+\\d+[A-Z]*)?",
        "[A-Z]{2,3}\\d{3}(?:-[A-Z]+)?"
      ],
      "description": "筆電型號識別",
      "examples": ["AG958", "APX958", "AB819-S: FP6"]
    },
    "SPEC_TYPE": {
      "patterns": [
        "\\b(?:cpu|gpu|記憶體|硬碟|電池|螢幕)\\b",
        "\\b(?:processor|memory|storage|battery|screen)\\b"
      ],
      "description": "規格類型識別"
    }
  }
}
```

**實際應用：**
```python
# 在entity_recognition.py中使用
def extract_model_names(query):
    patterns = entity_patterns["MODEL_NAME"]["patterns"]
    for pattern in patterns:
        matches = re.findall(pattern, query, re.IGNORECASE)
        if matches:
            return matches
    return []
```

**隱喻說明：** 這個文件就像是「密碼破譯手冊」，包含了各種識別規則，幫助系統從用戶的自然語言中精確提取出技術規格和型號信息。

### 🗨️ 對話模板配置 (chats.json)

**文件位置：** `libs/services/sales_assistant/multichat/chats.json`

**模板結構：**
```json
{
  "greeting_templates": [
    "您好！我是筆電推薦助手，很高興為您服務。",
    "歡迎使用智能筆電推薦系統！"
  ],
  "question_templates": {
    "cpu_preference": "請問您主要用筆電做什麼用途呢？",
    "budget_inquiry": "您的預算範圍大約是多少呢？"
  },
  "response_templates": {
    "recommendation_intro": "根據您的需求，我推薦以下筆電：",
    "comparison_intro": "讓我為您比較這兩款筆電的差異："
  }
}
```

### 📝 CSV解析規則 (rules.json)

**文件位置：** `libs/parse/csvparse/rules.json` 和 `libs/parse/csvparse2/rules.json`

**解析規則結構：**
```json
{
  "column_mappings": {
    "型號": "modelname",
    "處理器": "cpu", 
    "顯卡": "gpu",
    "記憶體": "memory",
    "儲存": "storage"
  },
  "data_transformations": {
    "memory": {
      "pattern": "(\\d+)GB",
      "unit": "GB"
    },
    "storage": {
      "pattern": "(\\d+)(GB|TB)",
      "normalize": true
    }
  },
  "validation_rules": {
    "required_fields": ["modelname", "cpu", "gpu"],
    "data_types": {
      "modelname": "string",
      "memory": "integer"
    }
  }
}
```

**使用流程：**
```python
# 在csv_parser.py中使用
def parse_csv_with_rules(csv_file, rules):
    # 1. 讀取CSV文件
    df = pd.read_csv(csv_file)
    
    # 2. 應用列名映射
    df = df.rename(columns=rules["column_mappings"])
    
    # 3. 數據轉換
    for field, transform in rules["data_transformations"].items():
        df[field] = df[field].str.extract(transform["pattern"])
    
    # 4. 數據驗證
    validate_data(df, rules["validation_rules"])
    
    return df
```

**隱喻說明：** 解析規則文件就像是「翻譯字典」，幫助系統理解不同格式的Excel/CSV文件，將各種不同的列名和數據格式統一轉換為系統內部的標準格式。

---

## 核心組件運作原理

### 🎭 RAG系統：智能圖書館管理員

**組件位置：** `libs/RAG/`

RAG（Retrieval-Augmented Generation）系統就像是一位經驗豐富的圖書館管理員：

**1. 知識檢索階段 (Retrieval)**
```python
# MilvusQuery.py - 向量相似度搜索
def search(self, query_vector, top_k=5):
    # 就像管理員根據關鍵字快速定位相關書籍
    search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
    results = self.collection.search(
        data=[query_vector],
        anns_field="embedding",
        param=search_params,
        limit=top_k
    )
    return results

# DuckDBQuery.py - 結構化數據查詢  
def query(self, sql_query):
    # 就像從分類明確的檔案櫃中精確提取文件
    return self.connection.execute(sql_query).fetchall()
```

**2. 知識整合階段 (Augmentation)**
```python
# 將檢索到的結構化數據與向量搜索結果合併
def combine_retrieval_results(duckdb_results, milvus_results):
    # 就像管理員將不同來源的資料整理成完整的資料包
    combined_data = {
        "structured_specs": duckdb_results,
        "similar_products": milvus_results,
        "context": "laptop_comparison"
    }
    return combined_data
```

**3. 智能生成階段 (Generation)**
```python
# LLMInitializer.py
def generate_response(self, prompt, retrieved_data):
    # 就像管理員閱讀資料後用自己的話為讀者解釋
    enhanced_prompt = f"""
    基於以下檢索到的資料：{retrieved_data}
    用戶問題：{prompt}
    
    請提供專業的分析和建議。
    """
    return self.llm.invoke(enhanced_prompt)
```

### 🎪 多輪對話系統：專業銷售顧問

**核心檔案：** `libs/services/sales_assistant/multichat/multichat_manager.py`

多輪對話系統就像是一位專業的筆電銷售顧問，具備以下能力：

**1. 需求識別階段**
```python
def detect_user_intent(self, query):
    # 就像顧問聽到客戶說"我想要一台筆電"時
    # 能判斷這是模糊需求，需要進一步了解
    
    vague_keywords = self.config["trigger_keywords"]["vague_queries"]
    if any(keyword in query for keyword in vague_keywords):
        return "needs_clarification"
    
    comparison_keywords = self.config["trigger_keywords"]["comparison_queries"] 
    if any(keyword in query for keyword in comparison_keywords):
        return "direct_comparison"
        
    return "specific_inquiry"
```

**2. 系統性問題設計**
```python
def generate_questions_sequence(self, user_profile):
    # 就像顧問根據客戶類型（學生、商務人士、遊戲玩家）
    # 調整問題的優先順序和內容
    
    if user_profile == "gaming":
        priority_order = ["gpu", "cpu", "memory", "storage", "price"]
    elif user_profile == "business": 
        priority_order = ["weight", "cpu", "price", "size", "memory"]
    
    questions = []
    for feature_id in priority_order:
        question_config = self.features_config[feature_id]
        questions.append({
            "step": len(questions) + 1,
            "feature_id": feature_id, 
            "question": question_config["question_template"],
            "options": question_config["options"]
        })
    
    return questions
```

**3. 智能推薦生成**
```python
def generate_recommendations(self, user_answers):
    # 就像顧問收集完所有需求後，綜合分析並推薦最適合的產品
    
    # 1. 構建數據庫查詢條件
    db_filters = {}
    for feature_id, option_id in user_answers.items():
        option_config = self.get_option_config(feature_id, option_id)
        db_filters.update(option_config["db_filter"])
    
    # 2. 查詢符合條件的產品
    candidates = self.query_matching_products(db_filters)
    
    # 3. 使用LLM生成個性化推薦說明
    recommendation_prompt = f"""
    用戶偏好：{user_answers}
    候選產品：{candidates}
    
    請生成專業的推薦分析和比較表格。
    """
    
    return self.llm.generate(recommendation_prompt)
```

### 🔄 事件流處理：即時通訊系統

**Server-Sent Events (SSE) 流程：**

```python
# sales_routes.py 中的流式響應
async def chat_stream(request: Request):
    async def generate_stream():
        # 就像電話客服與客戶的即時對話
        service_response = service.chat_stream(query)
        
        async for chunk in service_response:
            # 每個回應片段都包裝成SSE格式
            sse_data = f"data: {json.dumps(chunk)}\n\n"
            yield sse_data.encode('utf-8')
    
    return StreamingResponse(
        generate_stream(), 
        media_type="text/event-stream"
    )
```

**前端即時接收處理：**
```javascript
// sales_ai.js 中的SSE處理
async function receiveStreamResponse() {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        
        // 解析SSE數據格式
        if (chunk.startsWith('data: ')) {
            const jsonData = JSON.parse(chunk.substring(6));
            
            // 根據回應類型進行不同的渲染處理
            switch(jsonData.type) {
                case 'multichat_start':
                    renderMultiChatStart(container, jsonData);
                    break;
                case 'multichat_question':
                    renderMultiChatQuestion(container, jsonData);
                    break;
                case 'multichat_complete':
                    renderMultiChatComplete(container, jsonData);
                    break;
            }
        }
    }
}
```

### 📊 智能表格渲染：數據視覺化專家

**Markdown表格轉HTML的處理流程：**

```javascript
// 智能表格渲染系統就像是一位數據視覺化專家
function renderMarkdownContent(markdownText) {
    // 1. 檢測內容類型
    const hasTable = markdownText.includes('|') && markdownText.includes('---');
    
    if (hasTable) {
        // 2. 嘗試使用marked.js進行標準轉換
        if (typeof marked !== 'undefined') {
            try {
                const result = marked.parse(markdownText);
                if (result.includes('<table>')) {
                    return result; // 成功使用標準解析器
                }
            } catch (error) {
                console.log('標準解析器失敗，使用自定義解析器');
            }
        }
        
        // 3. 回退到自定義表格解析器
        return parseMarkdownTable(markdownText);
    }
    
    // 4. 處理非表格內容
    return markdownText.replace(/\n/g, '<br>');
}

function parseMarkdownTable(markdownText) {
    // 自定義表格解析器就像是一位細心的排版師
    const lines = markdownText.trim().split('\n');
    
    // 解析表頭
    const headerCells = lines[0].split('|')
        .map(cell => cell.trim())
        .filter(cell => cell);
    
    // 跳過分隔線，解析數據行
    const dataRows = [];
    for (let i = 2; i < lines.length; i++) {
        if (lines[i].includes('|')) {
            const rowCells = lines[i].split('|')
                .map(cell => cell.trim())
                .filter(cell => cell);
            dataRows.push(rowCells);
        }
    }
    
    // 生成HTML表格
    let html = '<table>\n<thead>\n<tr>\n';
    headerCells.forEach(header => {
        const cleanHeader = header.replace(/\*\*(.*?)\*\*/g, '$1');
        html += `<th>${cleanHeader}</th>\n`;
    });
    html += '</tr>\n</thead>\n<tbody>\n';
    
    dataRows.forEach(row => {
        html += '<tr>\n';
        row.forEach(cell => {
            const cleanCell = cell.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            html += `<td>${cleanCell}</td>\n`;
        });
        html += '</tr>\n';
    });
    
    html += '</tbody>\n</table>';
    return html;
}
```

---

## 技術架構與依賴關係

### 🏗️ 系統架構層次

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                           │
│  templates/index.html + static/js/sales_ai.js              │
│  (用戶界面 + JavaScript事件處理)                             │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTP/SSE
┌─────────────────▼───────────────────────────────────────────┐
│                     API Layer                              │
│  main.py + api/sales_routes.py                            │
│  (FastAPI路由 + 請求處理)                                    │
└─────────────────┬───────────────────────────────────────────┘
                  │ Service Call
┌─────────────────▼───────────────────────────────────────────┐
│                  Service Layer                             │
│  libs/service_manager.py + SalesAssistantService          │
│  (業務邏輯協調 + 服務管理)                                    │
└─────────────────┬───────────────────────────────────────────┘
                  │ Data Processing
┌─────────────────▼───────────────────────────────────────────┐
│                    Data Layer                              │
│  RAG系統 + 多輪對話 + 實體識別                                │
└─────────────────┬───────────────────────────────────────────┘
                  │ Database Query + LLM Call
┌─────────────────▼───────────────────────────────────────────┐
│                Infrastructure Layer                        │
│  DuckDB + Milvus + Ollama (DeepSeek-R1)                  │
│  (數據存儲 + 向量數據庫 + 大語言模型)                          │
└─────────────────────────────────────────────────────────────┘
```

### 📦 核心技術棧

**Web框架層：**
- **FastAPI**: 現代Python Web框架，提供自動API文檔和高性能
- **Uvicorn**: ASGI服務器，支持異步處理和WebSocket/SSE
- **Jinja2**: 模板引擎，用於HTML頁面渲染

**數據存儲層：**
- **DuckDB**: 嵌入式分析型數據庫，適合OLAP查詢
- **SQLite**: 輕量級關係數據庫，用於歷史記錄存儲  
- **Milvus**: 向量數據庫，支持相似度搜索和語義檢索

**AI/ML層：**
- **LangChain**: LLM應用開發框架，提供鏈式調用和工具集成
- **Ollama**: 本地LLM服務，運行DeepSeek-R1模型
- **sentence-transformers**: 文本向量化，用於語義相似度計算

**前端技術：**
- **Vanilla JavaScript**: 原生JS，無額外框架依賴
- **Server-Sent Events**: 實現服務器推送和即時通訊
- **marked.js**: Markdown解析器，支持GitHub風格表格

### 🔗 數據流向圖

```
用戶輸入
    ↓
JavaScript事件處理
    ↓
HTTP POST → FastAPI路由
    ↓
ServiceManager調度
    ↓
┌─────────────────────────────────────┐
│          SalesAssistantService      │
│  ┌─────────────┐  ┌─────────────┐   │
│  │ Entity      │  │ Multichat   │   │
│  │ Recognition │  │ Manager     │   │  
│  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────┘
    ↓                    ↓
DuckDB查詢          向量搜索(Milvus)
    ↓                    ↓
結構化數據 ← 數據合併 → 相似產品
    ↓
LLM處理(Ollama + DeepSeek-R1)
    ↓
JSON格式化回應
    ↓
SSE串流傳輸
    ↓
前端JavaScript解析
    ↓
DOM更新 + 表格渲染
    ↓
用戶看到結果
```

### ⚙️ 配置管理體系

**集中配置文件：** `config.py`
```python
# 數據庫配置
DB_PATH = BASE_DIR / "db" / "sales_specs.db"
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
MILVUS_COLLECTION_NAME = "sales_notebook_specs"

# 應用設置  
APP_HOST = "0.0.0.0"
APP_PORT = 8001

# 服務配置
SERVICES_CONFIG = {
    "sales_assistant": {
        "enabled": True,
        "db_path": str(DB_PATH),
        "milvus_host": MILVUS_HOST,
        "milvus_port": MILVUS_PORT,
        "collection_name": MILVUS_COLLECTION_NAME
    }
}
```

**JSON配置文件結構：**
```
libs/services/sales_assistant/
├── multichat/
│   ├── nb_features.json      # 多輪對話問題配置
│   ├── chats.json           # 對話模板配置  
│   └── templates.py         # 模板處理邏輯
├── prompts/
│   ├── entity_patterns.json # 實體識別規則
│   ├── query_keywords.json  # 查詢關鍵字分類
│   └── sales_prompt4.txt    # LLM提示詞模板
└── service.py              # 核心服務邏輯
```

### 🚀 性能優化策略

**1. 數據庫優化：**
- DuckDB採用列式存儲，優化分析查詢性能
- 合理的索引設計，加速常用查詢
- 讀寫分離，查詢使用read_only模式

**2. 緩存策略：**
- LLM回應結果緩存，避免重複計算
- 向量數據預計算和存儲
- 靜態資源CDN緩存

**3. 異步處理：**
- FastAPI異步路由，提高並發處理能力
- SSE流式回應，改善用戶體驗
- 數據庫查詢與向量搜索並行執行

**4. 前端優化：**
- JavaScript模塊化，按需加載
- DOM更新批處理，減少重繪
- 自定義表格解析器，降低依賴

### 🔒 安全性考量

**1. 輸入驗證：**
- SQL注入防護，使用參數化查詢
- XSS防護，HTML內容轉義
- 文件上傳類型和大小限制

**2. 數據保護：**
- 數據庫讀取權限控制
- 敏感配置環境變量化
- 錯誤信息脫敏處理

**3. 服務安全：**
- CORS策略配置
- 請求頻率限制
- 服務健康檢查

### 📈 監控與日誌

**日誌系統配置：**
```python
# main.py中的日誌設置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
```

**關鍵監控指標：**
- API響應時間和成功率
- 數據庫查詢性能
- LLM調用延遲和錯誤率  
- 內存和CPU使用情況
- 併發用戶數和請求量

---

## 總結

SalesRAG系統是一個精心設計的智能筆電推薦平台，通過多層架構設計實現了從用戶輸入到智能推薦的完整流程。系統的核心優勢在於：

1. **智能化程度高**：結合RAG技術和大語言模型，提供專業的產品分析
2. **用戶體驗優秀**：通過多輪對話和即時流式回應，提供個性化服務
3. **技術架構合理**：模塊化設計，便於維護和擴展
4. **數據處理能力強**：雙數據庫架構，支持結構化查詢和語義搜索

通過本文檔的詳細分析，開發者可以快速理解系統的運作機制，為後續的功能開發和系統優化提供參考。

---

*文檔生成時間：2025年1月*  
*系統版本：SalesRAG v1.0*  
*分析深度：完整系統流程 + 函數級別數據轉換*