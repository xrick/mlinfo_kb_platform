# LLMManager Design Specification (DSPy Version)

**Version**: 1.0.0
**Date**: 2025-10-10
**Purpose**: Thread-safe singleton LLM manager for DSPy integration with gpp-oss:20b via Ollama/llama.cpp

---

## 1. Architecture Overview

```
dspy_version/services/LLM/
├── __init__.py              # Module exports
├── llm_manager.py           # Main LLMManager singleton
├── config.py                # Configuration dataclasses
├── exceptions.py            # Custom exceptions
└── usage_example.py         # Usage examples
```

### Design Principles

1. **Singleton Pattern**: Thread-safe single instance across the application
2. **Backend Abstraction**: Support both Ollama and llama.cpp transparently
3. **DSPy Native**: First-class DSPy LM integration
4. **Token-Aware**: Automatic token management and truncation
5. **Production-Ready**: Error handling, retries, monitoring, health checks
6. **Async-First**: Full async/await support for modern Python applications

---

## 2. Core Components

### 2.1 LLMManager (Singleton)

**Responsibilities**:
- Manage single LLM instance lifecycle
- Provide thread-safe access to DSPy LM
- Handle connection pooling and retry logic
- Monitor health and collect metrics
- Manage token budgets and context windows

**Singleton Pattern Implementation**:
```python
class LLMManager:
    """Thread-safe singleton LLM manager for DSPy"""

    # Class-level singleton management
    _instance: Optional['LLMManager'] = None
    _lock: threading.Lock = threading.Lock()
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        """Double-checked locking for thread safety"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, ollama_config=None, llm_config=None):
        """Initialize only once"""
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return
            # Initialization logic here
            self._initialized = True
```

**Key Methods**:
- `get_instance()`: Class method to get singleton instance
- `get_lm()`: Get DSPy LM instance
- `complete()`: Synchronous completion
- `acomplete()`: Async completion
- `stream()`: Async streaming
- `health_check()`: Check backend availability
- `reconnect()`: Reconnect to backend
- `reconfigure()`: Update configuration
- `reset_instance()`: Reset singleton (testing only)

---

### 2.2 Configuration Management

#### OllamaConfig
```python
@dataclass
class OllamaConfig:
    """Ollama server configuration"""
    base_url: str = "http://localhost:11434"
    model_name: str = "gpt-oss:20b"
    timeout: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
```

#### LlamaCppConfig
```python
@dataclass
class LlamaCppConfig:
    """llama.cpp backend configuration"""
    n_ctx: int = 131072           # Context window
    n_batch: int = 512            # Batch size
    n_threads: int = 8            # CPU threads
    use_mmap: bool = True         # Memory mapping
    use_mlock: bool = False       # Lock memory
    n_gpu_layers: int = 0         # GPU acceleration
```

#### LLMConfig
```python
@dataclass
class LLMConfig:
    """Unified LLM generation configuration"""
    temperature: float = 0.3
    max_tokens: int = 2048
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: List[str] = field(default_factory=list)
```

**Configuration Priority**:
1. Explicit constructor parameters
2. Environment variables
3. YAML configuration file
4. Default values

---

### 2.3 DSPy Integration

#### Ollama Backend (Primary)
```python
import dspy

# Use DSPy's built-in Ollama LM
lm = dspy.OllamaLocal(
    model='gpt-oss:20b',
    base_url='http://localhost:11434',
    timeout=60
)
```

#### llama.cpp Backend (Custom)
```python
class LlamaCppLM(dspy.LM):
    """Custom DSPy LM wrapper for llama.cpp"""

    def __init__(self, config: LlamaCppConfig):
        from llama_cpp import Llama

        self.llm = Llama(
            model_path=config.model_path,
            n_ctx=config.n_ctx,
            n_batch=config.n_batch,
            n_threads=config.n_threads,
            use_mmap=config.use_mmap,
            use_mlock=config.use_mlock,
            n_gpu_layers=config.n_gpu_layers
        )
        self.config = config

    def __call__(self, prompt: str, **kwargs) -> str:
        """Synchronous completion"""
        response = self.llm(
            prompt,
            max_tokens=kwargs.get('max_tokens', 2048),
            temperature=kwargs.get('temperature', 0.3),
            top_p=kwargs.get('top_p', 0.9)
        )
        return response['choices'][0]['text']

    async def agenerate(self, prompt: str, **kwargs) -> str:
        """Async completion (run in executor)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.__call__, prompt, **kwargs)
```

---

## 3. API Design

### 3.1 Initialization API

