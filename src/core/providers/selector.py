"""
Provider selector for intelligent routing and selection.

This module implements logic for automatically selecting the best provider
based on requirements, cost, performance, and availability.
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from .base import (
    BaseProvider,
    STTProvider,
    NLPProvider,
    SummaryProvider,
    ProviderCapability,
    ProviderType,
)
from .factory import ProviderFactory

logger = logging.getLogger(__name__)


@dataclass
class SelectionCriteria:
    """Criteria for selecting a provider."""

    # Required capabilities
    required_capabilities: List[ProviderCapability] = None

    # Performance requirements
    max_latency_ms: Optional[float] = None
    min_confidence: Optional[float] = None

    # Cost requirements
    max_cost_per_request: Optional[float] = None
    optimize_for_cost: bool = False

    # Provider preferences
    prefer_local: bool = False
    prefer_cloud: bool = False
    exclude_providers: List[str] = None

    # Other
    language: Optional[str] = None

    def __post_init__(self):
        if self.required_capabilities is None:
            self.required_capabilities = []
        if self.exclude_providers is None:
            self.exclude_providers = []


class ProviderSelector:
    """
    Intelligent provider selector.

    Selects the best provider based on:
    - Required capabilities
    - Performance metrics (latency, accuracy)
    - Cost optimization
    - Provider health and availability
    - Fallback chains for reliability
    """

    def __init__(self, factory: ProviderFactory):
        self.factory = factory
        self._provider_scores: Dict[str, float] = {}

    async def select_stt_provider(
        self,
        providers: List[STTProvider],
        criteria: Optional[SelectionCriteria] = None
    ) -> Optional[STTProvider]:
        """
        Select the best STT provider based on criteria.

        Args:
            providers: List of available STT providers
            criteria: Selection criteria

        Returns:
            Selected provider or None if no suitable provider found
        """
        if not providers:
            logger.warning("No STT providers available")
            return None

        if criteria is None:
            criteria = SelectionCriteria()

        # Filter providers
        filtered = self._filter_providers(providers, criteria)

        if not filtered:
            logger.warning("No STT providers match criteria")
            return None

        # Score and rank providers
        scored = self._score_providers(filtered, criteria)

        # Return best provider
        best_provider = scored[0][0] if scored else None

        if best_provider:
            logger.info(
                f"Selected STT provider: {best_provider.name} "
                f"(score: {scored[0][1]:.2f})"
            )

        return best_provider

    async def select_nlp_provider(
        self,
        providers: List[NLPProvider],
        criteria: Optional[SelectionCriteria] = None
    ) -> Optional[NLPProvider]:
        """
        Select the best NLP provider based on criteria.

        Args:
            providers: List of available NLP providers
            criteria: Selection criteria

        Returns:
            Selected provider or None if no suitable provider found
        """
        if not providers:
            logger.warning("No NLP providers available")
            return None

        if criteria is None:
            criteria = SelectionCriteria()

        filtered = self._filter_providers(providers, criteria)

        if not filtered:
            logger.warning("No NLP providers match criteria")
            return None

        scored = self._score_providers(filtered, criteria)

        best_provider = scored[0][0] if scored else None

        if best_provider:
            logger.info(
                f"Selected NLP provider: {best_provider.name} "
                f"(score: {scored[0][1]:.2f})"
            )

        return best_provider

    async def select_summary_provider(
        self,
        providers: List[SummaryProvider],
        criteria: Optional[SelectionCriteria] = None
    ) -> Optional[SummaryProvider]:
        """
        Select the best Summary provider based on criteria.

        Args:
            providers: List of available Summary providers
            criteria: Selection criteria

        Returns:
            Selected provider or None if no suitable provider found
        """
        if not providers:
            logger.warning("No Summary providers available")
            return None

        if criteria is None:
            criteria = SelectionCriteria()

        filtered = self._filter_providers(providers, criteria)

        if not filtered:
            logger.warning("No Summary providers match criteria")
            return None

        scored = self._score_providers(filtered, criteria)

        best_provider = scored[0][0] if scored else None

        if best_provider:
            logger.info(
                f"Selected Summary provider: {best_provider.name} "
                f"(score: {scored[0][1]:.2f})"
            )

        return best_provider

    def _filter_providers(
        self,
        providers: List[BaseProvider],
        criteria: SelectionCriteria
    ) -> List[BaseProvider]:
        """Filter providers based on criteria."""
        filtered = []

        for provider in providers:
            # Check if provider is available
            if not provider.is_available:
                logger.debug(f"Provider {provider.name} is not available")
                continue

            # Check if provider is excluded
            if provider.name in criteria.exclude_providers:
                logger.debug(f"Provider {provider.name} is excluded")
                continue

            # Check required capabilities
            if criteria.required_capabilities:
                provider_caps = provider.get_capabilities()
                if not all(cap in provider_caps for cap in criteria.required_capabilities):
                    logger.debug(
                        f"Provider {provider.name} missing required capabilities"
                    )
                    continue

            # Check provider type preference
            if criteria.prefer_local and provider.config.provider_type != ProviderType.LOCAL:
                logger.debug(f"Provider {provider.name} is not local (preferred)")
                continue

            if criteria.prefer_cloud and provider.config.provider_type != ProviderType.CLOUD:
                logger.debug(f"Provider {provider.name} is not cloud (preferred)")
                continue

            # Check cost constraint
            if criteria.max_cost_per_request:
                if provider.config.cost_per_request > criteria.max_cost_per_request:
                    logger.debug(
                        f"Provider {provider.name} exceeds cost limit: "
                        f"{provider.config.cost_per_request} > {criteria.max_cost_per_request}"
                    )
                    continue

            # Check latency constraint
            if criteria.max_latency_ms:
                if provider.metrics.avg_latency_ms > criteria.max_latency_ms:
                    logger.debug(
                        f"Provider {provider.name} exceeds latency limit: "
                        f"{provider.metrics.avg_latency_ms} > {criteria.max_latency_ms}"
                    )
                    continue

            filtered.append(provider)

        return filtered

    def _score_providers(
        self,
        providers: List[BaseProvider],
        criteria: SelectionCriteria
    ) -> List[tuple[BaseProvider, float]]:
        """
        Score and rank providers.

        Scoring factors:
        - Priority (from config)
        - Performance (latency, error rate)
        - Cost (if optimize_for_cost is True)
        - Availability/uptime
        """
        scored = []

        for provider in providers:
            score = 0.0

            # Priority weight (0-100 points)
            score += provider.config.priority

            # Performance weight (0-50 points)
            if provider.metrics.total_requests > 0:
                # Lower error rate = higher score
                error_rate = provider.metrics.error_rate
                score += (100 - error_rate) * 0.3

                # Lower latency = higher score (normalized to 0-20 points)
                if provider.metrics.avg_latency_ms > 0:
                    latency_score = max(0, 20 - (provider.metrics.avg_latency_ms / 100))
                    score += latency_score
            else:
                # No history, give neutral score
                score += 25

            # Cost weight (0-30 points) - only if optimizing for cost
            if criteria.optimize_for_cost:
                # Lower cost = higher score
                if provider.config.cost_per_request > 0:
                    # Normalize cost to 0-30 points (assuming max $0.10 per request)
                    cost_score = max(0, 30 - (provider.config.cost_per_request * 300))
                    score += cost_score
                else:
                    # Free provider gets full points
                    score += 30

            # Health/uptime weight (0-20 points)
            score += (provider.metrics.uptime_percentage / 100) * 20

            scored.append((provider, score))

        # Sort by score (descending)
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored

    async def create_fallback_chain(
        self,
        provider_names: List[str],
        service_type: str
    ) -> List[BaseProvider]:
        """
        Create a fallback chain of providers.

        Args:
            provider_names: Ordered list of provider names
            service_type: Type of service ('stt', 'nlp', 'summary')

        Returns:
            List of provider instances in fallback order
        """
        providers = []

        for name in provider_names:
            provider = self.factory.get_instance(service_type, name)
            if provider and provider.is_available:
                providers.append(provider)
            else:
                logger.warning(
                    f"Provider {name} not available for fallback chain"
                )

        return providers

    def get_cost_estimate(
        self,
        provider: BaseProvider,
        audio_seconds: float = 0.0,
        text_length: int = 0,
        tokens: int = 0
    ) -> float:
        """
        Estimate cost for using a provider.

        Args:
            provider: Provider instance
            audio_seconds: Audio duration in seconds (for STT)
            text_length: Text length in characters (for NLP/Summary)
            tokens: Token count (if known)

        Returns:
            Estimated cost in USD
        """
        cost = 0.0

        # Base request cost
        cost += provider.config.cost_per_request

        # Audio-based cost (STT)
        if audio_seconds > 0 and provider.config.cost_per_minute > 0:
            cost += (audio_seconds / 60) * provider.config.cost_per_minute

        # Token-based cost (NLP/Summary)
        if tokens > 0 and provider.config.cost_per_token > 0:
            cost += tokens * provider.config.cost_per_token
        elif text_length > 0 and provider.config.cost_per_token > 0:
            # Rough estimate: ~4 chars per token
            estimated_tokens = text_length / 4
            cost += estimated_tokens * provider.config.cost_per_token

        return cost
