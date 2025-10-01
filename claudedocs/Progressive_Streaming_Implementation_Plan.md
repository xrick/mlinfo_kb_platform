# Progressive Streaming Implementation Plan
## Optimistic Progressive Markdown Parsing + 5-Phase Prompt Chunking

**Date**: 2025-10-01
**Project**: mlinfo_kb_platform (SalesRAG System)
**Goal**: 實現 ChatGPT 風格的漸進式 markdown 渲染，並將大型查詢拆分成 5 個階段處理

---

## 📊 系統架構總覽

### Current Architecture
```
User Query
  → /api/sales/chat-stream
    → ServiceManager.get_service("sales_assistant")
      → SalesAssistantService.chat_stream(query)
        → [Current: Simple streaming]
```

### Target Architecture (5-Phase Progressive Streaming)
```
User Query
  → /api/sales/chat-stream
    → SalesAssistantService.chat_stream_progressive(query)
      │
      ├─ Phase 1: Query Understanding (streaming)
      │    ├─ LLM: Extract intent & entities
      │    ├─ Stream: 🔍 正在分析您的查詢...
      │    └─ Output: {"intent": "compare", "entities": ["APX819", "APX839"]}
      │
      ├─ Phase 2: Multi-source Data Retrieval (parallel + streaming)
      │    ├─ Milvus Semantic Search (async)
      │    ├─ DuckDB Spec Query (async)
      │    ├─ Stream: 📦 正在檢索產品資料 (1/2)...
      │    └─ Output: {"products": [...], "specs": [...]}
      │
      ├─ Phase 3: Context Assembly & Ranking (streaming)
      │    ├─ Merge and rank results
      │    ├─ Apply context truncation
      │    ├─ Stream: 📊 正在整理產品資訊...
      │    └─ Output: {"ranked_products": [...], "context_tokens": 15000}
      │
      ├─ Phase 4: Response Generation (progressive markdown streaming)
      │    ├─ LLM with streaming callback
      │    ├─ Stream: Token-by-token markdown
      │    │    → ## 產品比較分析
      │    │    → **APX819** 是一款...
      │    │    → | 產品 | CPU | GPU |
      │    └─ Progressive Markdown Parsing (Frontend)
      │
      └─ Phase 5: Post-processing & Formatting (streaming)
           ├─ Add metadata and citations
           ├─ Stream: ✅ 分析完成
           └─ Output: Complete formatted response
```

---

## 🎯 實作優先級

根據您的決策：

1. **Performance optimization** (caching, parallel processing)
2. **Prompt chunking** for large context
3. **Progressive markdown rendering**
4. **Progress indication**
5. **Error recovery** and partial results

---

## 📐 Phase-by-Phase Implementation Details

### Phase 1: Query Understanding & Entity Extraction

**目標**: 從用戶查詢中提取結構化意圖和實體

**Prompt Template**:
```python
QUERY_UNDERSTANDING_PROMPT = """
你是一個專業的產品查詢分析助手。請分析以下用戶查詢並提取關鍵信息。

用戶查詢：{user_query}

可用產品型號：{available_modelnames}
可用機型類別：{available_modeltypes}

請以 JSON 格式回答，包含以下欄位：
{{
  "intent": "compare|recommend|spec_query|general_inquiry",
  "detected_products": ["產品1", "產品2"],
  "detected_modeltypes": ["819", "839"],
  "key_features": ["CPU", "GPU", "記憶體"],
  "user_focus": "效能|價格|攜帶性|電池續航力",
  "complexity": "simple|medium|complex"
}}

只回覆 JSON，不要其他說明。
"""
```

**Implementation**:
```python
async def phase1_query_understanding(self, query: str) -> Dict[str, Any]:
    """Phase 1: 查詢理解與實體提取"""

    # Prepare prompt
    prompt = QUERY_UNDERSTANDING_PROMPT.format(
        user_query=query,
        available_modelnames=AVAILABLE_MODELNAMES[:20],  # Limit for token efficiency
        available_modeltypes=AVAILABLE_MODELTYPES
    )

    # Stream progress update
    yield {
        "type": "progress",
        "phase": 1,
        "message": "🔍 正在分析您的查詢...",
        "progress": 10
    }

    # LLM Call with streaming
    response = await self.llm.ainvoke(prompt)

    try:
        analysis = json.loads(response.content)
    except json.JSONDecodeError:
        # Fallback to regex extraction
        analysis = self._fallback_entity_extraction(query)

    # Stream result
    yield {
        "type": "phase_result",
        "phase": 1,
        "data": analysis,
        "progress": 20
    }

    return analysis
```