```python
# Method 1: Class method (recommended)
from dspy_version.services.LLM import LLMManager

manager = LLMManager.get_instance(
    ollama_config=OllamaConfig(
        base_url="http://localhost:11434",
        model_name="gpt-oss:20b"
    ),
    llm_config=LLMConfig(temperature=0.3, max_tokens=2048)
)

# Method 2: Direct instantiation (returns singleton)
manager = LLMManager()

# Method 3: From environment variables
manager = LLMManager.from_env()

# Method 4: From YAML config
manager = LLMManager.from_config("config/llm_config.yaml")
```

### 3.2 LLM Access API

```python
# Get DSPy LM instance
lm = manager.get_lm()

# Configure DSPy globally
import dspy
dspy.settings.configure(lm=manager.get_lm())

# Get with config override
lm = manager.get_lm(temperature=0.7, max_tokens=4096)

# Direct completion (synchronous)
response = manager.complete(prompt="What is artificial intelligence?")

# Async completion
response = await manager.acomplete(prompt="Explain machine learning")

# Streaming (async generator)
async for chunk in manager.stream(prompt="Tell me a story"):
    print(chunk, end='', flush=True)
```

### 3.3 Management API

```python
# Health check
is_healthy = manager.health_check()
# Returns: bool

# Reconnect to backend
manager.reconnect()

# Reconfigure (affects all users of singleton)
manager.reconfigure(
    ollama_config=OllamaConfig(timeout=120),
    llm_config=LLMConfig(temperature=0.5)
)

# Get statistics
stats = manager.get_stats()
# Returns: LLMStats(total_requests=100, avg_latency_ms=234.5, ...)

# Reset instance (testing only - destroys singleton)
LLMManager.reset_instance()
```

---

## 4. Error Handling

### Exception Hierarchy

```python
class LLMManagerException(Exception):
    """Base exception for all LLMManager errors"""
    pass

class ConnectionError(LLMManagerException):
    """Failed to connect to Ollama or llama.cpp backend"""
    pass

class ModelNotFoundError(LLMManagerException):
    """Requested model is not available"""
    pass

class TokenLimitExceededError(LLMManagerException):
    """Input prompt exceeds maximum token limit"""
    pass

class TimeoutError(LLMManagerException):
    """Request timed out"""
    pass

class ConfigurationError(LLMManagerException):
    """Invalid configuration parameters"""
    pass
```

### Retry Strategy

**Exponential Backoff**:
- Initial delay: 1 second
- Backoff multiplier: 2.0
- Max retries: 3 (configurable)
- Max delay: 16 seconds

**Retry Conditions**:
- ✅ Retry: Connection errors, timeouts, rate limits
- ❌ No retry: Model not found, invalid input, authentication errors

**Implementation**:
```python
def _retry_with_backoff(self, func, *args, **kwargs):
    """Execute function with exponential backoff retry"""
    delay = self.ollama_config.retry_delay

    for attempt in range(self.ollama_config.max_retries):
        try:
            return func(*args, **kwargs)
        except (ConnectionError, TimeoutError) as e:
            if attempt == self.ollama_config.max_retries - 1:
                raise
            logger.warning(f"Attempt {attempt+1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= self.ollama_config.retry_backoff
```

---

## 5. Token Management

### TokenManager Class

```python
class TokenManager:
    """Token estimation and truncation utilities"""

    # Context window limits by model
    MODEL_CONTEXT_LIMITS = {
        "gpt-oss:20b": 131072,
        "default": 8192
    }

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count using character-based heuristic
        - ASCII (English/symbols): ~4 chars per token
        - Non-ASCII (CJK): ~2 chars per token
        """
        if not text:
            return 0
        ascii_count = sum(1 for ch in text if ord(ch) < 128)
        non_ascii_count = len(text) - ascii_count
        est = ascii_count / 4.0 + non_ascii_count / 2.0
        return int(est) + 1  # Conservative rounding

    @staticmethod
    def truncate_to_tokens(text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token budget
        Conservative estimate: 2 chars per token
        """
        if max_tokens <= 0 or not text:
            return ""
        char_budget = max_tokens * 2
        if len(text) <= char_budget:
            return text
        return text[:char_budget]

    def safe_completion(
        self,
        prompt: str,
        reserve_output: int = 2048,
        auto_truncate: bool = True,
        min_output: int = 64
    ) -> str:
        """
        Safe completion with automatic token management

        Args:
            prompt: Input text
            reserve_output: Desired output token budget
            auto_truncate: Auto-truncate input if needed
            min_output: Minimum output tokens

        Returns:
            Generated text

        Raises:
            TokenLimitExceededError: If prompt too long and auto_truncate=False
        """
        # 1. Estimate input tokens
        prompt_tokens = self.estimate_tokens(prompt)

        # 2. Calculate available output space
        max_ctx = self.MODEL_CONTEXT_LIMITS.get(
            self.ollama_config.model_name,
            self.MODEL_CONTEXT_LIMITS["default"]
        )
        available_output = max_ctx - prompt_tokens

        # 3. Truncate if necessary
        if available_output < min_output:
            if not auto_truncate:
                raise TokenLimitExceededError(
                    f"Prompt uses {prompt_tokens} tokens, only {available_output} left"
                )

            need_output = max(reserve_output, min_output)
            target_prompt_tokens = max(max_ctx - need_output, 0)
            prompt = self.truncate_to_tokens(prompt, target_prompt_tokens)
            prompt_tokens = self.estimate_tokens(prompt)
            available_output = max_ctx - prompt_tokens

        # 4. Calculate final max_tokens
        final_max_tokens = max(
            min(reserve_output, max(available_output, 0)),
            min_output
        )

        # 5. Call LLM with computed max_tokens
        return self.complete(prompt, max_tokens=final_max_tokens)
```

