# dspy_version/services/LLM/exceptions.py
"""
Custom exceptions for LLMManager
"""


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
