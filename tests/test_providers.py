"""
Test script for external LLM providers.

Tests OpenAI and OpenRouter NLP and Summary providers with dummy keys
to verify graceful error handling, and with real keys (if available) to
verify functionality.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.providers import (
    ProviderConfig,
    ProviderType,
    register_default_providers,
    get_factory,
)
from src.core.providers.exceptions import (
    ProviderAuthenticationError,
    ProviderError,
)
from src.core.config.api_keys import get_api_key_manager


async def test_openai_nlp_invalid_key():
    """Test OpenAI NLP provider with invalid API key."""
    print("\n" + "=" * 60)
    print("TEST: OpenAI NLP with Invalid Key")
    print("=" * 60)

    factory = get_factory()
    register_default_providers()

    config = ProviderConfig(
        name="openai-gpt4",
        provider_type=ProviderType.CLOUD,
        api_key="sk-invalid-key-12345",
        extra_config={"model": "gpt-4"}
    )

    try:
        provider = await factory.create_nlp_provider(config, initialize=False)
        await provider.initialize()
        print("FAIL: Should have raised authentication error")
    except ProviderAuthenticationError as e:
        print(f"PASS: Got expected authentication error: {e}")
    except Exception as e:
        print(f"FAIL: Got unexpected error: {type(e).__name__}: {e}")
    finally:
        try:
            await provider.shutdown()
        except:
            pass


async def test_openai_nlp_valid_key():
    """Test OpenAI NLP provider with valid API key (if available)."""
    print("\n" + "=" * 60)
    print("TEST: OpenAI NLP with Valid Key")
    print("=" * 60)

    api_key_manager = get_api_key_manager()

    if not api_key_manager.has_key("openai"):
        print("SKIP: No OpenAI API key configured")
        return

    api_key = api_key_manager.get_key("openai")
    factory = get_factory()

    config = ProviderConfig(
        name="openai-gpt4",
        provider_type=ProviderType.CLOUD,
        api_key=api_key,
        extra_config={"model": "gpt-4"}
    )

    try:
        provider = await factory.create_nlp_provider(config)

        # Test analysis
        test_text = "Apple Inc. announced record profits today. CEO Tim Cook was very pleased with the results."

        print(f"Analyzing text: '{test_text}'")
        result = await provider.analyze(test_text)

        print(f"\nPASS: Analysis completed successfully")
        print(f"  Provider: {result.provider_name}")
        print(f"  Processing time: {result.processing_time_ms:.2f}ms")
        print(f"  Keywords: {len(result.keywords)}")
        print(f"  Entities: {len(result.entities)}")
        print(f"  Sentiment: {result.sentiment.get('label', 'N/A')}")
        print(f"  Cost: ${result.metadata.get('cost_usd', 0):.6f}")
        print(f"  Tokens: {result.metadata.get('tokens', 0)}")

        if result.keywords:
            print(f"\n  Sample keywords:")
            for kw in result.keywords[:3]:
                print(f"    - {kw}")

        if result.entities:
            print(f"\n  Sample entities:")
            for ent in result.entities[:3]:
                print(f"    - {ent}")

        await provider.shutdown()

    except Exception as e:
        print(f"FAIL: {type(e).__name__}: {e}")


async def test_openrouter_nlp_valid_key():
    """Test OpenRouter NLP provider with valid API key (if available)."""
    print("\n" + "=" * 60)
    print("TEST: OpenRouter NLP with Valid Key")
    print("=" * 60)

    api_key_manager = get_api_key_manager()

    if not api_key_manager.has_key("openrouter"):
        print("SKIP: No OpenRouter API key configured")
        return

    api_key = api_key_manager.get_key("openrouter")
    factory = get_factory()

    config = ProviderConfig(
        name="openrouter",
        provider_type=ProviderType.CLOUD,
        api_key=api_key,
        extra_config={"model": "anthropic/claude-3.5-sonnet"}
    )

    try:
        provider = await factory.create_nlp_provider(config)

        test_text = "The new AI model achieved state-of-the-art performance on multiple benchmarks."

        print(f"Analyzing text: '{test_text}'")
        result = await provider.analyze(test_text)

        print(f"\nPASS: Analysis completed successfully")
        print(f"  Provider: {result.provider_name}")
        print(f"  Processing time: {result.processing_time_ms:.2f}ms")
        print(f"  Keywords: {len(result.keywords)}")
        print(f"  Entities: {len(result.entities)}")
        print(f"  Sentiment: {result.sentiment.get('label', 'N/A')}")
        print(f"  Cost: ${result.metadata.get('cost_usd', 0):.6f}")
        print(f"  Model: {result.metadata.get('model', 'N/A')}")

        await provider.shutdown()

    except Exception as e:
        print(f"FAIL: {type(e).__name__}: {e}")


async def test_openai_summary_valid_key():
    """Test OpenAI Summary provider with valid API key (if available)."""
    print("\n" + "=" * 60)
    print("TEST: OpenAI Summary with Valid Key")
    print("=" * 60)

    api_key_manager = get_api_key_manager()

    if not api_key_manager.has_key("openai"):
        print("SKIP: No OpenAI API key configured")
        return

    api_key = api_key_manager.get_key("openai")
    factory = get_factory()

    config = ProviderConfig(
        name="openai-gpt4",
        provider_type=ProviderType.CLOUD,
        api_key=api_key,
        extra_config={"model": "gpt-4"}
    )

    try:
        provider = await factory.create_summary_provider(config)

        test_text = """
        The quarterly earnings report showed significant growth across all major product lines.
        Revenue increased by 15% year-over-year, driven primarily by strong performance in the
        cloud services division. The CEO outlined plans for expansion into new markets and
        announced several strategic partnerships. Investors responded positively to the news,
        with stock prices rising 8% in after-hours trading.
        """

        print(f"Summarizing text...")
        result = await provider.summarize(test_text, style="concise")

        print(f"\nPASS: Summary generated successfully")
        print(f"  Provider: {result.provider_name}")
        print(f"  Processing time: {result.processing_time_ms:.2f}ms")
        print(f"  Summary: {result.summary}")
        print(f"  Key points: {len(result.key_points)}")
        print(f"  Action items: {len(result.action_items)}")
        print(f"  Cost: ${result.metadata.get('cost_usd', 0):.6f}")

        if result.key_points:
            print(f"\n  Key points:")
            for point in result.key_points:
                print(f"    - {point}")

        await provider.shutdown()

    except Exception as e:
        print(f"FAIL: {type(e).__name__}: {e}")


async def test_cost_tracking():
    """Test cost tracking functionality."""
    print("\n" + "=" * 60)
    print("TEST: Cost Tracking")
    print("=" * 60)

    from src.agents.orchestrator.provider_integration import get_provider_orchestrator

    orchestrator = get_provider_orchestrator()
    await orchestrator.initialize()

    # Check available providers
    providers = orchestrator.get_available_providers()
    print(f"\nAvailable NLP providers: {len(providers['nlp'])}")
    for p in providers['nlp']:
        print(f"  - {p['name']} ({p['type']}): {'✓' if p['available'] else '✗'}")

    print(f"\nAvailable Summary providers: {len(providers['summary'])}")
    for p in providers['summary']:
        print(f"  - {p['name']} ({p['type']}): {'✓' if p['available'] else '✗'}")

    # Get cost stats
    stats = orchestrator.get_cost_stats("daily")
    print(f"\nDaily Cost Stats:")
    print(f"  Total cost: ${stats['total_cost']:.6f}")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Total tokens: {stats['total_tokens']}")
    print(f"  Avg cost/request: ${stats['avg_cost_per_request']:.6f}")

    await orchestrator.shutdown()
    print("\nPASS: Cost tracking test completed")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("EXTERNAL LLM PROVIDER TESTS")
    print("=" * 60)

    # Test with invalid keys (should fail gracefully)
    await test_openai_nlp_invalid_key()

    # Test with valid keys (if available)
    await test_openai_nlp_valid_key()
    await test_openrouter_nlp_valid_key()
    await test_openai_summary_valid_key()

    # Test cost tracking
    await test_cost_tracking()

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