---

## 6. Concurrency & Performance

### 6.1 Thread Safety

**Singleton Protection**:
- `threading.Lock()` for instance creation
- Double-checked locking pattern
- Separate locks for config updates

**Thread-Local Storage** (optional):
```python
import threading

class LLMManager:
    _thread_local = threading.local()

    def _get_thread_lm(self):
        """Get or create thread-local LM instance"""
        if not hasattr(self._thread_local, 'lm'):
            self._thread_local.lm = self._create_lm()
        return self._thread_local.lm
```

### 6.2 Connection Pooling

```python
from queue import Queue

class ConnectionPool:
    """Manage pool of LM instances for concurrent requests"""

    def __init__(self, factory_func, size: int = 5):
        self._factory = factory_func
        self._pool: Queue = Queue(maxsize=size)
        self._size = size
        self._created = 0
        self._lock = threading.Lock()

    def acquire(self):
        """Get LM from pool or create new if under limit"""
        try:
            return self._pool.get_nowait()
        except:
            with self._lock:
                if self._created < self._size:
                    self._created += 1
                    return self._factory()
            # Wait for available instance
            return self._pool.get()

    def release(self, lm):
        """Return LM to pool"""
        try:
            self._pool.put_nowait(lm)
        except:
            pass  # Pool full, discard
```

### 6.3 Async Support

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class LLMManager:
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=5)

    async def acomplete(self, prompt: str, **kwargs) -> str:
        """Async completion using executor"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self.complete,
            prompt,
            **kwargs
        )

    async def stream(self, prompt: str, **kwargs):
        """Async streaming generator"""
        lm = self.get_lm()

        # If DSPy LM supports streaming
        if hasattr(lm, 'stream'):
            async for chunk in lm.stream(prompt, **kwargs):
                yield chunk
        else:
            # Fallback: simulate streaming by chunking output
            response = await self.acomplete(prompt, **kwargs)
            for chunk in self._chunk_response(response, chunk_size=10):
                await asyncio.sleep(0.01)  # Simulate streaming delay
                yield chunk
```

---

## 7. Monitoring & Logging

### 7.1 Metrics Collection

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

@dataclass
class LLMStats:
    """Statistics for LLM usage"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    last_request_time: Optional[datetime] = None
    error_counts: dict = field(default_factory=dict)

    def record_success(self, latency_ms: float, tokens: int):
        """Record successful request"""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_tokens += tokens
        self.total_latency_ms += latency_ms
        self.avg_latency_ms = self.total_latency_ms / self.successful_requests
        self.last_request_time = datetime.now()

    def record_failure(self, error_type: str):
        """Record failed request"""
        self.total_requests += 1
        self.failed_requests += 1
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        self.last_request_time = datetime.now()


class MetricsCollector:
    """Collect and aggregate LLM metrics"""

    def __init__(self):
        self.stats = LLMStats()
        self._lock = threading.Lock()

    def record_request(
        self,
        latency_ms: float,
        tokens: int = 0,
        success: bool = True,
        error_type: str = None
    ):
        """Thread-safe metric recording"""
        with self._lock:
            if success:
                self.stats.record_success(latency_ms, tokens)
            else:
                self.stats.record_failure(error_type or "unknown")

    def get_summary(self) -> LLMStats:
        """Get snapshot of current stats"""
        with self._lock:
            return LLMStats(**vars(self.stats))

    def reset(self):
        """Reset all statistics"""
        with self._lock:
            self.stats = LLMStats()
```

### 7.2 Logging Strategy

```python
import logging

logger = logging.getLogger(__name__)