**Performance Optimization**:
- **Cache frequently queried entities**: Use Redis to cache entity extraction results
- **Regex-based fast path**: For simple queries (single product code), skip LLM

---

### Phase 2: Multi-source Data Retrieval (Parallel)

**目標**: 並行檢索 Milvus 語義搜索和 DuckDB 規格查詢

**Implementation**:
```python
async def phase2_data_retrieval(
    self,
    query: str,
    analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """Phase 2: 並行多來源資料檢索"""

    # Stream progress
    yield {
        "type": "progress",
        "phase": 2,
        "message": "📦 正在檢索產品資料...",
        "progress": 25
    }

    # Parallel retrieval
    import asyncio

    tasks = [
        self._retrieve_from_milvus(query, top_k=30),
        self._retrieve_from_duckdb(analysis.get("detected_products", []))
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    milvus_results = results[0] if not isinstance(results[0], Exception) else []
    duckdb_results = results[1] if not isinstance(results[1], Exception) else []

    # Stream intermediate result
    yield {
        "type": "progress",
        "phase": 2,
        "message": f"✓ 找到 {len(milvus_results)} 個語義匹配結果",
        "progress": 35
    }

    yield {
        "type": "progress",
        "phase": 2,
        "message": f"✓ 找到 {len(duckdb_results)} 個規格資料",
        "progress": 45
    }

    # Combine results
    combined_results = {
        "semantic_matches": milvus_results,
        "spec_data": duckdb_results,
        "total_products": len(set([r['product_id'] for r in milvus_results]))
    }

    yield {
        "type": "phase_result",
        "phase": 2,
        "data": combined_results,
        "progress": 50
    }

    return combined_results
```

**Performance Optimization**:
- **Result caching**: Cache Milvus results for 5 minutes (query → results mapping)
- **Connection pooling**: Reuse DuckDB connections
- **Parallel execution**: Use `asyncio.gather()` for true parallelism

---

### Phase 3: Context Assembly & Ranking

**目標**: 整理、排序並截斷 context 以符合 token 限制

**Implementation**:
```python
async def phase3_context_assembly(
    self,
    retrieval_results: Dict[str, Any],
    analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """Phase 3: Context 組裝與排序"""

    yield {
        "type": "progress",
        "phase": 3,
        "message": "📊 正在整理產品資訊...",
        "progress": 55
    }

    # Merge semantic matches with spec data
    merged_products = self._merge_semantic_and_spec_data(
        retrieval_results["semantic_matches"],
        retrieval_results["spec_data"]
    )

    # Rank by relevance
    ranked_products = self._rank_products_by_relevance(
        merged_products,
        analysis.get("key_features", [])
    )

    # Context truncation based on MAX_CONTEXT_TOKENS
    truncated_context = self._truncate_context(
        ranked_products,
        max_tokens=self.MAX_CONTEXT_TOKENS - 10000  # Reserve for prompt
    )

    yield {
        "type": "progress",
        "phase": 3,
        "message": f"✓ 已整理 {len(truncated_context['products'])} 個產品（使用 {truncated_context['token_count']} tokens）",
        "progress": 65
    }

    yield {
        "type": "phase_result",
        "phase": 3,
        "data": truncated_context,
        "progress": 70
    }

    return truncated_context
```

