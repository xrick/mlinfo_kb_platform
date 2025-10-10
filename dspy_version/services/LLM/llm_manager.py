# dspy_version/services/LLM/llm_manager.py
"""
Thread-Safe Singleton LLM Manager for DSPy

Provides unified interface for connecting to gpp-oss:20b via Ollama/llama.cpp
with token management, async support, and monitoring.
"""

import logging
import threading
import time
import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from queue import Queue
import os

try:
    import dspy
except ImportError:
    raise ImportError(
        "DSPy is required. Install with: pip install dspy-ai"
    )

from .config import OllamaConfig, LlamaCppConfig, LLMConfig
from .exceptions import (
    LLMManagerException,
    ConnectionError,
    ModelNotFoundError,
    TokenLimitExceededError,
    TimeoutError,
    ConfigurationError,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Metrics & Statistics
# ============================================================================

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
    error_counts: Dict[str, int] = field(default_factory=dict)

    def record_success(self, latency_ms: float, tokens: int = 0):
        """Record successful request"""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_tokens += tokens
        self.total_latency_ms += latency_ms
        if self.successful_requests > 0:
            self.avg_latency_ms = self.total_latency_ms / self.successful_requests
        self.last_request_time = datetime.now()

    def record_failure(self, error_type: str):
        """Record failed request"""
        self.total_requests += 1
        self.failed_requests += 1
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        self.last_request_time = datetime.now()


class MetricsCollector:
    """Thread-safe metrics collector"""

    def __init__(self):
        self.stats = LLMStats()
        self._lock = threading.Lock()

    def record_request(
        self,
        latency_ms: float,
        tokens: int = 0,
        success: bool = True,
        error_type: Optional[str] = None
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
            # Create a copy to avoid race conditions
            return LLMStats(
                total_requests=self.stats.total_requests,
                successful_requests=self.stats.successful_requests,
                failed_requests=self.stats.failed_requests,
                total_tokens=self.stats.total_tokens,
                total_latency_ms=self.stats.total_latency_ms,
                avg_latency_ms=self.stats.avg_latency_ms,
                last_request_time=self.stats.last_request_time,
                error_counts=self.stats.error_counts.copy()
            )

    def reset(self):
        """Reset all statistics"""
        with self._lock:
            self.stats = LLMStats()


# ============================================================================
# Token Management
# ============================================================================

class TokenManager:
    """Token estimation and truncation utilities"""

    # Context window limits by model
    MODEL_CONTEXT_LIMITS = {
        "gpt-oss:20b": 131072,
        "deepseek-r1:7b": 131072,
        "llama3:8b": 8192,
        "mistral:7b": 32768,
        "default": 8192
    }

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.max_context_tokens = self.MODEL_CONTEXT_LIMITS.get(
            model_name,
            self.MODEL_CONTEXT_LIMITS["default"]
        )

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


# ============================================================================
# Connection Pool
# ============================================================================

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
                    logger.debug(f"Creating new LM instance ({self._created}/{self._size})")
                    return self._factory()
            # Wait for available instance
            logger.debug("Waiting for available LM instance from pool")
            return self._pool.get()

    def release(self, lm):
        """Return LM to pool"""
        try:
            self._pool.put_nowait(lm)
        except:
            logger.debug("Pool full, discarding LM instance")
            pass  # Pool full, discard


# ============================================================================
# Main LLMManager Class
# ============================================================================

class LLMManager:
    """
    Thread-safe singleton LLM manager for DSPy

    Features:
    - Singleton pattern with thread-safe initialization
    - DSPy LM integration (Ollama primary, llama.cpp optional)
    - Token management and auto-truncation
    - Async/streaming support
    - Connection pooling
    - Monitoring and metrics
    - Health checks and auto-retry
    """

    # Class-level singleton management
    _instance: Optional['LLMManager'] = None
    _lock: threading.Lock = threading.Lock()
    _initialized: bool = False

    # Context window limits
    MODEL_CONTEXT_LIMITS = TokenManager.MODEL_CONTEXT_LIMITS

    def __new__(cls, *args, **kwargs):
        """Double-checked locking for thread safety"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    logger.debug("Creating new LLMManager singleton instance")
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        ollama_config: Optional[OllamaConfig] = None,
        llama_cpp_config: Optional[LlamaCppConfig] = None,
        llm_config: Optional[LLMConfig] = None,
        use_backend: str = "ollama"  # "ollama" or "llama_cpp"
    ):
        """
        Initialize LLMManager (only once due to singleton)

        Args:
            ollama_config: Ollama server configuration
            llama_cpp_config: llama.cpp configuration (optional)
            llm_config: LLM generation parameters
            use_backend: Backend to use ("ollama" or "llama_cpp")
        """
        # Prevent re-initialization
        if self._initialized:
            logger.debug("LLMManager already initialized, skipping re-initialization")
            return

        with self._lock:
            if self._initialized:
                return

            logger.info("Initializing LLMManager singleton")

            # Configuration
            self.ollama_config = ollama_config or OllamaConfig()
            self.llama_cpp_config = llama_cpp_config or LlamaCppConfig()
            self.llm_config = llm_config or LLMConfig()
            self.use_backend = use_backend

            # Token management
            self.token_manager = TokenManager(self.ollama_config.model_name)

            # Metrics
            self.metrics = MetricsCollector()

            # Async executor
            self._executor = ThreadPoolExecutor(max_workers=5)

            # Initialize LM
            self._lm = None
            self._create_lm()

            # Connection pool
            self._pool = ConnectionPool(
                factory_func=self._create_lm,
                size=5
            )

            self._initialized = True
            logger.info(
                f"LLMManager initialized with {use_backend} backend "
                f"(model: {self.ollama_config.model_name})"
            )

    def _create_lm(self):
        """Create DSPy LM instance based on backend"""
        try:
            if self.use_backend == "ollama":
                logger.debug(f"Creating Ollama LM: {self.ollama_config.base_url}")
                self._lm = dspy.OllamaLocal(
                    model=self.ollama_config.model_name,
                    base_url=self.ollama_config.base_url,
                    timeout=self.ollama_config.timeout,
                    temperature=self.llm_config.temperature,
                    max_tokens=self.llm_config.max_tokens,
                    top_p=self.llm_config.top_p,
                )
                return self._lm

            elif self.use_backend == "llama_cpp":
                # Custom llama.cpp backend (optional)
                if self.llama_cpp_config.model_path is None:
                    raise ConfigurationError("llama_cpp backend requires model_path")

                logger.debug(f"Creating llama.cpp LM: {self.llama_cpp_config.model_path}")
                # Import lazily to avoid dependency if not used
                from .llama_cpp_backend import LlamaCppLM
                self._lm = LlamaCppLM(self.llama_cpp_config, self.llm_config)
                return self._lm

            else:
                raise ConfigurationError(
                    f"Unknown backend: {self.use_backend}. Use 'ollama' or 'llama_cpp'"
                )

        except Exception as e:
            logger.error(f"Failed to create LM: {e}", exc_info=True)
            raise ConnectionError(f"Failed to initialize LM backend: {e}") from e

    def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry"""
        delay = self.ollama_config.retry_delay
        last_exception = None

        for attempt in range(self.ollama_config.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == self.ollama_config.max_retries - 1:
                    break

                # Check if error is retryable
                if isinstance(e, (ConnectionError, TimeoutError)):
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.ollama_config.max_retries} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay *= self.ollama_config.retry_backoff
                else:
                    # Non-retryable error
                    break

        # All retries exhausted
        logger.error(f"All retry attempts failed: {last_exception}")
        raise last_exception

    # ========================================================================
    # Class Methods
    # ========================================================================

    @classmethod
    def get_instance(
        cls,
        ollama_config: Optional[OllamaConfig] = None,
        llama_cpp_config: Optional[LlamaCppConfig] = None,
        llm_config: Optional[LLMConfig] = None,
        use_backend: str = "ollama"
    ) -> 'LLMManager':
        """
        Get singleton instance (recommended usage)

        Example:
            manager = LLMManager.get_instance(
                ollama_config=OllamaConfig(model_name="gpt-oss:20b"),
                llm_config=LLMConfig(temperature=0.3)
            )
        """
        return cls(ollama_config, llama_cpp_config, llm_config, use_backend)

    @classmethod
    def from_env(cls) -> 'LLMManager':
        """Load configuration from environment variables"""
        ollama_config = OllamaConfig(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model_name=os.getenv("OLLAMA_MODEL_NAME", "gpt-oss:20b"),
            timeout=int(os.getenv("OLLAMA_TIMEOUT", "60")),
            max_retries=int(os.getenv("OLLAMA_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("OLLAMA_RETRY_DELAY", "1.0")),
            retry_backoff=float(os.getenv("OLLAMA_RETRY_BACKOFF", "2.0")),
        )

        llm_config = LLMConfig(
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2048")),
            top_p=float(os.getenv("LLM_TOP_P", "0.9")),
            frequency_penalty=float(os.getenv("LLM_FREQUENCY_PENALTY", "0.0")),
            presence_penalty=float(os.getenv("LLM_PRESENCE_PENALTY", "0.0")),
        )

        use_backend = os.getenv("LLM_BACKEND", "ollama")

        logger.info("Loading LLMManager from environment variables")
        return cls.get_instance(
            ollama_config=ollama_config,
            llm_config=llm_config,
            use_backend=use_backend
        )

    @classmethod
    def from_config(cls, config_path: str) -> 'LLMManager':
        """Load configuration from YAML file"""
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML is required for config file support. Install with: pip install pyyaml")

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        ollama_config = OllamaConfig(**config.get('ollama', {}))
        llama_cpp_config = LlamaCppConfig(**config.get('llama_cpp', {}))
        llm_config = LLMConfig(**config.get('llm', {}))
        use_backend = config.get('backend', 'ollama')

        logger.info(f"Loading LLMManager from config file: {config_path}")
        return cls.get_instance(
            ollama_config=ollama_config,
            llama_cpp_config=llama_cpp_config,
            llm_config=llm_config,
            use_backend=use_backend
        )

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset singleton instance (TESTING ONLY)
        ⚠️ Warning: Do not use in production
        """
        with cls._lock:
            logger.warning("Resetting LLMManager singleton (testing only)")
            if cls._instance and hasattr(cls._instance, '_executor'):
                cls._instance._executor.shutdown(wait=False)
            cls._instance = None
            cls._initialized = False

    # ========================================================================
    # LM Access
    # ========================================================================

    def get_lm(self, **overrides) -> Any:
        """
        Get DSPy LM instance with optional parameter overrides

        Example:
            lm = manager.get_lm(temperature=0.7, max_tokens=4096)
        """
        if overrides:
            # Create temporary LM with overrides
            logger.debug(f"Creating LM with overrides: {overrides}")
            if self.use_backend == "ollama":
                return dspy.OllamaLocal(
                    model=self.ollama_config.model_name,
                    base_url=self.ollama_config.base_url,
                    timeout=self.ollama_config.timeout,
                    temperature=overrides.get('temperature', self.llm_config.temperature),
                    max_tokens=overrides.get('max_tokens', self.llm_config.max_tokens),
                    top_p=overrides.get('top_p', self.llm_config.top_p),
                )
            else:
                # For llama.cpp, would need to recreate with new config
                logger.warning("Parameter overrides not fully supported for llama_cpp backend")
                return self._lm

        return self._lm

    # ========================================================================
    # Completion Methods
    # ========================================================================

    def complete(self, prompt: str, **kwargs) -> str:
        """
        Synchronous completion

        Args:
            prompt: Input text
            **kwargs: Override generation parameters (temperature, max_tokens, etc.)

        Returns:
            Generated text

        Raises:
            ConnectionError: If backend unavailable
            TimeoutError: If request times out
        """
        start_time = time.time()
        tokens = self.token_manager.estimate_tokens(prompt)

        try:
            logger.debug(f"Completion request: {len(prompt)} chars (~{tokens} tokens)")

            # Get LM (with overrides if provided)
            lm = self.get_lm(**kwargs) if kwargs else self._lm

            # Execute with retry
            def _do_complete():
                # DSPy LM interface
                if hasattr(lm, '__call__'):
                    return lm(prompt)
                else:
                    raise AttributeError("LM does not support __call__")

            response = self._retry_with_backoff(_do_complete)

            latency_ms = (time.time() - start_time) * 1000
            self.metrics.record_request(latency_ms, tokens, success=True)

            logger.info(f"Completion successful: {latency_ms:.2f}ms")
            return response

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self.metrics.record_request(latency_ms, 0, success=False, error_type=type(e).__name__)
            logger.error(f"Completion failed: {e}", exc_info=True)
            raise

    async def acomplete(self, prompt: str, **kwargs) -> str:
        """
        Async completion using executor

        Args:
            prompt: Input text
            **kwargs: Override generation parameters

        Returns:
            Generated text
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self.complete,
            prompt,
            **kwargs
        )

    async def stream(self, prompt: str, chunk_size: int = 10, **kwargs) -> AsyncGenerator[str, None]:
        """
        Async streaming generator

        Args:
            prompt: Input text
            chunk_size: Characters per chunk (for simulated streaming)
            **kwargs: Override generation parameters

        Yields:
            Text chunks
        """
        # Note: DSPy's OllamaLocal may not support streaming natively
        # This simulates streaming by chunking the complete response
        logger.debug(f"Streaming request: {len(prompt)} chars")

        response = await self.acomplete(prompt, **kwargs)

        # Simulate streaming by yielding chunks
        for i in range(0, len(response), chunk_size):
            chunk = response[i:i + chunk_size]
            await asyncio.sleep(0.01)  # Small delay for realistic streaming
            yield chunk

    def safe_completion(
        self,
        prompt: str,
        reserve_output: int = 2048,
        auto_truncate: bool = True,
        min_output: int = 64,
        **kwargs
    ) -> str:
        """
        Safe completion with automatic token management

        Args:
            prompt: Input text
            reserve_output: Desired output token budget
            auto_truncate: Auto-truncate input if needed
            min_output: Minimum output tokens
            **kwargs: Override generation parameters

        Returns:
            Generated text

        Raises:
            TokenLimitExceededError: If prompt too long and auto_truncate=False
        """
        # 1. Estimate input tokens
        prompt_tokens = self.token_manager.estimate_tokens(prompt)

        # 2. Calculate available output space
        max_ctx = self.token_manager.max_context_tokens
        available_output = max_ctx - prompt_tokens

        # 3. Truncate if necessary
        if available_output < min_output:
            if not auto_truncate:
                raise TokenLimitExceededError(
                    f"Prompt uses {prompt_tokens} tokens, only {available_output} tokens left "
                    f"for output (context limit: {max_ctx})"
                )

            logger.warning(
                f"Prompt too long ({prompt_tokens} tokens), truncating to fit context window"
            )

            need_output = max(reserve_output, min_output)
            target_prompt_tokens = max(max_ctx - need_output, 0)
            prompt = self.token_manager.truncate_to_tokens(prompt, target_prompt_tokens)
            prompt_tokens = self.token_manager.estimate_tokens(prompt)
            available_output = max_ctx - prompt_tokens

        # 4. Calculate final max_tokens
        final_max_tokens = max(
            min(reserve_output, max(available_output, 0)),
            min_output
        )

        logger.debug(
            f"Token budget: prompt={prompt_tokens}, output={final_max_tokens}, "
            f"total={prompt_tokens + final_max_tokens}/{max_ctx}"
        )

        # 5. Call with computed max_tokens
        return self.complete(prompt, max_tokens=final_max_tokens, **kwargs)

    # ========================================================================
    # Management Methods
    # ========================================================================

    def health_check(self) -> bool:
        """
        Check if backend is available

        Returns:
            True if healthy, False otherwise
        """
        try:
            logger.debug("Performing health check")
            # Simple test prompt
            response = self.complete("ping", max_tokens=10)
            logger.info("Health check passed")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def reconnect(self) -> None:
        """Recreate LM connection"""
        logger.info("Reconnecting to LM backend")
        try:
            self._create_lm()
            logger.info("Reconnection successful")
        except Exception as e:
            logger.error(f"Reconnection failed: {e}", exc_info=True)
            raise

    def reconfigure(
        self,
        ollama_config: Optional[OllamaConfig] = None,
        llama_cpp_config: Optional[LlamaCppConfig] = None,
        llm_config: Optional[LLMConfig] = None
    ) -> None:
        """
        Reconfigure LLM (affects all users of singleton)
        ⚠️ Use with caution in production

        Args:
            ollama_config: New Ollama configuration
            llama_cpp_config: New llama.cpp configuration
            llm_config: New LLM generation parameters
        """
        with self._lock:
            logger.warning("Reconfiguring LLMManager (affects all users)")

            if ollama_config:
                self.ollama_config = ollama_config
                self.token_manager = TokenManager(ollama_config.model_name)

            if llama_cpp_config:
                self.llama_cpp_config = llama_cpp_config

            if llm_config:
                self.llm_config = llm_config

            # Recreate LM with new config
            self._create_lm()

            logger.info("Reconfiguration complete")

    def get_stats(self) -> LLMStats:
        """Get usage statistics"""
        return self.metrics.get_summary()

    def reset_stats(self) -> None:
        """Reset usage statistics"""
        logger.info("Resetting LLM statistics")
        self.metrics.reset()