# Log levels and usage:
# - DEBUG: Request/response details, token counts
# - INFO: Initialization, configuration changes, health checks
# - WARNING: Retries, performance degradation, token truncation
# - ERROR: Connection failures, API errors
# - CRITICAL: Singleton corruption, unrecoverable errors

# Example logging in LLMManager:
class LLMManager:
    def __init__(self):
        logger.info(f"Initializing LLMManager singleton")
        logger.debug(f"Config: {self.ollama_config}")

    def complete(self, prompt: str) -> str:
        start = time.time()
        logger.debug(f"Completion request: {len(prompt)} chars")

        try:
            response = self._lm(prompt)
            latency = (time.time() - start) * 1000
            logger.info(f"Completion successful: {latency:.2f}ms")
            return response
        except Exception as e:
            logger.error(f"Completion failed: {e}", exc_info=True)
            raise
```

---

## 8. Usage Patterns

### 8.1 Basic DSPy Integration

```python
import dspy
from dspy_version.services.LLM import LLMManager

# Initialize manager
manager = LLMManager.get_instance(
    ollama_config=OllamaConfig(model_name="gpt-oss:20b"),
    llm_config=LLMConfig(temperature=0.3)
)

# Configure DSPy globally
dspy.settings.configure(lm=manager.get_lm())

# Use with DSPy signatures
class QA(dspy.Signature):
    """Answer questions based on context"""
    question = dspy.InputField()
    answer = dspy.OutputField()

# Use DSPy modules
qa_module = dspy.Predict(QA)
result = qa_module(question="What is machine learning?")
print(result.answer)
```

### 8.2 RAG Pipeline

```python
import dspy
from dspy_version.services.LLM import LLMManager

# Initialize with RAG-optimized settings
manager = LLMManager.get_instance(
    llm_config=LLMConfig(
        temperature=0.1,  # Lower for factual responses
        max_tokens=4096
    )
)

dspy.settings.configure(lm=manager.get_lm())

# Define RAG module
class RAG(dspy.Module):
    def __init__(self, num_passages=5):
        super().__init__()
        self.retrieve = dspy.Retrieve(k=num_passages)
        self.generate = dspy.ChainOfThought("context, question -> answer")

    def forward(self, question):
        context = self.retrieve(question).passages
        answer = self.generate(context=context, question=question)
        return answer

# Use RAG
rag = RAG(num_passages=5)
response = rag(question="How does attention mechanism work?")
```

### 8.3 Async Batch Processing

```python
import asyncio
from dspy_version.services.LLM import LLMManager

async def process_questions(questions: List[str]):
    """Process multiple questions concurrently"""
    manager = LLMManager.get_instance()

    tasks = [
        manager.acomplete(f"Answer this question: {q}")
        for q in questions
    ]

    results = await asyncio.gather(*tasks)
    return results

# Usage
questions = [
    "What is AI?",
    "Explain neural networks",
    "What is deep learning?"
]
answers = asyncio.run(process_questions(questions))
```

### 8.4 Streaming Responses

```python
import asyncio
from dspy_version.services.LLM import LLMManager

async def stream_response(prompt: str):
    """Stream LLM response in real-time"""
    manager = LLMManager.get_instance()

    print("Response: ", end='', flush=True)
    async for chunk in manager.stream(prompt):
        print(chunk, end='', flush=True)
    print()  # Newline

# Usage
asyncio.run(stream_response("Tell me a short story about AI"))
```

---

## 9. Configuration Files

### 9.1 Environment Variables (.env)

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_NAME=gpt-oss:20b
OLLAMA_TIMEOUT=60
OLLAMA_MAX_RETRIES=3
OLLAMA_RETRY_DELAY=1.0
OLLAMA_RETRY_BACKOFF=2.0

# LLM Generation Parameters
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2048
LLM_TOP_P=0.9
LLM_FREQUENCY_PENALTY=0.0
LLM_PRESENCE_PENALTY=0.0

# llama.cpp Configuration (if using)
LLAMA_CPP_N_CTX=131072
LLAMA_CPP_N_BATCH=512
LLAMA_CPP_N_THREADS=8
LLAMA_CPP_USE_MMAP=true
LLAMA_CPP_USE_MLOCK=false
LLAMA_CPP_N_GPU_LAYERS=0
```

### 9.2 YAML Configuration (config/llm_config.yaml)

```yaml
ollama:
  base_url: http://localhost:11434
  model_name: gpt-oss:20b
  timeout: 60
  max_retries: 3
  retry_delay: 1.0
  retry_backoff: 2.0

llama_cpp:
  n_ctx: 131072
  n_batch: 512
  n_threads: 8
  use_mmap: true
  use_mlock: false
  n_gpu_layers: 0

llm:
  temperature: 0.3
  max_tokens: 2048
  top_p: 0.9
  frequency_penalty: 0.0
  presence_penalty: 0.0
  stop_sequences: []
```

