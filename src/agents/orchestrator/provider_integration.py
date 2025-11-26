"""
Provider Integration for WebSocket Orchestrator

Integrates external LLM providers with the orchestrator's WebSocket gateway.
Handles provider selection, routing, fallback, and cost tracking.
"""

import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime

from src.core.providers import (
    get_factory,
    register_default_providers,
    ProviderConfig,
    ProviderType,
    NLPProvider,
    SummaryProvider,
    NLPResult,
    SummaryResult,
)
from src.core.providers.exceptions import (
    ProviderError,
    ProviderNotAvailableError,
    ProviderAuthenticationError,
)
from src.core.config.api_keys import get_api_key_manager

logger = logging.getLogger(__name__)


class ProviderOrchestrator:
    """
    Orchestrates provider selection and request routing.

    Features:
    - Dynamic provider selection based on user preference
    - Automatic fallback to local providers on API failures
    - Cost tracking and reporting
    - Provider health monitoring
    """

    def __init__(self):
        """Initialize the provider orchestrator."""
        self.factory = get_factory()
        self.api_key_manager = get_api_key_manager()
        self.nlp_providers: Dict[str, NLPProvider] = {}
        self.summary_providers: Dict[str, SummaryProvider] = {}
        self.cost_entries: list = []
        self._initialized = False

        # Default provider selections
        self.default_nlp_provider = "local"
        self.default_summary_provider = "local"

    async def initialize(self) -> None:
        """Initialize the orchestrator and register providers."""
        if self._initialized:
            return

        # Register all default providers
        register_default_providers()

        # Initialize available providers based on API keys
        await self._initialize_providers()

        self._initialized = True
        logger.info("ProviderOrchestrator initialized")

    async def _initialize_providers(self) -> None:
        """Initialize providers based on available API keys."""
        # Initialize OpenAI providers if API key is available
        if self.api_key_manager.has_key("openai"):
            try:
                api_key = self.api_key_manager.get_key("openai")

                # Create NLP provider
                nlp_config = ProviderConfig(
                    name="openai-gpt4",
                    provider_type=ProviderType.CLOUD,
                    api_key=api_key,
                    cost_per_token=0.00006,  # Average cost
                    extra_config={"model": "gpt-4"}
                )
                nlp_provider = await self.factory.create_nlp_provider(nlp_config)
                self.nlp_providers["openai-gpt4"] = nlp_provider

                # Create Summary provider
                summary_config = ProviderConfig(
                    name="openai-gpt4",
                    provider_type=ProviderType.CLOUD,
                    api_key=api_key,
                    cost_per_token=0.00006,
                    extra_config={"model": "gpt-4"}
                )
                summary_provider = await self.factory.create_summary_provider(summary_config)
                self.summary_providers["openai-gpt4"] = summary_provider

                logger.info("OpenAI providers initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI providers: {e}")

        # Initialize OpenRouter providers if API key is available
        if self.api_key_manager.has_key("openrouter"):
            try:
                api_key = self.api_key_manager.get_key("openrouter")

                # Create NLP provider with Claude 3.5 Sonnet as default
                nlp_config = ProviderConfig(
                    name="openrouter",
                    provider_type=ProviderType.CLOUD,
                    api_key=api_key,
                    cost_per_token=0.000018,  # Claude 3.5 Sonnet average
                    extra_config={"model": "anthropic/claude-3.5-sonnet"}
                )
                nlp_provider = await self.factory.create_nlp_provider(nlp_config)
                self.nlp_providers["openrouter"] = nlp_provider

                # Create Summary provider
                summary_config = ProviderConfig(
                    name="openrouter",
                    provider_type=ProviderType.CLOUD,
                    api_key=api_key,
                    cost_per_token=0.000018,
                    extra_config={"model": "anthropic/claude-3.5-sonnet"}
                )
                summary_provider = await self.factory.create_summary_provider(summary_config)
                self.summary_providers["openrouter"] = summary_provider

                logger.info("OpenRouter providers initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenRouter providers: {e}")

    async def analyze_text(
        self,
        text: str,
        provider_name: Optional[str] = None,
        fallback_to_local: bool = True,
        **kwargs
    ) -> tuple[NLPResult, Optional[str]]:
        """
        Analyze text using the selected NLP provider.

        Args:
            text: Text to analyze
            provider_name: Preferred provider (None = use default)
            fallback_to_local: Whether to fallback to local on failure
            **kwargs: Additional arguments for the provider

        Returns:
            Tuple of (NLPResult, error_message)
        """
        if not self._initialized:
            await self.initialize()

        # Select provider
        selected_provider = provider_name or self.default_nlp_provider
        error_msg = None

        # Try selected provider
        if selected_provider in self.nlp_providers:
            provider = self.nlp_providers[selected_provider]

            try:
                if not provider.is_available:
                    raise ProviderNotAvailableError(
                        f"Provider {selected_provider} is not available",
                        provider_name=selected_provider
                    )

                result = await provider.analyze(text, **kwargs)

                # Track cost
                if result.metadata.get("cost_usd"):
                    self._track_cost(
                        provider=selected_provider,
                        service="nlp",
                        cost=result.metadata["cost_usd"],
                        tokens=result.metadata.get("tokens", 0),
                        model=result.metadata.get("model", "unknown")
                    )

                return result, None

            except ProviderAuthenticationError as e:
                logger.error(f"Authentication failed for {selected_provider}: {e}")
                error_msg = f"API authentication failed for {selected_provider}"
            except ProviderError as e:
                logger.error(f"Provider error for {selected_provider}: {e}")
                error_msg = f"Provider error: {str(e)}"
            except Exception as e:
                logger.error(f"Unexpected error with {selected_provider}: {e}")
                error_msg = f"Unexpected error: {str(e)}"

        # Fallback to local provider (using gRPC service)
        if fallback_to_local:
            logger.warning(f"Falling back to local NLP provider. Reason: {error_msg}")
            # Here you would call the local gRPC NLP service
            # For now, return a minimal result
            result = NLPResult(
                keywords=[],
                entities=[],
                sentiment={"label": "neutral", "score": 0.5},
                topics=[],
                provider_name="local-fallback",
                processing_time_ms=0.0,
                metadata={"fallback": True, "original_error": error_msg}
            )
            return result, error_msg

        # If no fallback, raise the error
        raise ProviderError(error_msg or "NLP analysis failed", provider_name=selected_provider)

    async def summarize_text(
        self,
        text: str,
        provider_name: Optional[str] = None,
        fallback_to_local: bool = True,
        style: str = "concise",
        max_length: Optional[int] = None,
        **kwargs
    ) -> tuple[SummaryResult, Optional[str]]:
        """
        Summarize text using the selected provider.

        Args:
            text: Text to summarize
            provider_name: Preferred provider (None = use default)
            fallback_to_local: Whether to fallback to local on failure
            style: Summary style
            max_length: Maximum summary length
            **kwargs: Additional arguments

        Returns:
            Tuple of (SummaryResult, error_message)
        """
        if not self._initialized:
            await self.initialize()

        selected_provider = provider_name or self.default_summary_provider
        error_msg = None

        # Try selected provider
        if selected_provider in self.summary_providers:
            provider = self.summary_providers[selected_provider]

            try:
                if not provider.is_available:
                    raise ProviderNotAvailableError(
                        f"Provider {selected_provider} is not available",
                        provider_name=selected_provider
                    )

                result = await provider.summarize(
                    text,
                    max_length=max_length,
                    style=style,
                    **kwargs
                )

                # Track cost
                if result.metadata.get("cost_usd"):
                    self._track_cost(
                        provider=selected_provider,
                        service="summary",
                        cost=result.metadata["cost_usd"],
                        tokens=result.metadata.get("tokens", 0),
                        model=result.metadata.get("model", "unknown")
                    )

                return result, None

            except ProviderAuthenticationError as e:
                logger.error(f"Authentication failed for {selected_provider}: {e}")
                error_msg = f"API authentication failed for {selected_provider}"
            except ProviderError as e:
                logger.error(f"Provider error for {selected_provider}: {e}")
                error_msg = f"Provider error: {str(e)}"
            except Exception as e:
                logger.error(f"Unexpected error with {selected_provider}: {e}")
                error_msg = f"Unexpected error: {str(e)}"

        # Fallback to local provider
        if fallback_to_local:
            logger.warning(f"Falling back to local Summary provider. Reason: {error_msg}")
            # Call local gRPC summary service
            result = SummaryResult(
                summary="Summary unavailable",
                key_points=[],
                action_items=[],
                provider_name="local-fallback",
                processing_time_ms=0.0,
                metadata={"fallback": True, "original_error": error_msg}
            )
            return result, error_msg

        raise ProviderError(error_msg or "Summary generation failed", provider_name=selected_provider)

    def _track_cost(
        self,
        provider: str,
        service: str,
        cost: float,
        tokens: int,
        model: str
    ) -> None:
        """Track cost entry for monitoring."""
        entry = {
            "timestamp": datetime.utcnow(),
            "provider": provider,
            "service": service,
            "model": model,
            "tokens": tokens,
            "cost_usd": cost,
        }
        self.cost_entries.append(entry)

        # Keep only last 1000 entries
        if len(self.cost_entries) > 1000:
            self.cost_entries = self.cost_entries[-1000:]

        logger.debug(f"Cost tracked: {provider}/{service} - ${cost:.6f}")

    def get_cost_stats(self, time_range: str = "daily") -> Dict[str, Any]:
        """
        Get cost statistics for the specified time range.

        Args:
            time_range: 'daily', 'weekly', or 'monthly'

        Returns:
            Cost statistics dictionary
        """
        # Calculate time threshold
        now = datetime.utcnow()
        if time_range == "daily":
            threshold = now.timestamp() - 86400
        elif time_range == "weekly":
            threshold = now.timestamp() - 604800
        else:  # monthly
            threshold = now.timestamp() - 2592000

        # Filter entries
        filtered = [
            e for e in self.cost_entries
            if e["timestamp"].timestamp() >= threshold
        ]

        # Calculate stats
        total_cost = sum(e["cost_usd"] for e in filtered)
        total_requests = len(filtered)
        total_tokens = sum(e["tokens"] for e in filtered)

        by_provider: Dict[str, Dict] = {}
        by_service: Dict[str, Dict] = {}

        for entry in filtered:
            # By provider
            if entry["provider"] not in by_provider:
                by_provider[entry["provider"]] = {"cost": 0, "requests": 0, "tokens": 0}
            by_provider[entry["provider"]]["cost"] += entry["cost_usd"]
            by_provider[entry["provider"]]["requests"] += 1
            by_provider[entry["provider"]]["tokens"] += entry["tokens"]

            # By service
            if entry["service"] not in by_service:
                by_service[entry["service"]] = {"cost": 0, "requests": 0, "tokens": 0}
            by_service[entry["service"]]["cost"] += entry["cost_usd"]
            by_service[entry["service"]]["requests"] += 1
            by_service[entry["service"]]["tokens"] += entry["tokens"]

        return {
            "total_cost": total_cost,
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "avg_cost_per_request": total_cost / total_requests if total_requests > 0 else 0,
            "by_provider": by_provider,
            "by_service": by_service,
            "time_range": time_range,
        }

    def get_available_providers(self) -> Dict[str, Any]:
        """
        Get list of available providers and their status.

        Returns:
            Dictionary with provider information
        """
        return {
            "nlp": [
                {
                    "id": name,
                    "name": provider.name,
                    "type": provider.config.provider_type.value,
                    "available": provider.is_available,
                    "cost_per_request": provider.config.cost_per_token * 1000 if provider.config.cost_per_token else 0,
                    "avg_latency_ms": provider.metrics.avg_latency_ms,
                    "capabilities": [c.value for c in provider.get_capabilities()],
                }
                for name, provider in self.nlp_providers.items()
            ],
            "summary": [
                {
                    "id": name,
                    "name": provider.name,
                    "type": provider.config.provider_type.value,
                    "available": provider.is_available,
                    "cost_per_request": provider.config.cost_per_token * 1500 if provider.config.cost_per_token else 0,
                    "avg_latency_ms": provider.metrics.avg_latency_ms,
                    "capabilities": [c.value for c in provider.get_capabilities()],
                }
                for name, provider in self.summary_providers.items()
            ],
        }

    async def shutdown(self) -> None:
        """Shutdown all providers."""
        await self.factory.shutdown_all()
        logger.info("ProviderOrchestrator shutdown complete")


# Global instance
_orchestrator: Optional[ProviderOrchestrator] = None


def get_provider_orchestrator() -> ProviderOrchestrator:
    """Get the global provider orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ProviderOrchestrator()
    return _orchestrator
