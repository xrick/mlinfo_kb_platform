我將進入研究模式來分析 `sales_ai.js` 從系統啟動到實際使用的完整流程。讓我先查看相關的系統架構和啟動流程。

[8 tools called]

基於對系統架構的深入分析，我現在可以詳細解釋 `sales_ai.js` 從系統啟動到實際使用的完整流程。

## 🚀 `sales_ai.js` 從系統啟動到使用的完整流程分析

### **第一階段：系統啟動 (main.py)**

#### **1. 應用程式初始化**

```python
# main.py 啟動流程
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=APP_HOST,        # 0.0.0.0
        port=APP_PORT,        # 8001
        reload=True,          # 開發模式自動重載
        log_level="info"
    )
```

#### **2. FastAPI 應用程式配置**

```python
# 創建 FastAPI 實例
app = FastAPI(
    title="MGFD SalesRAG Integration System",
    description="智能對話系統 - 基於FastAPI的現代化實現",
    version="2.0.0"
)

# 掛載靜態檔案目錄
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 設定模板引擎
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
```

#### **3. API 路由註冊(main.py)**

```python
# 註冊銷售相關 API 路由
from api import sales_routes
app.include_router(sales_routes.router, prefix="/api/sales", tags=["sales"])

# 主要端點：
# - /api/sales/chat-stream     # 流式聊天
# - /api/sales/funnel-question # 漏斗問題
# - /api/sales/funnel-choice   # 漏斗選擇
# - /api/sales/multichat       # 多輪對話
# - /api/sales/specialized-flow # 專業流程
```

### **第二階段：HTTP 服務啟動**

#### **4. 服務器啟動事件**

```python
@app.on_event("startup")
async def startup_event():
    logging.info("🚀 MGFD SalesRAG Integration System 啟動中...")
    logging.info(f"�� API文檔: http://{APP_HOST}:{APP_PORT}/docs")
    logging.info("✅ 系統啟動完成")
```

#### **5. 根路徑處理**

```python
@app.get("/", response_class=HTMLResponse)
async def main_interface(request: Request):
    """主要整合介面"""
    return templates.TemplateResponse("index.html", {"request": request})
```

### **第三階段：前端頁面載入**

#### **6. HTML 模板渲染**

```html
<!-- templates/index.html -->
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <title>SalesRAG 整合系統</title>
    <link rel="stylesheet" href="/static/css/integrated.css?v=20250724e">
    <link rel="stylesheet" href="/static/css/components.css?v=20250724e">
</head>
<body>
    <!-- 主要介面結構 -->
    <div class="app-container">
        <aside class="sidebar">
            <!-- 導航按鈕 -->
            <button id="sales-ai-btn" class="nav-button active" onclick="switchView('sales-ai')">
                <div class="nav-icon">💻</div>
                <div class="nav-text">Sales-AI</div>
            </button>
        </aside>

        <main class="main-content">
            <!-- Sales-AI 視圖 -->
            <div id="sales-ai-view" class="content-view active">
                <div id="chatMessages" class="chat-messages"></div>
                <div class="chat-input-container">
                    <textarea id="userInput" class="chat-input"></textarea>
                    <button id="sendButton" class="btn btn--primary">發送</button>
                </div>
            </div>
        </main>
    </div>

    <!-- JavaScript 腳本載入順序 -->
    <script src="/static/js/marked.min.js"></script>        <!-- Markdown 解析器 -->
    <script src="/static/js/app.js?v=20250724e"></script>   <!-- 主應用邏輯 -->
    <script src="/static/js/sales_ai.js?v=20250724e"></script> <!-- 銷售 AI 核心 -->
    <script src="/static/js/history.js?v=20250724e"></script>  <!-- 歷史記錄 -->
</body>
</html>
```

### **第四階段：JavaScript 初始化**

#### **7. 主應用程式初始化 (app.js)**

```javascript
// static/js/app.js
document.addEventListener('DOMContentLoaded', function() {
    hljs.highlightAll();        // 語法高亮
    initializeApp();            // 初始化主應用
});

function initializeApp() {
    console.log('Initializing SalesRAG Integration App...');
    setupEventListeners();      // 設置事件監聽器
    switchView('sales-ai');     // 切換到銷售 AI 視圖
    loadHistory();              // 載入歷史記錄
}
```

#### **8. 視圖切換與 Sales AI 初始化**

