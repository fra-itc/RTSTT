#!/usr/bin/env python3
"""
Setup script for External LLM APIs feature.

This script:
1. Checks dependencies
2. Sets up API keys
3. Tests provider connectivity
4. Generates a setup report
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config.api_keys import get_api_key_manager
from src.core.providers import register_default_providers, get_factory, ProviderConfig, ProviderType


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{title}")
    print("-" * 70)


async def check_dependencies():
    """Check if required dependencies are installed."""
    print_section("Checking Dependencies")

    required = {
        "aiohttp": "For HTTP requests to APIs",
        "cryptography": "For API key encryption",
    }

    all_good = True
    for module, purpose in required.items():
        try:
            __import__(module)
            print(f"✓ {module:20s} - {purpose}")
        except ImportError:
            print(f"✗ {module:20s} - {purpose} (NOT INSTALLED)")
            all_good = False

    if not all_good:
        print("\nInstall missing dependencies with:")
        print("  pip install aiohttp cryptography")
        return False

    return True


def setup_api_keys():
    """Interactive setup for API keys."""
    print_section("API Key Setup")

    api_key_manager = get_api_key_manager()

    # Check existing keys
    print("\nCurrent API key status:")
    existing = api_key_manager.export_keys(include_sensitive=True)

    for provider in ["openai", "openrouter"]:
        if provider in existing:
            print(f"  ✓ {provider:15s} - {existing[provider]['masked_key']}")
        else:
            print(f"  ✗ {provider:15s} - Not configured")

    print("\nOptions:")
    print("  1. Configure OpenAI API key")
    print("  2. Configure OpenRouter API key")
    print("  3. Test existing keys")
    print("  4. Remove a key")
    print("  5. Skip")

    choice = input("\nEnter choice (1-5): ").strip()

    if choice == "1":
        key = input("Enter OpenAI API key (sk-...): ").strip()
        if key:
            api_key_manager.set_key("openai", key)
            print("✓ OpenAI API key saved")
    elif choice == "2":
        key = input("Enter OpenRouter API key (sk-or-...): ").strip()
        if key:
            api_key_manager.set_key("openrouter", key)
            print("✓ OpenRouter API key saved")
    elif choice == "3":
        print("\nValidating API keys...")
        for provider in ["openai", "openrouter"]:
            if api_key_manager.has_key(provider):
                valid = api_key_manager.validate_key(provider)
                if valid:
                    print(f"  ✓ {provider:15s} - Format appears valid")
                else:
                    print(f"  ✗ {provider:15s} - Format appears invalid")
    elif choice == "4":
        provider = input("Enter provider to remove (openai/openrouter): ").strip()
        if api_key_manager.remove_key(provider):
            print(f"✓ Removed {provider} API key")
        else:
            print(f"✗ No key found for {provider}")


async def test_providers():
    """Test provider connectivity."""
    print_section("Testing Provider Connectivity")

    api_key_manager = get_api_key_manager()
    register_default_providers()
    factory = get_factory()

    results = {
        "openai": {"nlp": None, "summary": None},
        "openrouter": {"nlp": None, "summary": None},
    }

    # Test OpenAI
    if api_key_manager.has_key("openai"):
        print("\nTesting OpenAI providers...")
        api_key = api_key_manager.get_key("openai")

        # Test NLP
        try:
            config = ProviderConfig(
                name="openai-gpt4",
                provider_type=ProviderType.CLOUD,
                api_key=api_key,
                extra_config={"model": "gpt-4"}
            )
            provider = await factory.create_nlp_provider(config)
            health = await provider.health_check()
            results["openai"]["nlp"] = "✓ Connected" if health else "✗ Failed"
            await provider.shutdown()
        except Exception as e:
            results["openai"]["nlp"] = f"✗ Error: {str(e)[:50]}"

        # Test Summary
        try:
            config = ProviderConfig(
                name="openai-gpt4",
                provider_type=ProviderType.CLOUD,
                api_key=api_key,
                extra_config={"model": "gpt-4"}
            )
            provider = await factory.create_summary_provider(config)
            results["openai"]["summary"] = "✓ Available"
            await provider.shutdown()
        except Exception as e:
            results["openai"]["summary"] = f"✗ Error: {str(e)[:50]}"

    else:
        results["openai"]["nlp"] = "- No API key"
        results["openai"]["summary"] = "- No API key"

    # Test OpenRouter
    if api_key_manager.has_key("openrouter"):
        print("\nTesting OpenRouter providers...")
        api_key = api_key_manager.get_key("openrouter")

        # Test NLP
        try:
            config = ProviderConfig(
                name="openrouter",
                provider_type=ProviderType.CLOUD,
                api_key=api_key,
                extra_config={"model": "anthropic/claude-3.5-sonnet"}
            )
            provider = await factory.create_nlp_provider(config)
            health = await provider.health_check()
            results["openrouter"]["nlp"] = "✓ Connected" if health else "✗ Failed"
            await provider.shutdown()
        except Exception as e:
            results["openrouter"]["nlp"] = f"✗ Error: {str(e)[:50]}"

        # Test Summary
        try:
            config = ProviderConfig(
                name="openrouter",
                provider_type=ProviderType.CLOUD,
                api_key=api_key,
                extra_config={"model": "anthropic/claude-3.5-sonnet"}
            )
            provider = await factory.create_summary_provider(config)
            results["openrouter"]["summary"] = "✓ Available"
            await provider.shutdown()
        except Exception as e:
            results["openrouter"]["summary"] = f"✗ Error: {str(e)[:50]}"

    else:
        results["openrouter"]["nlp"] = "- No API key"
        results["openrouter"]["summary"] = "- No API key"

    # Print results
    print("\nProvider Status:")
    print(f"  OpenAI NLP:      {results['openai']['nlp']}")
    print(f"  OpenAI Summary:  {results['openai']['summary']}")
    print(f"  OpenRouter NLP:  {results['openrouter']['nlp']}")
    print(f"  OpenRouter Summary: {results['openrouter']['summary']}")

    return results


def generate_report(results):
    """Generate setup report."""
    print_section("Setup Report")

    all_configured = all(
        "✓" in status
        for provider_results in results.values()
        for status in provider_results.values()
        if status and "No API key" not in status
    )

    if all_configured:
        print("\n✓ All configured providers are working correctly!")
    else:
        print("\n⚠ Some providers are not working. Review the status above.")

    print("\nNext steps:")
    print("  1. Start the backend server on port 8002")
    print("  2. Access the API Settings panel in the UI")
    print("  3. Use the Provider Selector to choose your preferred providers")
    print("  4. Monitor costs in the Cost Monitor dashboard")

    print("\nUseful commands:")
    print("  - Test providers: python tests/test_providers.py")
    print("  - Run this setup again: python scripts/setup_external_llm.py")


async def main():
    """Main setup flow."""
    print_header("External LLM APIs Setup")

    # Check dependencies
    if not await check_dependencies():
        print("\n❌ Setup cannot continue due to missing dependencies")
        return 1

    # Setup API keys
    setup_api_keys()

    # Test providers
    results = await test_providers()

    # Generate report
    generate_report(results)

    print_header("Setup Complete")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