### 9.3 Loading Configuration

```python
import os
import yaml
from pathlib import Path

class LLMManager:
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        ollama_config = OllamaConfig(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model_name=os.getenv("OLLAMA_MODEL_NAME", "gpt-oss:20b"),
            timeout=int(os.getenv("OLLAMA_TIMEOUT", "60")),
            max_retries=int(os.getenv("OLLAMA_MAX_RETRIES", "3")),
        )

        llm_config = LLMConfig(
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2048")),
            top_p=float(os.getenv("LLM_TOP_P", "0.9")),
        )

        return cls.get_instance(
            ollama_config=ollama_config,
            llm_config=llm_config
        )

    @classmethod
    def from_config(cls, config_path: str):
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        ollama_config = OllamaConfig(**config.get('ollama', {}))
        llm_config = LLMConfig(**config.get('llm', {}))

        return cls.get_instance(
            ollama_config=ollama_config,
            llm_config=llm_config
        )
```

---

## 10. Testing Strategy

### 10.1 Unit Tests

```python
import pytest
import threading
from dspy_version.services.LLM import LLMManager

class TestLLMManager:
    """Unit tests for LLMManager"""

    def setup_method(self):
        """Reset singleton before each test"""
        LLMManager.reset_instance()

    def test_singleton_pattern(self):
        """Verify only one instance exists"""
        manager1 = LLMManager.get_instance()
        manager2 = LLMManager.get_instance()
        assert manager1 is manager2

    def test_thread_safety(self):
        """Test concurrent access to singleton"""
        instances = []

        def create_instance():
            instances.append(LLMManager.get_instance())

        threads = [threading.Thread(target=create_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All instances should be the same
        assert all(inst is instances[0] for inst in instances)

    def test_initialization_once(self):
        """Verify initialization happens only once"""
        manager = LLMManager.get_instance()
        original_lm = manager._lm

        # Get instance again
        manager2 = LLMManager.get_instance()

        # Should be same instance and same LM
        assert manager2 is manager
        assert manager2._lm is original_lm

    def test_token_estimation(self):
        """Test token counting accuracy"""
        manager = LLMManager.get_instance()

        # ASCII text
        ascii_text = "Hello world"  # ~2-3 tokens
        tokens = manager.token_manager.estimate_tokens(ascii_text)
        assert 2 <= tokens <= 4

        # CJK text
        cjk_text = "你好世界"  # ~4 tokens
        tokens = manager.token_manager.estimate_tokens(cjk_text)
        assert 3 <= tokens <= 5

    def test_token_truncation(self):
        """Test text truncation"""
        manager = LLMManager.get_instance()

        long_text = "A" * 1000
        truncated = manager.token_manager.truncate_to_tokens(long_text, 50)

        # Should be truncated
        assert len(truncated) < len(long_text)
        assert len(truncated) <= 100  # ~50 tokens * 2 chars

    @pytest.mark.asyncio
    async def test_async_completion(self):
        """Test async completion"""
        manager = LLMManager.get_instance()
        response = await manager.acomplete("Test prompt")
        assert isinstance(response, str)
        assert len(response) > 0

    def test_reconfigure(self):
        """Test runtime reconfiguration"""
        manager = LLMManager.get_instance()
        original_temp = manager.llm_config.temperature

        manager.reconfigure(
            llm_config=LLMConfig(temperature=0.7)
        )

        assert manager.llm_config.temperature == 0.7
        assert manager.llm_config.temperature != original_temp

    def test_metrics_collection(self):
        """Test statistics tracking"""
        manager = LLMManager.get_instance()

        # Make some requests
        manager.complete("Test 1")
        manager.complete("Test 2")

        stats = manager.get_stats()
        assert stats.total_requests >= 2
        assert stats.successful_requests >= 2
```

### 10.2 Integration Tests

```python
import pytest
from dspy_version.services.LLM import LLMManager

class TestIntegration:
    """Integration tests with real backends"""

    @pytest.mark.integration
    def test_ollama_connection(self):
        """Test connection to Ollama server"""
        manager = LLMManager.get_instance(
            ollama_config=OllamaConfig(
                base_url="http://localhost:11434",
                model_name="gpt-oss:20b"
            )
        )

        # Health check
        assert manager.health_check() is True

        # Simple completion
        response = manager.complete("Say 'hello'")
        assert len(response) > 0

    @pytest.mark.integration
    def test_dspy_module_integration(self):
        """Test integration with DSPy modules"""
        import dspy

        manager = LLMManager.get_instance()
        dspy.settings.configure(lm=manager.get_lm())

        # Define simple signature
        class Sentiment(dspy.Signature):
            text = dspy.InputField()
            sentiment = dspy.OutputField()

        # Use with predictor
        classifier = dspy.Predict(Sentiment)
        result = classifier(text="I love this!")

        assert result.sentiment in ['positive', 'negative', 'neutral']

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling concurrent requests"""
        import asyncio

        manager = LLMManager.get_instance()

        # Send 10 concurrent requests
        tasks = [
            manager.acomplete(f"Question {i}")
            for i in range(10)
        ]

        responses = await asyncio.gather(*tasks)

        assert len(responses) == 10
        assert all(len(r) > 0 for r in responses)
```

