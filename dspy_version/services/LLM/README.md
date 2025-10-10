# LLMManager - DSPy LLM Singleton Manager

Thread-safe singleton LLM manager for DSPy integration with gpp-oss:20b via Ollama/llama.cpp backends.

## Features

✅ **Singleton Pattern**: Thread-safe with double-checked locking
✅ **Dual Backend**: Supports both Ollama (primary) and llama.cpp (optional)
✅ **DSPy Native**: First-class DSPy LM integration
✅ **Token-Aware**: Automatic token estimation and truncation
✅ **Async-Ready**: Full async/await support with streaming
✅ **Production-Grade**: Monitoring, retry logic, health checks
✅ **Connection Pooling**: Handle concurrent requests efficiently

---

## Installation

### Basic Installation
```bash
pip install -r requirements.txt
```

### Minimal Installation (Ollama only)
```bash
pip install dspy-ai ollama pydantic pyyaml python-dotenv aiohttp
```

### With llama.cpp Backend
```bash
pip install llama-cpp-python
```

---

## Quick Start

### 1. Basic Usage

```python
from dspy_version.services.LLM import LLMManager, OllamaConfig, LLMConfig

# Initialize manager
manager = LLMManager.get_instance(
    ollama_config=OllamaConfig(model_name="gpt-oss:20b"),
    llm_config=LLMConfig(temperature=0.3)
)

# Direct completion
response = manager.complete("What is artificial intelligence?")
print(response)
```

### 2. DSPy Integration

```python
import dspy
from dspy_version.services.LLM import LLMManager

# Initialize and configure DSPy
manager = LLMManager.get_instance()
dspy.settings.configure(lm=manager.get_lm())

# Define signature
class QA(dspy.Signature):
    question = dspy.InputField()
    answer = dspy.OutputField()

# Use predictor
qa = dspy.Predict(QA)
result = qa(question="What is machine learning?")
print(result.answer)
```

### 3. Async Completion

```python
import asyncio
from dspy_version.services.LLM import LLMManager

async def process_questions(questions):
    manager = LLMManager.get_instance()

    tasks = [
        manager.acomplete(f"Answer: {q}")
        for q in questions
    ]

    return await asyncio.gather(*tasks)

# Usage
questions = ["What is Python?", "What is JavaScript?"]
answers = asyncio.run(process_questions(questions))
```

### 4. Streaming

```python
import asyncio
from dspy_version.services.LLM import LLMManager

async def stream_response(prompt):
    manager = LLMManager.get_instance()

    async for chunk in manager.stream(prompt):
        print(chunk, end='', flush=True)
    print()

asyncio.run(stream_response("Tell me a story"))
```

---

## Configuration

### Method 1: Code Configuration

```python
from dspy_version.services.LLM import LLMManager, OllamaConfig, LLMConfig

manager = LLMManager.get_instance(
    ollama_config=OllamaConfig(
        base_url="http://localhost:11434",
        model_name="gpt-oss:20b",
        timeout=60,
        max_retries=3
    ),
    llm_config=LLMConfig(
        temperature=0.3,
        max_tokens=2048,
        top_p=0.9
    )
)
```

### Method 2: Environment Variables

```bash
# .env file
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_NAME=gpt-oss:20b
OLLAMA_TIMEOUT=60
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2048
```

```python
from dspy_version.services.LLM import LLMManager

manager = LLMManager.from_env()
```

### Method 3: YAML Configuration

```yaml
# config/llm_config.yaml
ollama:
  base_url: http://localhost:11434
  model_name: gpt-oss:20b
  timeout: 60
  max_retries: 3

llm:
  temperature: 0.3
  max_tokens: 2048
  top_p: 0.9
```

```python
from dspy_version.services.LLM import LLMManager

manager = LLMManager.from_config("config/llm_config.yaml")
```

---

## Advanced Features

### Token Management

```python
manager = LLMManager.get_instance()

# Estimate tokens
text = "Hello world"
tokens = manager.token_manager.estimate_tokens(text)
print(f"Estimated tokens: {tokens}")

# Safe completion with auto-truncation
long_prompt = "Explain AI. " * 1000
response = manager.safe_completion(
    prompt=long_prompt,
    reserve_output=2048,
    auto_truncate=True
)
```

### Health Checks

```python
manager = LLMManager.get_instance()

# Check backend health
if manager.health_check():
    print("Backend is healthy")
else:
    print("Backend is down")
    manager.reconnect()
```

### Monitoring

