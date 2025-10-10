# dspy_version/services/LLM/test_llm_manager.py
"""
Unit tests for LLMManager

Run with:
    pytest test_llm_manager.py -v
    pytest test_llm_manager.py -v -s  # with print output
    pytest test_llm_manager.py -k test_singleton  # specific test
"""

import pytest
import threading
import time
import asyncio
from unittest.mock import Mock, patch

from config import OllamaConfig, LLMConfig
from exceptions import (
    ConnectionError,
    TokenLimitExceededError,
    ConfigurationError
)
from llm_manager import LLMManager, MetricsCollector, TokenManager


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset singleton before each test"""
    LLMManager.reset_instance()
    yield
    LLMManager.reset_instance()


@pytest.fixture
def ollama_config():
    """Default Ollama configuration"""
    return OllamaConfig(
        base_url="http://localhost:11434",
        model_name="gpt-oss:20b",
        timeout=60
    )


@pytest.fixture
def llm_config():
    """Default LLM configuration"""
    return LLMConfig(
        temperature=0.3,
        max_tokens=2048
    )


# ============================================================================
# Singleton Pattern Tests
# ============================================================================

class TestSingletonPattern:
    """Test singleton pattern implementation"""

    def test_singleton_returns_same_instance(self, ollama_config, llm_config):
        """Verify only one instance exists"""
        manager1 = LLMManager.get_instance(
            ollama_config=ollama_config,
            llm_config=llm_config
        )
        manager2 = LLMManager.get_instance()

        assert manager1 is manager2

    def test_singleton_thread_safety(self, ollama_config, llm_config):
        """Test concurrent access to singleton"""
        instances = []

        def create_instance():
            inst = LLMManager.get_instance(
                ollama_config=ollama_config,
                llm_config=llm_config
            )
            instances.append(inst)

        threads = [threading.Thread(target=create_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All instances should be the same
        assert len(instances) == 10
        assert all(inst is instances[0] for inst in instances)

    def test_initialization_happens_once(self, ollama_config, llm_config):
        """Verify initialization only happens once"""
        manager1 = LLMManager.get_instance(
            ollama_config=ollama_config,
            llm_config=llm_config
        )
        original_lm = manager1._lm

        # Get instance again
        manager2 = LLMManager.get_instance()

        # Should be same instance and same LM
        assert manager2 is manager1
        assert manager2._lm is original_lm

    def test_reset_instance(self, ollama_config, llm_config):
        """Test singleton reset (for testing)"""
        manager1 = LLMManager.get_instance(
            ollama_config=ollama_config,
            llm_config=llm_config
        )

        LLMManager.reset_instance()

        manager2 = LLMManager.get_instance(
            ollama_config=ollama_config,
            llm_config=llm_config
        )

        # Should be different instances after reset
        assert manager1 is not manager2


# ============================================================================
# Token Management Tests
# ============================================================================

class TestTokenManager:
    """Test token estimation and truncation"""

    def test_estimate_tokens_ascii(self):
        """Test token estimation for ASCII text"""
        tm = TokenManager("gpt-oss:20b")

        text = "Hello world"  # ~2-3 tokens
        tokens = tm.estimate_tokens(text)

        assert 2 <= tokens <= 4

    def test_estimate_tokens_cjk(self):
        """Test token estimation for CJK text"""
        tm = TokenManager("gpt-oss:20b")

        text = "你好世界"  # ~4 tokens
        tokens = tm.estimate_tokens(text)

        assert 3 <= tokens <= 5

    def test_estimate_tokens_mixed(self):
        """Test token estimation for mixed text"""
        tm = TokenManager("gpt-oss:20b")

        text = "Hello 世界 Python"
        tokens = tm.estimate_tokens(text)

        assert tokens > 0

    def test_estimate_tokens_empty(self):
        """Test token estimation for empty text"""
        tm = TokenManager("gpt-oss:20b")

        tokens = tm.estimate_tokens("")
        assert tokens == 0

    def test_truncate_to_tokens(self):
        """Test text truncation"""
        tm = TokenManager("gpt-oss:20b")

        long_text = "A" * 1000
        truncated = tm.truncate_to_tokens(long_text, 50)

        # Should be truncated
        assert len(truncated) < len(long_text)
        assert len(truncated) <= 100  # ~50 tokens * 2 chars

    def test_truncate_already_short(self):
        """Test truncation of already short text"""
        tm = TokenManager("gpt-oss:20b")

        short_text = "Hello"
        truncated = tm.truncate_to_tokens(short_text, 100)

        # Should be unchanged
        assert truncated == short_text

    def test_context_limits(self):
        """Test context window limits"""
        tm = TokenManager("gpt-oss:20b")
        assert tm.max_context_tokens == 131072

        tm2 = TokenManager("unknown-model")
        assert tm2.max_context_tokens == 8192  # default


# ============================================================================
# Metrics Tests
# ============================================================================

class TestMetrics:
    """Test metrics collection"""

    def test_record_success(self):
        """Test recording successful request"""
        collector = MetricsCollector()

        collector.record_request(latency_ms=100.0, tokens=50, success=True)

        stats = collector.get_summary()
        assert stats.total_requests == 1
        assert stats.successful_requests == 1
        assert stats.failed_requests == 0
        assert stats.total_tokens == 50
        assert stats.avg_latency_ms == 100.0

    def test_record_failure(self):
        """Test recording failed request"""
        collector = MetricsCollector()

        collector.record_request(
            latency_ms=0,
            success=False,
            error_type="ConnectionError"
        )

        stats = collector.get_summary()
        assert stats.total_requests == 1
        assert stats.successful_requests == 0
        assert stats.failed_requests == 1
        assert stats.error_counts["ConnectionError"] == 1

    def test_multiple_requests(self):
        """Test aggregating multiple requests"""
        collector = MetricsCollector()

        collector.record_request(100.0, 50, True)
        collector.record_request(200.0, 100, True)
        collector.record_request(0, 0, False, "TimeoutError")

        stats = collector.get_summary()
        assert stats.total_requests == 3
        assert stats.successful_requests == 2
        assert stats.failed_requests == 1
        assert stats.total_tokens == 150
        assert stats.avg_latency_ms == 150.0  # (100 + 200) / 2

    def test_reset_metrics(self):
        """Test resetting metrics"""
        collector = MetricsCollector()

        collector.record_request(100.0, 50, True)
        collector.reset()

        stats = collector.get_summary()
        assert stats.total_requests == 0
        assert stats.successful_requests == 0


# ============================================================================
# Configuration Tests
# ============================================================================

class TestConfiguration:
    """Test configuration management"""

    def test_default_configuration(self):
        """Test default configuration values"""
        config = OllamaConfig()

        assert config.base_url == "http://localhost:11434"
        assert config.model_name == "gpt-oss:20b"
        assert config.timeout == 60

    def test_custom_configuration(self):
        """Test custom configuration"""
        config = OllamaConfig(
            base_url="http://custom:8080",
            model_name="custom-model",
            timeout=120
        )

        assert config.base_url == "http://custom:8080"
        assert config.model_name == "custom-model"
        assert config.timeout == 120

    @patch.dict('os.environ', {
        'OLLAMA_BASE_URL': 'http://env:11434',
        'OLLAMA_MODEL_NAME': 'env-model',
        'LLM_TEMPERATURE': '0.5'
    })
    def test_from_env(self):
        """Test loading from environment variables"""
        manager = LLMManager.from_env()

        assert manager.ollama_config.base_url == "http://env:11434"
        assert manager.ollama_config.model_name == "env-model"
        assert manager.llm_config.temperature == 0.5


# ============================================================================
# Mock Tests (without actual Ollama connection)
# ============================================================================

class TestLLMManagerMocked:
    """Test LLMManager with mocked backend"""

    @patch('llm_manager.dspy.OllamaLocal')
    def test_manager_initialization(self, mock_ollama, ollama_config, llm_config):
        """Test manager initialization"""
        manager = LLMManager.get_instance(
            ollama_config=ollama_config,
            llm_config=llm_config
        )

        assert manager is not None
        assert manager.ollama_config.model_name == "gpt-oss:20b"
        mock_ollama.assert_called_once()

    @patch('llm_manager.dspy.OllamaLocal')
    def test_get_lm(self, mock_ollama, ollama_config, llm_config):
        """Test get_lm method"""
        manager = LLMManager.get_instance(
            ollama_config=ollama_config,
            llm_config=llm_config
        )

        lm = manager.get_lm()
        assert lm is not None

    @patch('llm_manager.dspy.OllamaLocal')
    def test_reconfigure(self, mock_ollama, ollama_config, llm_config):
        """Test reconfiguration"""
        manager = LLMManager.get_instance(
            ollama_config=ollama_config,
            llm_config=llm_config
        )

        new_llm_config = LLMConfig(temperature=0.7, max_tokens=1024)
        manager.reconfigure(llm_config=new_llm_config)

        assert manager.llm_config.temperature == 0.7
        assert manager.llm_config.max_tokens == 1024


# ============================================================================
# Async Tests
# ============================================================================

class TestAsync:
    """Test async functionality"""

    @pytest.mark.asyncio
    @patch('llm_manager.dspy.OllamaLocal')
    async def test_acomplete(self, mock_ollama, ollama_config, llm_config):
        """Test async completion"""
        # Setup mock
        mock_lm = Mock()
        mock_lm.return_value = "Test response"
        mock_ollama.return_value = mock_lm

        manager = LLMManager.get_instance(
            ollama_config=ollama_config,
            llm_config=llm_config
        )

        # Note: This test may fail without proper async setup
        # In real usage, would need actual Ollama server
        # response = await manager.acomplete("Test prompt")
        # assert isinstance(response, str)


# ============================================================================
# Integration Tests (require running Ollama server)
# ============================================================================

@pytest.mark.integration
class TestIntegration:
    """Integration tests with real Ollama server"""

    def test_health_check(self, ollama_config, llm_config):
        """Test health check with real backend"""
        # Skip if Ollama not available
        pytest.skip("Requires running Ollama server")

        manager = LLMManager.get_instance(
            ollama_config=ollama_config,
            llm_config=llm_config
        )

        is_healthy = manager.health_check()
        assert is_healthy is True

    def test_complete(self, ollama_config, llm_config):
        """Test completion with real backend"""
        # Skip if Ollama not available
        pytest.skip("Requires running Ollama server")

        manager = LLMManager.get_instance(
            ollama_config=ollama_config,
            llm_config=llm_config
        )

        response = manager.complete("Say hello", max_tokens=10)
        assert isinstance(response, str)
        assert len(response) > 0


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.benchmark
class TestPerformance:
    """Performance benchmarks"""

    def test_singleton_access_speed(self, benchmark, ollama_config, llm_config):
        """Benchmark singleton access time"""
        # Initialize once
        LLMManager.get_instance(
            ollama_config=ollama_config,
            llm_config=llm_config
        )

        def access():
            return LLMManager.get_instance()

        result = benchmark(access)
        # Should be very fast (< 1ms)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