**Context Truncation Strategy**:
```python
def _truncate_context(self, products: List[Dict], max_tokens: int) -> Dict[str, Any]:
    """智能截斷 context"""

    # Strategy 1: Remove low-relevance products
    products = products[:10]  # Keep top 10 by relevance score

    # Strategy 2: Remove non-essential fields
    essential_fields = ['modeltype', 'modelname', 'cpu', 'gpu', 'memory',
                       'storage', 'lcd', 'battery', 'thermal', 'ai']

    truncated_products = []
    for product in products:
        truncated = {k: v for k, v in product.items() if k in essential_fields}
        truncated_products.append(truncated)

    # Strategy 3: Estimate tokens and further truncate if needed
    context_text = json.dumps(truncated_products, ensure_ascii=False)
    estimated_tokens = len(context_text) // 3  # Rough estimate: 1 token ≈ 3 chars

    if estimated_tokens > max_tokens:
        # Further reduce: keep top 5 products
        truncated_products = truncated_products[:5]
        estimated_tokens = len(json.dumps(truncated_products)) // 3

    return {
        "products": truncated_products,
        "token_count": estimated_tokens,
        "truncation_applied": len(products) > len(truncated_products)
    }
```

**Performance Optimization**:
- **Lazy field loading**: Only load essential fields from DuckDB
- **Token estimation caching**: Cache token counts for common field combinations
- **Smart summarization**: For very long specs, use LLM to summarize

---

### Phase 4: Response Generation (Progressive Markdown Streaming)

**目標**: 使用 LangChain streaming callback 實現 token-by-token markdown 輸出

**Prompt Template**:
```python
RESPONSE_GENERATION_PROMPT = """
你是一個專業的筆記型電腦銷售助手。請根據以下產品資料回答用戶的問題。

用戶查詢：{user_query}

查詢分析：
- 意圖：{intent}
- 關注重點：{user_focus}

產品資料：
{product_context}

請以繁體中文回答，格式要求：
1. 使用 Markdown 格式（headers, bold, tables）
2. 如果是產品比較，使用表格呈現關鍵規格差異
3. 提供清晰的購買建議，說明適用場景
4. 保持專業但友善的語氣

開始回答：
"""
```

**LangChain Streaming Implementation**:
```python
from langchain.callbacks.base import AsyncCallbackHandler

class ProgressiveStreamingCallback(AsyncCallbackHandler):
    """Custom callback for progressive markdown streaming"""

    def __init__(self, queue: asyncio.Queue):
        self.queue = queue

    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Called when new token is generated"""
        await self.queue.put({
            "type": "markdown_token",
            "token": token,
            "phase": 4
        })

async def phase4_response_generation(
    self,
    query: str,
    analysis: Dict[str, Any],
    context: Dict[str, Any]
) -> AsyncGenerator:
    """Phase 4: 漸進式回應生成"""

    yield {
        "type": "progress",
        "phase": 4,
        "message": "✍️ 正在生成回答...",
        "progress": 75
    }

    # Prepare prompt
    prompt = RESPONSE_GENERATION_PROMPT.format(
        user_query=query,
        intent=analysis.get("intent", "general"),
        user_focus=analysis.get("user_focus", "全面評估"),
        product_context=self._format_product_context(context["products"])
    )

    # Setup streaming callback
    queue = asyncio.Queue()
    callback = ProgressiveStreamingCallback(queue)

    # Start LLM generation in background task
    async def generate():
        await self.llm.ainvoke(prompt, callbacks=[callback])
        await queue.put(None)  # Signal completion

    task = asyncio.create_task(generate())

    # Stream tokens as they arrive
    while True:
        token_data = await queue.get()
        if token_data is None:
            break
        yield token_data

    await task

    yield {
        "type": "progress",
        "phase": 4,
        "message": "✅ 回答生成完成",
        "progress": 95
    }
```

**Performance Optimization**:
- **Response caching**: Cache similar queries' responses for 30 minutes
- **Temperature optimization**: Use lower temperature (0.3) for faster, more deterministic responses
- **Token limit per phase**: Cap Phase 4 output at 2000 tokens to avoid excessive generation

---

### Phase 5: Post-processing & Formatting

**目標**: 添加元數據、引用來源、格式驗證

**Implementation**:
```python
async def phase5_postprocessing(
    self,
    generated_response: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Phase 5: 後處理與格式化"""

    yield {
        "type": "progress",
        "phase": 5,
        "message": "🎨 正在完成最後修飾...",
        "progress": 97
    }

    # Add metadata
    response_with_metadata = {
        "response": generated_response,
        "metadata": {
            "products_analyzed": len(context["products"]),
            "context_tokens": context["token_count"],
            "timestamp": datetime.now().isoformat(),
            "model": self.llm_initializer.model_name
        },
        "sources": [
            {
                "product_id": p["modeltype"],
                "product_name": p["modelname"]
            }
            for p in context["products"]
        ]
    }

    # Validate markdown format
    if not self._is_valid_markdown(generated_response):
        logging.warning("Generated response has markdown format issues")
        # Optional: Fix common markdown issues
        response_with_metadata["response"] = self._fix_markdown(generated_response)

    yield {
        "type": "complete",
        "phase": 5,
        "data": response_with_metadata,
        "progress": 100
    }

    return response_with_metadata
```

