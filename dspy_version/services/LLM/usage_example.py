# dspy_version/services/LLM/usage_example.py
"""
Usage examples for LLMManager with DSPy

Demonstrates various ways to use the LLMManager singleton with DSPy modules.
"""

import asyncio
import logging
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# ============================================================================
# Example 1: Basic Initialization
# ============================================================================

def example_basic_initialization():
    """Example: Initialize LLMManager with basic configuration"""
    print("\n" + "="*70)
    print("Example 1: Basic Initialization")
    print("="*70)

    from dspy_version.services.LLM import LLMManager, OllamaConfig, LLMConfig

    # Method 1: Get instance with explicit config
    manager = LLMManager.get_instance(
        ollama_config=OllamaConfig(
            base_url="http://localhost:11434",
            model_name="gpt-oss:20b",
            timeout=60
        ),
        llm_config=LLMConfig(
            temperature=0.3,
            max_tokens=2048
        )
    )

    print(f"✓ LLMManager initialized")
    print(f"  Backend: ollama")
    print(f"  Model: {manager.ollama_config.model_name}")
    print(f"  Base URL: {manager.ollama_config.base_url}")

    # Verify it's a singleton
    manager2 = LLMManager.get_instance()
    assert manager is manager2, "Should be same instance"
    print(f"✓ Singleton pattern verified (manager is manager2: {manager is manager2})")

    return manager


# ============================================================================
# Example 2: DSPy Integration
# ============================================================================

def example_dspy_integration(manager):
    """Example: Use LLMManager with DSPy modules"""
    print("\n" + "="*70)
    print("Example 2: DSPy Integration")
    print("="*70)

    import dspy

    # Configure DSPy globally
    lm = manager.get_lm()
    dspy.settings.configure(lm=lm)
    print("✓ DSPy configured with LLMManager LM")

    # Define a simple signature
    class QA(dspy.Signature):
        """Answer questions concisely"""
        question = dspy.InputField()
        answer = dspy.OutputField()

    # Create predictor
    qa = dspy.Predict(QA)

    # Test question
    question = "What is the capital of France?"
    print(f"\nQuestion: {question}")

    try:
        result = qa(question=question)
        print(f"Answer: {result.answer}")
        print("✓ DSPy prediction successful")
    except Exception as e:
        print(f"✗ DSPy prediction failed: {e}")
        logger.error(f"Prediction error: {e}", exc_info=True)


# ============================================================================
# Example 3: Direct Completion
# ============================================================================

def example_direct_completion(manager):
    """Example: Use direct completion methods"""
    print("\n" + "="*70)
    print("Example 3: Direct Completion")
    print("="*70)

    prompt = "Explain machine learning in one sentence."
    print(f"Prompt: {prompt}")

    try:
        # Synchronous completion
        response = manager.complete(prompt, max_tokens=100)
        print(f"\nResponse: {response}")
        print("✓ Direct completion successful")

        # Get statistics
        stats = manager.get_stats()
        print(f"\nStatistics:")
        print(f"  Total requests: {stats.total_requests}")
        print(f"  Successful: {stats.successful_requests}")
        print(f"  Failed: {stats.failed_requests}")
        print(f"  Avg latency: {stats.avg_latency_ms:.2f}ms")

    except Exception as e:
        print(f"✗ Direct completion failed: {e}")
        logger.error(f"Completion error: {e}", exc_info=True)


# ============================================================================
# Example 4: Token Management
# ============================================================================

def example_token_management(manager):
    """Example: Safe completion with token management"""
    print("\n" + "="*70)
    print("Example 4: Token Management")
    print("="*70)

    # Test token estimation
    short_text = "Hello world"
    tokens = manager.token_manager.estimate_tokens(short_text)
    print(f"Text: '{short_text}'")
    print(f"Estimated tokens: {tokens}")

    cjk_text = "你好世界"
    tokens = manager.token_manager.estimate_tokens(cjk_text)
    print(f"\nText: '{cjk_text}'")
    print(f"Estimated tokens: {tokens}")

    # Test safe completion
    long_prompt = "Explain artificial intelligence. " * 100
    prompt_tokens = manager.token_manager.estimate_tokens(long_prompt)
    print(f"\nLong prompt length: {len(long_prompt)} chars (~{prompt_tokens} tokens)")

    try:
        response = manager.safe_completion(
            prompt=long_prompt,
            reserve_output=1024,
            auto_truncate=True
        )
        print(f"✓ Safe completion successful (truncated if needed)")
        print(f"Response length: {len(response)} chars")

    except Exception as e:
        print(f"✗ Safe completion failed: {e}")


# ============================================================================
# Example 5: Async Completion
# ============================================================================

async def example_async_completion(manager):
    """Example: Async completion methods"""
    print("\n" + "="*70)
    print("Example 5: Async Completion")
    print("="*70)

    questions = [
        "What is Python?",
        "What is JavaScript?",
        "What is Go?",
    ]

    print(f"Processing {len(questions)} questions concurrently...")

    try:
        # Process concurrently
        tasks = [
            manager.acomplete(f"Answer briefly: {q}", max_tokens=50)
            for q in questions
        ]

        responses = await asyncio.gather(*tasks)

        print("\nResults:")
        for q, r in zip(questions, responses):
            print(f"\nQ: {q}")
            print(f"A: {r[:100]}...")  # Truncate for display

        print(f"\n✓ Processed {len(responses)} requests concurrently")

    except Exception as e:
        print(f"✗ Async completion failed: {e}")
        logger.error(f"Async error: {e}", exc_info=True)