### 10.3 Performance Tests

```python
import time
import pytest

class TestPerformance:
    """Performance benchmarks"""

    def test_singleton_access_speed(self, benchmark):
        """Benchmark singleton access time"""
        def access():
            return LLMManager.get_instance()

        result = benchmark(access)
        # Should be < 1ms for cached singleton
        assert benchmark.stats['mean'] < 0.001

    def test_completion_latency(self):
        """Measure completion latency"""
        manager = LLMManager.get_instance()

        start = time.time()
        response = manager.complete("Test" * 50)  # ~100 tokens
        latency = time.time() - start

        # Should complete within 2 seconds for 100 tokens
        assert latency < 2.0

    @pytest.mark.asyncio
    async def test_async_throughput(self):
        """Measure async throughput"""
        import asyncio

        manager = LLMManager.get_instance()

        start = time.time()
        tasks = [
            manager.acomplete("Short prompt")
            for _ in range(10)
        ]
        await asyncio.gather(*tasks)
        duration = time.time() - start

        # 10 requests should complete concurrently faster than serial
        assert duration < 10.0  # Not 10x serial time
```

---

## 11. Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] Create `dspy_version/services/LLM/` directory
- [ ] Implement `config.py` with dataclasses
  - [ ] OllamaConfig
  - [ ] LlamaCppConfig
  - [ ] LLMConfig
- [ ] Implement `exceptions.py`
  - [ ] LLMManagerException (base)
  - [ ] ConnectionError
  - [ ] ModelNotFoundError
  - [ ] TokenLimitExceededError
  - [ ] TimeoutError
  - [ ] ConfigurationError
- [ ] Create `__init__.py` with exports

### Phase 2: Singleton Manager
- [ ] Implement `LLMManager` class in `llm_manager.py`
- [ ] Add `__new__()` with double-checked locking
- [ ] Add `__init__()` with lazy initialization guard
- [ ] Implement `get_instance()` class method
- [ ] Implement `reset_instance()` class method (testing)
- [ ] Add thread-safe reconfiguration
- [ ] Add `from_env()` class method
- [ ] Add `from_config()` class method

### Phase 3: LLM Backends
- [ ] Integrate DSPy Ollama LM (primary backend)
  - [ ] Import `dspy.OllamaLocal`
  - [ ] Configure with OllamaConfig
  - [ ] Add connection retry logic
- [ ] Implement custom `LlamaCppLM` wrapper (optional)
  - [ ] Inherit from `dspy.LM`
  - [ ] Implement `__call__()` method
  - [ ] Implement `agenerate()` async method
- [ ] Add backend selection logic
- [ ] Implement `health_check()` method
- [ ] Implement `reconnect()` method

### Phase 4: Token Management
- [ ] Create `TokenManager` class
- [ ] Port `estimate_tokens()` from LangChain version
- [ ] Implement `truncate_to_tokens()` method
- [ ] Add `safe_completion()` with auto-truncation
- [ ] Add context window validation
- [ ] Integrate token budget tracking with metrics

### Phase 5: Async & Concurrency
- [ ] Implement `acomplete()` async method
- [ ] Implement `stream()` async generator
- [ ] Add `ConnectionPool` class
  - [ ] `acquire()` method
  - [ ] `release()` method
  - [ ] Size limit enforcement
- [ ] Add thread-local storage (optional)
- [ ] Create `ThreadPoolExecutor` for sync-to-async

### Phase 6: Monitoring
- [ ] Implement `LLMStats` dataclass
  - [ ] Request counters
  - [ ] Latency tracking
  - [ ] Token usage
  - [ ] Error counts
- [ ] Implement `MetricsCollector` class
  - [ ] `record_request()` method
  - [ ] `get_summary()` method
  - [ ] `reset()` method
- [ ] Add logging integration
  - [ ] INFO: initialization, config changes
  - [ ] DEBUG: request/response details
  - [ ] WARNING: retries, truncation
  - [ ] ERROR: failures