---

## 🔧 Main Orchestrator: chat_stream_progressive()

**Complete Integration**:
```python
async def chat_stream_progressive(self, query: str) -> AsyncGenerator:
    """
    主要流式處理函數：協調 5 個階段的漸進式處理

    Yields:
        Dict with keys: type, phase, message, data, token, progress

    Types:
        - "progress": Phase進度更新
        - "phase_result": 階段完成結果
        - "markdown_token": Markdown token (Phase 4)
        - "complete": 最終完成
    """

    try:
        # Phase 1: Query Understanding
        async for update in self.phase1_query_understanding(query):
            yield self._format_sse(update)
            if update["type"] == "phase_result":
                analysis = update["data"]

        # Phase 2: Data Retrieval (Parallel)
        async for update in self.phase2_data_retrieval(query, analysis):
            yield self._format_sse(update)
            if update["type"] == "phase_result":
                retrieval_results = update["data"]

        # Phase 3: Context Assembly
        async for update in self.phase3_context_assembly(retrieval_results, analysis):
            yield self._format_sse(update)
            if update["type"] == "phase_result":
                context = update["data"]

        # Phase 4: Response Generation (Progressive Markdown)
        async for update in self.phase4_response_generation(query, analysis, context):
            yield self._format_sse(update)

        # Phase 5: Post-processing
        async for update in self.phase5_postprocessing(
            generated_response="",  # Accumulated from Phase 4
            context=context
        ):
            yield self._format_sse(update)

    except Exception as e:
        logging.error(f"Error in progressive streaming: {e}")
        yield self._format_sse({
            "type": "error",
            "message": f"處理過程中發生錯誤: {str(e)}",
            "partial_results": True
        })

def _format_sse(self, data: Dict[str, Any]) -> str:
    """Format data as Server-Sent Event"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
```

---

## 🎨 Frontend: Progressive Markdown Parser

**JavaScript Implementation**:
```javascript
// File: static/js/progressive_markdown_renderer.js

class ProgressiveMarkdownRenderer {
    constructor(containerSelector, progressBarSelector) {
        this.container = document.querySelector(containerSelector);
        this.progressBar = document.querySelector(progressBarSelector);
        this.accumulated = "";
        this.currentPhase = 0;

        // Configure marked.js for better parsing
        marked.setOptions({
            breaks: true,
            gfm: true,
            tables: true
        });
    }

    addToken(token) {
        // Accumulate token
        this.accumulated += token;

        // Try to parse as markdown
        try {
            const html = marked.parse(this.accumulated);
            this.container.innerHTML = html;
        } catch (e) {
            // If parsing fails, show as plain text
            this.container.textContent = this.accumulated;
        }

        // Auto-scroll to bottom
        this.container.scrollTop = this.container.scrollHeight;
    }

    updateProgress(phase, message, progress) {
        // Update progress bar
        if (this.progressBar) {
            this.progressBar.style.width = `${progress}%`;
            this.progressBar.textContent = `${message} (${progress}%)`;
        }

        // Add phase indicator
        if (phase !== this.currentPhase) {
            this.currentPhase = phase;
            this.addPhaseMarker(phase, message);
        }
    }

    addPhaseMarker(phase, message) {
        // Add visual separator between phases
        const marker = document.createElement('div');
        marker.className = 'phase-marker';
        marker.innerHTML = `<hr/><small>${message}</small>`;
        this.container.appendChild(marker);
    }

    complete() {
        // Final render to ensure perfect formatting
        const html = marked.parse(this.accumulated);
        this.container.innerHTML = html;

        if (this.progressBar) {
            this.progressBar.style.width = '100%';
            this.progressBar.textContent = '完成 ✓';
            this.progressBar.classList.add('complete');
        }
    }

    handleError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = `⚠️ ${message}`;
        this.container.appendChild(errorDiv);
    }
}

// Usage with EventSource (SSE)
function startProgressiveChat(query) {
    const renderer = new ProgressiveMarkdownRenderer(
        '#chat-response',
        '#progress-bar'
    );

    const eventSource = new EventSource(
        `/api/sales/chat-stream?query=${encodeURIComponent(query)}`
    );

    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);

        switch (data.type) {
            case 'progress':
                renderer.updateProgress(
                    data.phase,
                    data.message,
                    data.progress
                );
                break;

            case 'markdown_token':
                renderer.addToken(data.token);
                break;

            case 'complete':
                renderer.complete();
                eventSource.close();
                break;

            case 'error':
                renderer.handleError(data.message);
                eventSource.close();
                break;
        }
    };

    eventSource.onerror = (error) => {
        console.error('SSE Error:', error);
        renderer.handleError('連線中斷，請重試');
        eventSource.close();
    };
}
```