# ============================================================================
# Example 6: Streaming
# ============================================================================

async def example_streaming(manager):
    """Example: Async streaming"""
    print("\n" + "="*70)
    print("Example 6: Streaming")
    print("="*70)

    prompt = "Tell me a very short story about AI."
    print(f"Prompt: {prompt}\n")
    print("Response: ", end='', flush=True)

    try:
        async for chunk in manager.stream(prompt, chunk_size=20):
            print(chunk, end='', flush=True)

        print("\n\n✓ Streaming completed")

    except Exception as e:
        print(f"\n✗ Streaming failed: {e}")
        logger.error(f"Streaming error: {e}", exc_info=True)


# ============================================================================
# Example 7: RAG Pipeline with DSPy
# ============================================================================

def example_rag_pipeline(manager):
    """Example: RAG pipeline using DSPy"""
    print("\n" + "="*70)
    print("Example 7: RAG Pipeline with DSPy")
    print("="*70)

    import dspy

    # Configure DSPy
    dspy.settings.configure(lm=manager.get_lm())

    # Define RAG signature
    class RAGSignature(dspy.Signature):
        """Answer question based on context"""
        context = dspy.InputField(desc="relevant context")
        question = dspy.InputField()
        answer = dspy.OutputField()

    # Create RAG module
    class SimpleRAG(dspy.Module):
        def __init__(self):
            super().__init__()
            self.generate = dspy.ChainOfThought(RAGSignature)

        def forward(self, context: str, question: str):
            return self.generate(context=context, question=question)

    # Test RAG
    rag = SimpleRAG()

    context = """
    Machine learning is a subset of artificial intelligence that enables
    computers to learn from data without explicit programming. It uses
    statistical techniques to give computers the ability to learn patterns.
    """

    question = "What is machine learning?"

    print(f"Context: {context[:100]}...")
    print(f"Question: {question}")

    try:
        result = rag(context=context, question=question)
        print(f"\nAnswer: {result.answer}")
        print("✓ RAG pipeline successful")

    except Exception as e:
        print(f"✗ RAG pipeline failed: {e}")
        logger.error(f"RAG error: {e}", exc_info=True)


# ============================================================================
# Example 8: Configuration Management
# ============================================================================

def example_configuration(manager):
    """Example: Configuration and reconfiguration"""
    print("\n" + "="*70)
    print("Example 8: Configuration Management")
    print("="*70)

    # Show current config
    print("Current configuration:")
    print(f"  Model: {manager.ollama_config.model_name}")
    print(f"  Temperature: {manager.llm_config.temperature}")
    print(f"  Max tokens: {manager.llm_config.max_tokens}")

    # Reconfigure (affects all users!)
    from dspy_version.services.LLM import LLMConfig

    print("\nReconfiguring with higher temperature...")
    manager.reconfigure(
        llm_config=LLMConfig(
            temperature=0.7,
            max_tokens=1024
        )
    )

    print("New configuration:")
    print(f"  Temperature: {manager.llm_config.temperature}")
    print(f"  Max tokens: {manager.llm_config.max_tokens}")
    print("✓ Reconfiguration successful")

    # Reset to original
    print("\nResetting to original configuration...")
    manager.reconfigure(
        llm_config=LLMConfig(
            temperature=0.3,
            max_tokens=2048
        )
    )
    print("✓ Reset to original configuration")


# ============================================================================
# Example 9: Health Check and Monitoring
# ============================================================================

def example_monitoring(manager):
    """Example: Health checks and statistics"""
    print("\n" + "="*70)
    print("Example 9: Health Check and Monitoring")
    print("="*70)

    # Health check
    print("Performing health check...")
    is_healthy = manager.health_check()
    print(f"Health status: {'✓ Healthy' if is_healthy else '✗ Unhealthy'}")

    # Get detailed statistics
    stats = manager.get_stats()
    print("\nDetailed Statistics:")
    print(f"  Total requests: {stats.total_requests}")
    print(f"  Successful: {stats.successful_requests}")
    print(f"  Failed: {stats.failed_requests}")
    print(f"  Total tokens: {stats.total_tokens}")
    print(f"  Avg latency: {stats.avg_latency_ms:.2f}ms")
    print(f"  Last request: {stats.last_request_time}")

    if stats.error_counts:
        print(f"  Error counts: {stats.error_counts}")


# ============================================================================
# Main
# ============================================================================

def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("LLMManager Usage Examples")
    print("="*70)

    try:
        # Example 1: Basic initialization
        manager = example_basic_initialization()

        # Example 2: DSPy integration
        example_dspy_integration(manager)

        # Example 3: Direct completion
        example_direct_completion(manager)

        # Example 4: Token management
        example_token_management(manager)

        # Example 5-6: Async examples
        print("\nRunning async examples...")
        asyncio.run(example_async_completion(manager))
        asyncio.run(example_streaming(manager))

        # Example 7: RAG pipeline
        example_rag_pipeline(manager)

        # Example 8: Configuration
        example_configuration(manager)

        # Example 9: Monitoring
        example_monitoring(manager)

        print("\n" + "="*70)
        print("All examples completed!")
        print("="*70)

    except Exception as e:
        logger.error(f"Example execution failed: {e}", exc_info=True)
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    main()