```python
manager = LLMManager.get_instance()

# Get statistics
stats = manager.get_stats()
print(f"Total requests: {stats.total_requests}")
print(f"Success rate: {stats.successful_requests / stats.total_requests * 100:.1f}%")
print(f"Avg latency: {stats.avg_latency_ms:.2f}ms")
```

### Reconfiguration

```python
from dspy_version.services.LLM import LLMManager, LLMConfig

manager = LLMManager.get_instance()

# Reconfigure at runtime (affects all users!)
manager.reconfigure(
    llm_config=LLMConfig(temperature=0.7, max_tokens=4096)
)
```

---

## RAG Pipeline Example

```python
import dspy
from dspy_version.services.LLM import LLMManager

# Initialize
manager = LLMManager.get_instance()
dspy.settings.configure(lm=manager.get_lm())

# Define RAG module
class RAG(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(
            "context, question -> answer"
        )

    def forward(self, context, question):
        return self.generate(
            context=context,
            question=question
        )

# Use RAG
rag = RAG()
context = "Python is a high-level programming language..."
result = rag(context=context, question="What is Python?")
print(result.answer)
```

---

## API Reference

### LLMManager

#### Class Methods
- `get_instance(ollama_config, llm_config, use_backend)` - Get singleton instance
- `from_env()` - Load config from environment variables
- `from_config(path)` - Load config from YAML file
- `reset_instance()` - Reset singleton (testing only)

#### Instance Methods
- `get_lm(**overrides)` - Get DSPy LM instance
- `complete(prompt, **kwargs)` - Synchronous completion
- `acomplete(prompt, **kwargs)` - Async completion
- `stream(prompt, **kwargs)` - Async streaming generator
- `safe_completion(prompt, reserve_output, auto_truncate)` - Token-safe completion
- `health_check()` - Check backend availability
- `reconnect()` - Reconnect to backend
- `reconfigure(ollama_config, llm_config)` - Update configuration
- `get_stats()` - Get usage statistics
- `reset_stats()` - Reset statistics

---

## Configuration Classes

### OllamaConfig
```python
@dataclass
class OllamaConfig:
    base_url: str = "http://localhost:11434"
    model_name: str = "gpt-oss:20b"
    timeout: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
```

### LLMConfig
```python
@dataclass
class LLMConfig:
    temperature: float = 0.3
    max_tokens: int = 2048
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: List[str] = []
```

---

## Exception Handling

```python
from dspy_version.services.LLM import (
    LLMManager,
    ConnectionError,
    TokenLimitExceededError,
    TimeoutError
)

manager = LLMManager.get_instance()

try:
    response = manager.complete("Your prompt")
except ConnectionError as e:
    print(f"Backend unavailable: {e}")
    manager.reconnect()
except TokenLimitExceededError as e:
    print(f"Prompt too long: {e}")
    # Use safe_completion with auto_truncate=True
except TimeoutError as e:
    print(f"Request timed out: {e}")
```

---

## Testing

### Unit Tests
```bash
pytest dspy_version/services/LLM/test_llm_manager.py -v
```

### Run Examples
```bash
python dspy_version/services/LLM/usage_example.py
```

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Initialization (first) | < 500ms |
| Singleton access (cached) | < 1ms |
| Completion (100 tokens) | < 2s |
| Concurrent requests | 10+ |
| Token estimation accuracy | ± 10% |

---

## Troubleshooting

### Issue: "Connection refused to Ollama"
**Solution**: Ensure Ollama is running
```bash
ollama serve
```

### Issue: "Model not found"
**Solution**: Pull the model
```bash
ollama pull gpt-oss:20b
```

### Issue: "Token limit exceeded"
**Solution**: Use safe_completion with auto_truncate
```python
response = manager.safe_completion(prompt, auto_truncate=True)
```

---

## Architecture

```
LLMManager (Singleton)
├── Configuration (OllamaConfig, LLMConfig)
├── Backend (Ollama / llama.cpp)
├── Token Manager (estimation, truncation)
├── Connection Pool (concurrent requests)
├── Metrics Collector (statistics)
└── Async Executor (async/await support)
```

---

## Migration from LangChain

**Old (LangChain)**:
```python
from libs.RAG.LLM.LLMInitializer import LLMInitializer

llm_init = LLMInitializer.get_instance()
llm = llm_init.get_llm()
```

**New (DSPy)**:
```python
from dspy_version.services.LLM import LLMManager

manager = LLMManager.get_instance()
lm = manager.get_lm()
```

---

## License

See project LICENSE file.

---

## Contributing

See [LLM_Layer_Design_dspy.md](LLM_Layer_Design_dspy.md) for design documentation.

---

## Support

For issues and questions, contact the development team.