**CSS Styling**:
```css
/* File: static/css/progressive_streaming.css */

/* Progress bar */
#progress-bar {
    width: 0%;
    height: 30px;
    background: linear-gradient(90deg, #4CAF50, #8BC34A);
    color: white;
    text-align: center;
    line-height: 30px;
    border-radius: 5px;
    transition: width 0.3s ease;
}

#progress-bar.complete {
    background: #4CAF50;
}

/* Chat response container */
#chat-response {
    max-height: 600px;
    overflow-y: auto;
    padding: 20px;
    background: #f9f9f9;
    border-radius: 8px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* Markdown elements */
#chat-response h2 {
    color: #333;
    border-bottom: 2px solid #4CAF50;
    padding-bottom: 5px;
    margin-top: 20px;
}

#chat-response table {
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
}

#chat-response table th,
#chat-response table td {
    border: 1px solid #ddd;
    padding: 10px;
    text-align: left;
}

#chat-response table th {
    background-color: #4CAF50;
    color: white;
}

/* Phase markers */
.phase-marker {
    margin: 10px 0;
    opacity: 0.6;
}

.phase-marker hr {
    border: none;
    border-top: 1px dashed #999;
}

/* Error messages */
.error-message {
    background: #f44336;
    color: white;
    padding: 10px;
    border-radius: 5px;
    margin: 10px 0;
}
```

---

## 🚀 Performance Optimization Strategies

### 1. Redis Caching Layer

**Cache Strategy**:
```python
import redis
import hashlib

class ProgressiveStreamingCache:
    """Redis-based caching for progressive streaming"""

    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )

    def get_cache_key(self, query: str, phase: int) -> str:
        """Generate cache key"""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return f"stream:phase{phase}:{query_hash}"

    async def get_cached_phase_result(self, query: str, phase: int):
        """Get cached phase result"""
        key = self.get_cache_key(query, phase)
        cached = self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def cache_phase_result(
        self,
        query: str,
        phase: int,
        result: Dict[str, Any],
        ttl: int = 300  # 5 minutes
    ):
        """Cache phase result"""
        key = self.get_cache_key(query, phase)
        self.redis.setex(
            key,
            ttl,
            json.dumps(result, ensure_ascii=False)
        )
```

**Integration**:
```python
# In SalesAssistantService.__init__()
self.cache = ProgressiveStreamingCache()

# In phase methods
async def phase1_query_understanding(self, query: str):
    # Check cache first
    cached = await self.cache.get_cached_phase_result(query, phase=1)
    if cached:
        yield {
            "type": "phase_result",
            "phase": 1,
            "data": cached,
            "from_cache": True
        }
        return cached

    # ... normal processing ...

    # Cache result
    await self.cache.cache_phase_result(query, phase=1, result=analysis)
```

### 2. Parallel Processing Optimization