```javascript
function switchView(viewName) {
    // 隱藏所有視圖
    document.querySelectorAll('.content-view').forEach(view => {
        view.classList.remove('active');
        view.classList.add('hidden');
    });

    // 顯示目標視圖
    const targetView = document.getElementById(viewName + '-view');
    if (targetView) {
        targetView.classList.remove('hidden');
        targetView.classList.add('active');
    }

    // 初始化視圖特定功能
    if (viewName === 'sales-ai') {
        initializeSalesAI();    // 初始化銷售 AI
    }
}

function initializeSalesAI() {
    console.log('Initializing Sales-AI view...');
    if (typeof initSalesAI === 'function') {
        initSalesAI();          // 調用 sales_ai.js 的初始化函數
    }
}
```

### **第五階段：Sales AI 核心功能啟動**

#### **9. Sales AI 初始化 (sales_ai.js)**

```javascript
// static/js/sales_ai.js
function initSalesAI() {
    console.log('Initializing Sales AI view...');

    // 檢查 marked.js 並配置
    if (typeof marked !== 'undefined' && marked.parse) {
        configureMarkedJS();
        testMarkdownTableConversion();
    }

    // 設置事件監聽器
    const userInput = document.getElementById("userInput");
    const sendButton = document.getElementById("sendButton");
    const chatMessages = document.getElementById("chatMessages");

    // 綁定發送按鈕事件
    sendButton.addEventListener("click", sendMessage);

    // 綁定預設問題按鈕
    const presetButtons = document.querySelector('.preset-buttons');
    if (presetButtons) {
        presetButtons.addEventListener('click', (e) => {
            if (e.target.classList.contains('preset-btn')) {
                userInput.value = e.target.dataset.question;
                sendMessage();
            }
        });
    }
}
```

### **第六階段：用戶互動與 API 通信**

#### **10. 用戶輸入處理**

```javascript
async function sendMessage() {
    const query = userInput.value.trim();
    if (!query) return;

    // 顯示用戶訊息
    appendMessage({ role: "user", content: query });
    userInput.value = "";
    toggleInput(true);

    // 顯示思考指示器
    const thinkingBubble = showThinkingIndicator();

    try {
        // 發送 API 請求到後端
        const response = await fetch("/api/sales/chat-stream", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                query: query, 
                service_name: "sales_assistant" 
            }),
        });

        // 處理流式響應
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            // 解析 SSE 數據並更新介面
            processStreamingResponse(chunk);
        }
    } catch (error) {
        console.error("請求錯誤:", error);
        appendMessage({ role: 'assistant', content: { error: `請求失敗: ${error.message}` } });
    } finally {
        toggleInput(false);
        userInput.focus();
    }
}
```

### **第七階段：後端服務處理**

#### **11. API 路由處理 (sales_routes.py)**

```python
@router.post("/chat-stream")
async def chat_stream(request: Request):
    """處理聊天請求並返回流式響應"""
    try:
        data = await request.json()
        query = data.get("query")
        service_name = data.get("service_name", "sales_assistant")

        # 獲取服務實例
        service = service_manager.get_service(service_name)
        if not service:
            return JSONResponse(status_code=404, content={"error": f"Service '{service_name}' not found"})

        # 返回流式響應
        return StreamingResponse(
            service.chat_stream(query), 
            media_type="text/event-stream"
        )
    except Exception as e:
        logging.error(f"Error in chat_stream: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})
```

#### **12. 服務管理器處理**

```python
# libs/service_manager.py
class ServiceManager:
    def get_service(self, service_name):
        """獲取指定的服務實例"""
        if service_name == "sales_assistant":
            return self.sales_assistant_service
        # ... 其他服務

    def sales_assistant_service(self, query):
        """銷售助手服務的聊天流處理"""
        # 調用 MGFD 系統或 RAG 系統處理查詢
        # 返回流式響應
```

### **完整流程總結**

1. **系統啟動**: `python main.py` → 啟動 FastAPI 服務器
2. **服務配置**: 註冊 API 路由，掛載靜態檔案和模板
3. **頁面請求**: 用戶訪問 `/` → 渲染 `index.html`
4. **腳本載入**: 按順序載入 JavaScript 文件
5. **應用初始化**: `app.js` 初始化主應用，切換到 Sales AI 視圖
6. **Sales AI 啟動**: `sales_ai.js` 初始化聊天介面和事件監聽器
7. **用戶互動**: 用戶輸入問題 → 觸發 `sendMessage()` 函數
8. **API 通信**: 發送 POST 請求到 `/api/sales/chat-stream`
9. **後端處理**: 路由到 `sales_routes.py` → 服務管理器 → AI 服務
10. **流式響應**: 返回 Server-Sent Events 格式的數據
11. **前端更新**: 實時解析響應並更新聊天介面

這個流程展現了一個完整的現代化 Web 應用架構，從後端服務啟動到前端功能初始化，再到用戶互動和 AI 服務響應的完整閉環。`sales_ai.js` 作為前端核心，在用戶訪問頁面後自動初始化，並在整個用戶會話期間保持活躍狀態。