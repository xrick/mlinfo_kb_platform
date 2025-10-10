# dspy_version/services/LLM/config.py
"""
Configuration dataclasses for LLMManager
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class OllamaConfig:
    """Ollama server configuration"""
    base_url: str = "http://localhost:11434"
    model_name: str = "gpt-oss:20b"
    timeout: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0


@dataclass
class LlamaCppConfig:
    """llama.cpp backend configuration"""
    model_path: Optional[str] = None
    n_ctx: int = 131072           # Context window
    n_batch: int = 512            # Batch size
    n_threads: int = 8            # CPU threads
    use_mmap: bool = True         # Memory mapping
    use_mlock: bool = False       # Lock memory
    n_gpu_layers: int = 0         # GPU acceleration


@dataclass
class LLMConfig:
    """Unified LLM generation configuration"""
    temperature: float = 0.3
    max_tokens: int = 2048
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: List[str] = field(default_factory=list)