**Async DuckDB Query**:
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncDuckDBQuery:
    """Async wrapper for DuckDB queries"""

    def __init__(self, db_file: str):
        self.db_file = db_file
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def execute_async(self, query: str):
        """Execute DuckDB query in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._execute_sync,
            query
        )

    def _execute_sync(self, query: str):
        import duckdb
        conn = duckdb.connect(self.db_file)
        result = conn.execute(query).fetchall()
        conn.close()
        return result
```

### 3. Token Estimation & Context Window Management

**Accurate Token Counter**:
```python
import tiktoken

class TokenManager:
    """Manage token counting and context window"""

    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.encoder = tiktoken.encoding_for_model(model_name)
        self.max_tokens = 131072  # gpt-oss:20b

    def count_tokens(self, text: str) -> int:
        """Accurate token counting"""
        return len(self.encoder.encode(text))

    def truncate_to_token_limit(
        self,
        text: str,
        max_tokens: int
    ) -> str:
        """Truncate text to fit token limit"""
        tokens = self.encoder.encode(text)
        if len(tokens) <= max_tokens:
            return text

        truncated_tokens = tokens[:max_tokens]
        return self.encoder.decode(truncated_tokens)
```

---

## 📁 File Structure Changes

**New Files to Create**:
```
mlinfo_kb_platform/
├── libs/
│   ├── services/
│   │   └── sales_assistant/
│   │       ├── progressive_streaming.py (NEW)
│   │       ├── phase_processors.py (NEW)
│   │       ├── streaming_callbacks.py (NEW)
│   │       └── prompts/
│   │           ├── phase1_query_understanding.txt (NEW)
│   │           ├── phase4_response_generation.txt (NEW)
│   │           └── ...
│   └── caching/
│       └── redis_cache.py (NEW)
├── static/
│   ├── js/
│   │   └── progressive_markdown_renderer.js (NEW)
│   └── css/
│       └── progressive_streaming.css (NEW)
└── claudedocs/
    └── Progressive_Streaming_Implementation_Plan.md (THIS FILE)
```

---

## 🧪 Testing Plan

### Unit Tests
```python
# tests/test_progressive_streaming.py

import pytest
from libs.services.sales_assistant.progressive_streaming import (
    ProgressiveStreamingService
)

@pytest.mark.asyncio
async def test_phase1_query_understanding():
    """Test Phase 1: Query Understanding"""
    service = ProgressiveStreamingService()

    query = "比較 APX819 和 APX839 的 CPU 效能"

    results = []
    async for update in service.phase1_query_understanding(query):
        results.append(update)

    # Check that we got phase result
    phase_results = [r for r in results if r["type"] == "phase_result"]
    assert len(phase_results) == 1

    # Check detected entities
    analysis = phase_results[0]["data"]
    assert "APX819" in analysis["detected_products"]
    assert "APX839" in analysis["detected_products"]
    assert analysis["intent"] == "compare"

@pytest.mark.asyncio
async def test_parallel_retrieval():
    """Test Phase 2: Parallel Data Retrieval"""
    service = ProgressiveStreamingService()

    query = "APX819"
    analysis = {"detected_products": ["APX819"]}

    results = []
    async for update in service.phase2_data_retrieval(query, analysis):
        results.append(update)

    phase_results = [r for r in results if r["type"] == "phase_result"]
    assert len(phase_results) == 1

    data = phase_results[0]["data"]
    assert "semantic_matches" in data
    assert "spec_data" in data

@pytest.mark.asyncio
async def test_context_truncation():
    """Test Phase 3: Context Truncation"""
    service = ProgressiveStreamingService()

    # Create mock products with large context
    large_products = [
        {f"field_{i}": "x" * 1000 for i in range(50)}
        for _ in range(20)
    ]

    truncated = service._truncate_context(
        large_products,
        max_tokens=5000
    )

    assert truncated["token_count"] < 5000
    assert truncated["truncation_applied"] == True
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_full_progressive_stream():
    """Test complete 5-phase streaming"""
    service = ProgressiveStreamingService()

    query = "推薦適合遊戲的筆電，預算 5 萬以內"

    phases_completed = []
    markdown_tokens = []

    async for update in service.chat_stream_progressive(query):
        if update["type"] == "phase_result":
            phases_completed.append(update["phase"])
        elif update["type"] == "markdown_token":
            markdown_tokens.append(update["token"])

    # Check all phases completed
    assert phases_completed == [1, 2, 3, 5]

    # Check markdown was generated
    assert len(markdown_tokens) > 0

    # Check markdown quality
    full_markdown = "".join(markdown_tokens)
    assert "##" in full_markdown  # Has headers
    assert "|" in full_markdown   # Has tables
```

### Performance Tests
```python
import time

@pytest.mark.asyncio
async def test_streaming_performance():
    """Test that streaming starts quickly"""
    service = ProgressiveStreamingService()

    query = "APX819 規格"

    start_time = time.time()
    first_token_time = None

    async for update in service.chat_stream_progressive(query):
        if update["type"] == "markdown_token" and first_token_time is None:
            first_token_time = time.time()
            break

    time_to_first_token = first_token_time - start_time

    # Should start streaming within 2 seconds
    assert time_to_first_token < 2.0
```

---

## 📊 Monitoring & Metrics

**Key Metrics to Track**:
```python
class StreamingMetrics:
    """Track streaming performance metrics"""

    def __init__(self):
        self.metrics = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_time_to_first_token": 0,
            "avg_total_time": 0,
            "phase_timings": {
                1: [],
                2: [],
                3: [],
                4: [],
                5: []
            },
            "error_count": 0
        }

    def record_query(self, phase_timings: Dict[int, float],
                    total_time: float, cache_hit: bool):
        """Record query metrics"""
        self.metrics["total_queries"] += 1

        if cache_hit:
            self.metrics["cache_hits"] += 1
        else:
            self.metrics["cache_misses"] += 1

        # Update average times
        for phase, timing in phase_timings.items():
            self.metrics["phase_timings"][phase].append(timing)

        # Update average total time
        current_avg = self.metrics["avg_total_time"]
        n = self.metrics["total_queries"]
        self.metrics["avg_total_time"] = (current_avg * (n-1) + total_time) / n

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        return {
            "total_queries": self.metrics["total_queries"],
            "cache_hit_rate": self.metrics["cache_hits"] / max(1, self.metrics["total_queries"]),
            "avg_total_time": self.metrics["avg_total_time"],
            "avg_phase_times": {
                phase: sum(times) / len(times) if times else 0
                for phase, times in self.metrics["phase_timings"].items()
            }
        }
```

---

## 🎯 Success Criteria

### User Experience
- ✅ 用戶在 **50ms** 內看到第一個進度更新
- ✅ 用戶在 **500ms** 內看到 Phase 1 結果
- ✅ 用戶在 **2s** 內開始看到 markdown 內容
- ✅ 完整回應在 **5-8s** 內完成（視複雜度）

### Performance
- ✅ Cache hit rate > **60%** for common queries
- ✅ Parallel retrieval reduces Phase 2 time by **40%**
- ✅ Context truncation keeps token usage < **100K tokens**
- ✅ Frontend rendering smooth at **60 FPS**

### Quality
- ✅ Markdown格式正確率 > **95%**
- ✅ 表格正確顯示率 > **90%**
- ✅ Error recovery提供 partial results > **80%** cases

---

## 🚦 Implementation Roadmap

### Week 1: Core Infrastructure
- [ ] Setup Redis cache layer
- [ ] Create phase processor base classes
- [ ] Implement token manager and context truncator
- [ ] Setup async DuckDB wrapper

### Week 2: Phase 1-3 Implementation
- [ ] Implement Phase 1: Query Understanding
- [ ] Implement Phase 2: Parallel Retrieval
- [ ] Implement Phase 3: Context Assembly
- [ ] Add caching for all phases

### Week 3: Phase 4-5 + Frontend
- [ ] Implement Phase 4: Streaming Generation
- [ ] Implement Phase 5: Post-processing
- [ ] Build Progressive Markdown Renderer (JavaScript)
- [ ] Integrate SSE with frontend

### Week 4: Testing & Optimization
- [ ] Write unit tests for all phases
- [ ] Write integration tests
- [ ] Performance testing and optimization
- [ ] User acceptance testing

---

## 📝 Next Steps

1. **Review this plan** with stakeholders
2. **Setup development environment** (Redis, testing framework)
3. **Create GitHub issues** for each implementation phase
4. **Start with Week 1 tasks** (infrastructure)

---

**Document Status**: ✅ Complete - Ready for Implementation
**Last Updated**: 2025-10-01
**Author**: Claude (SuperClaude)
**Next Review**: After Week 1 completion
