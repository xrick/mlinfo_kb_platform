# dspy_version/services/LLM/llama_cpp_backend.py
"""
Custom DSPy LM wrapper for llama.cpp backend

This is an optional backend. Install with:
    pip install llama-cpp-python
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

try:
    import dspy
except ImportError:
    raise ImportError("DSPy is required. Install with: pip install dspy-ai")

from .config import LlamaCppConfig, LLMConfig
from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class LlamaCppLM(dspy.LM):
    """
    Custom DSPy LM wrapper for llama.cpp

    Usage:
        config = LlamaCppConfig(
            model_path="/path/to/model.gguf",
            n_ctx=131072,
            n_threads=8
        )
        lm = LlamaCppLM(config)
    """

    def __init__(self, llama_config: LlamaCppConfig, llm_config: Optional[LLMConfig] = None):
        """
        Initialize llama.cpp backend

        Args:
            llama_config: llama.cpp configuration
            llm_config: Generation parameters
        """
        if Llama is None:
            raise ImportError(
                "llama-cpp-python is required for llama.cpp backend. "
                "Install with: pip install llama-cpp-python"
            )

        if llama_config.model_path is None:
            raise ConfigurationError("model_path is required for llama.cpp backend")

        super().__init__()

        self.llama_config = llama_config
        self.llm_config = llm_config or LLMConfig()

        logger.info(f"Initializing llama.cpp backend: {llama_config.model_path}")

        try:
            self.llm = Llama(
                model_path=llama_config.model_path,
                n_ctx=llama_config.n_ctx,
                n_batch=llama_config.n_batch,
                n_threads=llama_config.n_threads,
                use_mmap=llama_config.use_mmap,
                use_mlock=llama_config.use_mlock,
                n_gpu_layers=llama_config.n_gpu_layers,
                verbose=False
            )
            logger.info("llama.cpp backend initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize llama.cpp: {e}", exc_info=True)
            raise ConfigurationError(f"llama.cpp initialization failed: {e}") from e

    def __call__(self, prompt: str, **kwargs) -> str:
        """
        Synchronous completion (DSPy LM interface)

        Args:
            prompt: Input text
            **kwargs: Override generation parameters

        Returns:
            Generated text
        """
        max_tokens = kwargs.get('max_tokens', self.llm_config.max_tokens)
        temperature = kwargs.get('temperature', self.llm_config.temperature)
        top_p = kwargs.get('top_p', self.llm_config.top_p)

        logger.debug(f"llama.cpp completion: {len(prompt)} chars, max_tokens={max_tokens}")

        try:
            response = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                echo=False
            )

            # Extract text from response
            if isinstance(response, dict):
                text = response['choices'][0]['text']
            else:
                text = str(response)

            return text

        except Exception as e:
            logger.error(f"llama.cpp completion failed: {e}", exc_info=True)
            raise

    async def agenerate(self, prompt: str, **kwargs) -> str:
        """
        Async completion (run in executor)

        Args:
            prompt: Input text
            **kwargs: Override generation parameters

        Returns:
            Generated text
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.__call__, prompt, **kwargs)

    def stream(self, prompt: str, **kwargs):
        """
        Streaming completion (generator)

        Args:
            prompt: Input text
            **kwargs: Override generation parameters

        Yields:
            Text chunks
        """
        max_tokens = kwargs.get('max_tokens', self.llm_config.max_tokens)
        temperature = kwargs.get('temperature', self.llm_config.temperature)
        top_p = kwargs.get('top_p', self.llm_config.top_p)

        logger.debug(f"llama.cpp streaming: {len(prompt)} chars")

        try:
            stream = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stream=True
            )

            for chunk in stream:
                if isinstance(chunk, dict):
                    text = chunk['choices'][0]['text']
                else:
                    text = str(chunk)
                yield text

        except Exception as e:
            logger.error(f"llama.cpp streaming failed: {e}", exc_info=True)
            raise