- [ ] Implement `get_stats()` in LLMManager

### Phase 7: Testing & Documentation
- [ ] Write unit tests (`test_llm_manager.py`)
  - [ ] test_singleton_pattern
  - [ ] test_thread_safety
  - [ ] test_initialization_once
  - [ ] test_token_estimation
  - [ ] test_token_truncation
  - [ ] test_async_completion
  - [ ] test_reconfigure
  - [ ] test_metrics_collection
- [ ] Write integration tests
  - [ ] test_ollama_connection
  - [ ] test_dspy_module_integration
  - [ ] test_concurrent_requests
- [ ] Create `usage_example.py`
  - [ ] Basic initialization
  - [ ] DSPy integration
  - [ ] RAG pipeline
  - [ ] Async batch processing
  - [ ] Streaming
- [ ] Add docstrings & type hints
- [ ] Update main README

---

## 12. Dependencies

### Required Packages

```txt
# Core DSPy
dspy-ai >= 2.4.0

# LLM Backends
ollama >= 0.1.0
llama-cpp-python >= 0.2.0

# Configuration
pydantic >= 2.0.0
pyyaml >= 6.0
python-dotenv >= 1.0.0

# Async Support
aiohttp >= 3.9.0

# Testing
pytest >= 7.4.0
pytest-asyncio >= 0.21.0
pytest-benchmark >= 4.0.0
```

### Installation

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install individually
pip install dspy-ai ollama llama-cpp-python pydantic pyyaml python-dotenv aiohttp pytest pytest-asyncio
```

---

## 13. Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Initialization (first call) | < 500ms | Creating LM instance |
| Singleton access (cached) | < 1ms | Subsequent calls |
| Completion latency (100 tokens) | < 2s | gpt-oss:20b on GPU |
| Concurrent requests | 10+ | With connection pool |
| Token estimation accuracy | ± 10% | vs actual tokenizer |
| Memory overhead | < 50MB | Per singleton instance |
| Retry delay (first) | 1s | Exponential backoff |
| Max retry delay | 16s | After 4 retries |

---

## 14. Security Considerations

1. **API Key Management**
   - Never hardcode credentials
   - Use environment variables or secure vaults
   - Rotate keys regularly

2. **Input Validation**
   - Sanitize prompts before sending to LLM
   - Validate max_tokens parameter
   - Check for injection attacks

3. **Rate Limiting**
   - Implement request throttling
   - Track per-user quotas
   - Add circuit breaker for failures

4. **Timeout Protection**
   - Set reasonable timeouts (default 60s)
   - Prevent resource exhaustion
   - Cancel stuck requests

5. **Error Information**
   - Don't leak internal details in errors
   - Log sensitive info only to secure logs
   - Sanitize exception messages

6. **Connection Security**
   - Use HTTPS for remote Ollama
   - Validate SSL certificates
   - Encrypt sensitive data in transit

---

## 15. Future Enhancements

### Short-term (v1.1)
- [ ] Add prompt caching with Redis integration
- [ ] Support multiple model instances (multi-model manager)
- [ ] Add request queuing for rate limiting
- [ ] Implement circuit breaker pattern
- [ ] Add telemetry export (Prometheus format)

### Medium-term (v1.2)
- [ ] Dynamic model loading/unloading
- [ ] Fine-tuning integration (LoRA adapters)
- [ ] A/B testing support (model comparison)
- [ ] Advanced retry strategies (jitter, backpressure)
- [ ] WebSocket streaming for real-time UIs

### Long-term (v2.0)
- [ ] Multi-backend load balancing
- [ ] Distributed LLM inference (ray/celery)
- [ ] Model registry service
- [ ] Automatic failover to backup models
- [ ] Cost optimization (model routing by complexity)

---

## 16. Migration Guide

### From LangChain LLMInitializer to DSPy LLMManager

**Step 1: Install Dependencies**
```bash
pip install dspy-ai
```

**Step 2: Update Imports**
```python
# Old (LangChain)
from libs.RAG.LLM.LLMInitializer import LLMInitializer

# New (DSPy)
from dspy_version.services.LLM import LLMManager
```

**Step 3: Update Initialization**
```python
# Old
llm_init = LLMInitializer.get_instance(
    model_name="gpt-oss:20b",
    temperature=0.3
)
llm = llm_init.get_llm()

# New
manager = LLMManager.get_instance(
    ollama_config=OllamaConfig(model_name="gpt-oss:20b"),
    llm_config=LLMConfig(temperature=0.3)
)
lm = manager.get_lm()
```

**Step 4: Migrate LangChain Chains to DSPy Modules**
```python
# Old (LangChain)
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

