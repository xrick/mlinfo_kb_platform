# dspy_version/services/LLM/__init__.py
"""
DSPy LLM Manager Module

Thread-safe singleton LLM manager for DSPy integration with gpp-oss:20b
via Ollama/llama.cpp backends.

Usage:
    from dspy_version.services.LLM import LLMManager, OllamaConfig, LLMConfig

    manager = LLMManager.get_instance(
        ollama_config=OllamaConfig(model_name="gpt-oss:20b"),
        llm_config=LLMConfig(temperature=0.3)
    )

    lm = manager.get_lm()
"""

from .config import OllamaConfig, LlamaCppConfig, LLMConfig
from .exceptions import (
    LLMManagerException,
    ConnectionError,
    ModelNotFoundError,
    TokenLimitExceededError,
    TimeoutError,
    ConfigurationError,
)

from .llm_manager import LLMManager

__all__ = [
    # Configuration
    "OllamaConfig",
    "LlamaCppConfig",
    "LLMConfig",
    # Exceptions
    "LLMManagerException",
    "ConnectionError",
    "ModelNotFoundError",
    "TokenLimitExceededError",
    "TimeoutError",
    "ConfigurationError",
    # Main class
    "LLMManager",
]

__version__ = "1.0.0"
