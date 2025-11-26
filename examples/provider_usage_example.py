"""
Example: Using External STT Providers

This example demonstrates how to use the different STT providers
(local and cloud) with the RTSTT system.
"""

import asyncio
import os
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.providers.factory import ProviderFactory, ProviderRegistry
from core.providers.manager import ProviderManager
from core.providers.comparison import (
    compare_by_cost,
    compare_by_latency,
    get_best_for_use_case,
    generate_comparison_table
)


async def example_local_whisper():
    """Example: Using Local Whisper provider."""
    print("\n=== Local Whisper Provider ===")

    # Create local Whisper provider
    provider = await ProviderFactory.create_local_whisper(
        model="large-v3",
        language="it"
    )

    if not provider:
        print("Failed to create local Whisper provider")
        return

    # Get provider info
    info = provider.get_info()
    print(f"Provider: {info.name}")
    print(f"Cost per minute: ${info.cost_per_minute}")
    print(f"Latency: {info.latency_ms}ms")
    print(f"Streaming: {info.capabilities}")

    # Health check
    is_healthy = await provider.health_check()
    print(f"Health: {'OK' if is_healthy else 'FAIL'}")

    # Transcribe a file (example)
    # result = await provider.transcribe("path/to/audio.wav", language="it")
    # print(f"Transcription: {result.text}")

    await provider.cleanup()


async def example_openai_whisper():
    """Example: Using OpenAI Whisper API."""
    print("\n=== OpenAI Whisper API ===")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set. Skipping.")
        return

    # Create OpenAI provider
    provider = await ProviderFactory.create_openai(
        api_key=api_key,
        language="it"
    )

    if not provider:
        print("Failed to create OpenAI provider")
        return

    # Get provider info
    info = provider.get_info()
    print(f"Provider: {info.name}")
    print(f"Cost per minute: ${info.cost_per_minute}")
    print(f"Models: {info.models}")

    # Health check
    is_healthy = await provider.health_check()
    print(f"Health: {'OK' if is_healthy else 'FAIL'}")

    # Estimate cost
    cost = await provider.estimate_cost(300)  # 5 minutes
    print(f"Estimated cost for 5 minutes: ${cost:.4f}")

    await provider.cleanup()


async def example_deepgram():
    """Example: Using Deepgram provider."""
    print("\n=== Deepgram Provider ===")

    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        print("DEEPGRAM_API_KEY not set. Skipping.")
        return

    # Create Deepgram provider
    provider = await ProviderFactory.create_deepgram(
        api_key=api_key,
        model="nova-2",
        language="it",
        enable_diarization=True
    )

    if not provider:
        print("Failed to create Deepgram provider")
        return

    # Get provider info
    info = provider.get_info()
    print(f"Provider: {info.name}")
    print(f"Cost per minute: ${info.cost_per_minute}")
    print(f"Latency: {info.latency_ms}ms")
    print(f"Streaming support: {info.capabilities}")

    # Health check
    is_healthy = await provider.health_check()
    print(f"Health: {'OK' if is_healthy else 'FAIL'}")

    await provider.cleanup()


async def example_assemblyai():
    """Example: Using AssemblyAI provider."""
    print("\n=== AssemblyAI Provider ===")

    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    if not api_key:
        print("ASSEMBLYAI_API_KEY not set. Skipping.")
        return

    # Create AssemblyAI provider
    provider = await ProviderFactory.create_assemblyai(
        api_key=api_key,
        language="it",
        enable_speaker_labels=True,
        enable_sentiment=True
    )

    if not provider:
        print("Failed to create AssemblyAI provider")
        return

    # Get provider info
    info = provider.get_info()
    print(f"Provider: {info.name}")
    print(f"Cost per minute: ${info.cost_per_minute}")
    print(f"Features: Speaker labels, sentiment analysis")

    # Health check
    is_healthy = await provider.health_check()
    print(f"Health: {'OK' if is_healthy else 'FAIL'}")

    await provider.cleanup()


async def example_provider_manager():
    """Example: Using Provider Manager with fallback chain."""
    print("\n=== Provider Manager with Fallback ===")

    # Create provider manager
    manager = ProviderManager()

    # Create providers
    local = await ProviderFactory.create_local_whisper(model="large-v3")

    openai_key = os.getenv("OPENAI_API_KEY")
    deepgram_key = os.getenv("DEEPGRAM_API_KEY")

    fallbacks = []
    if deepgram_key:
        deepgram = await ProviderFactory.create_deepgram(api_key=deepgram_key)
        if deepgram:
            fallbacks.append(deepgram)

    if openai_key:
        openai = await ProviderFactory.create_openai(api_key=openai_key)
        if openai:
            fallbacks.append(openai)

    # Set up fallback chain
    if local:
        await manager.set_primary_provider(local, fallback_chain=fallbacks)
        print("Primary: Local Whisper")
        print(f"Fallbacks: {[p.config.provider_name for p in fallbacks]}")

        # Check health of all providers
        health = await manager.check_all_health()
        print(f"Health status: {health}")

        # Get usage stats
        stats = await manager.get_usage_stats()
        print(f"Total cost: ${stats['total_cost']}")
        print(f"Total duration: {stats['total_duration_minutes']:.2f} minutes")

    await manager.cleanup()


async def example_cost_comparison():
    """Example: Compare providers by cost."""
    print("\n=== Cost Comparison (60 min/month) ===")

    comparisons = compare_by_cost(duration_minutes=60, include_local=True)

    for comp in comparisons:
        print(f"{comp['name']:30} - Monthly: ${comp['monthly_cost']:.2f}")


async def example_latency_comparison():
    """Example: Compare providers by latency."""
    print("\n=== Latency Comparison ===")

    comparisons = compare_by_latency()

    for comp in comparisons:
        print(f"{comp['name']:30} - {comp['latency_ms']:4}ms - Streaming: {comp['streaming']}")


async def example_best_for_use_case():
    """Example: Get best provider for use case."""
    print("\n=== Best Providers for Real-Time Transcription ===")

    providers = get_best_for_use_case(
        use_case="real-time",
        budget_per_hour=1.0,  # Max $1/hour
        requires_streaming=True
    )

    for provider in providers:
        print(f"  - {provider}")


def example_comparison_table():
    """Example: Generate comparison table."""
    print("\n=== Provider Comparison Table ===")
    table = generate_comparison_table()
    print(table[:500] + "...")  # Print first 500 chars


async def main():
    """Run all examples."""
    print("=" * 60)
    print("External STT Providers - Usage Examples")
    print("=" * 60)

    # Provider examples
    await example_local_whisper()
    await example_openai_whisper()
    await example_deepgram()
    await example_assemblyai()

    # Manager example
    await example_provider_manager()

    # Comparison examples
    await example_cost_comparison()
    await example_latency_comparison()
    await example_best_for_use_case()
    example_comparison_table()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