prompt = PromptTemplate(template="Question: {question}\nAnswer:")
chain = LLMChain(llm=llm, prompt=prompt)
response = chain.run(question="What is AI?")

# New (DSPy)
import dspy

dspy.settings.configure(lm=manager.get_lm())

class QA(dspy.Signature):
    question = dspy.InputField()
    answer = dspy.OutputField()

qa = dspy.Predict(QA)
response = qa(question="What is AI?").answer
```

**Step 5: Update Configuration**
```python
# Old
llm_init.reconfigure(temperature=0.5)

# New
manager.reconfigure(llm_config=LLMConfig(temperature=0.5))
```

**Step 6: Update Async Calls**
```python
# Old
response = await asyncio.to_thread(llm.invoke, prompt)

# New
response = await manager.acomplete(prompt)
```

---

## 17. Troubleshooting

### Common Issues

**Issue 1: "Connection refused to Ollama"**
```
Error: ConnectionError: Failed to connect to http://localhost:11434
```
**Solution**:
- Verify Ollama is running: `ollama serve`
- Check port: `curl http://localhost:11434/api/tags`
- Update `base_url` in config

**Issue 2: "Model not found"**
```
Error: ModelNotFoundError: Model 'gpt-oss:20b' not available
```
**Solution**:
- Pull model: `ollama pull gpt-oss:20b`
- List models: `ollama list`
- Verify model name matches exactly

**Issue 3: "Token limit exceeded"**
```
Error: TokenLimitExceededError: Prompt uses 140000 tokens, exceeds 131072 limit
```
**Solution**:
- Enable auto-truncation: `safe_completion(prompt, auto_truncate=True)`
- Reduce prompt length manually
- Increase `reserve_output` to allow more truncation

**Issue 4: "Singleton already initialized with different config"**
```
Warning: LLMManager already initialized, reconfigure() affects all users
```
**Solution**:
- This is expected singleton behavior
- Use `reconfigure()` carefully in production
- For testing, use `reset_instance()` between tests

**Issue 5: "Async completion hangs"**
```
Task hangs indefinitely on await manager.acomplete()
```
**Solution**:
- Check timeout settings: `ollama_config.timeout`
- Verify Ollama server is responsive
- Look for deadlocks in connection pool

---

## 18. API Reference Summary

### LLMManager

```python
class LLMManager:
    # Class Methods
    @classmethod
    def get_instance(cls, ollama_config=None, llm_config=None) -> 'LLMManager'
    @classmethod
    def from_env(cls) -> 'LLMManager'
    @classmethod
    def from_config(cls, config_path: str) -> 'LLMManager'
    @classmethod
    def reset_instance(cls) -> None

    # Instance Methods
    def get_lm(self, **overrides) -> dspy.LM
    def complete(self, prompt: str, **kwargs) -> str
    async def acomplete(self, prompt: str, **kwargs) -> str
    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]
    def health_check(self) -> bool
    def reconnect(self) -> None
    def reconfigure(self, ollama_config=None, llm_config=None) -> None
    def get_stats(self) -> LLMStats

    # Token Management
    def safe_completion(self, prompt: str, reserve_output: int = 2048,
                       auto_truncate: bool = True) -> str
```

---

## 19. Appendix

### A. Context Window Sizes

| Model | Context Window | Notes |
|-------|----------------|-------|
| gpt-oss:20b | 131,072 tokens | Default for this implementation |
| deepseek-r1:7b | 131,072 tokens | Same as gpt-oss |
| llama3:8b | 8,192 tokens | Standard Llama3 |
| mistral:7b | 32,768 tokens | Extended context |

### B. Token Estimation Formula

**ASCII Characters (English, symbols)**:
```
tokens ≈ character_count / 4
```

**Non-ASCII (CJK, emoji)**:
```
tokens ≈ character_count / 2
```

**Mixed Text**:
```
tokens ≈ (ascii_chars / 4) + (non_ascii_chars / 2) + 1
```

### C. Environment Setup

**Development Setup**:
```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull model
ollama pull gpt-oss:20b

# 3. Start Ollama server
ollama serve

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Set environment variables
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL_NAME=gpt-oss:20b
```

**Production Setup**:
```bash
# Use systemd service for Ollama
sudo systemctl enable ollama
sudo systemctl start ollama

# Configure with YAML instead of env vars
cp config/llm_config.example.yaml config/llm_config.yaml
vim config/llm_config.yaml
```

---

## 20. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-10 | Initial design specification |
| | | - Singleton pattern with DSPy integration |
| | | - Ollama + llama.cpp backend support |
| | | - Token management and auto-truncation |
| | | - Async/streaming support |
| | | - Monitoring and metrics |

---

**End of Design Document**
