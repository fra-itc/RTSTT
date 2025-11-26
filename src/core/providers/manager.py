"""
Provider Manager - Manage STT provider lifecycle and switching.

This service handles:
- Provider initialization and cleanup
- Dynamic provider switching
- Fallback chains
- Cost tracking
- Health monitoring
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

from .base import STTProvider, ProviderConfig, STTResult
from .factory import ProviderRegistry, ProviderFactory

logger = logging.getLogger(__name__)


@dataclass
class UsageRecord:
    """Record of provider usage."""
    provider_name: str
    timestamp: datetime
    audio_duration_seconds: float
    cost: float
    success: bool
    error: Optional[str] = None


@dataclass
class ProviderHealth:
    """Health status of a provider."""
    provider_name: str
    is_healthy: bool
    last_check: datetime
    consecutive_failures: int = 0
    last_error: Optional[str] = None


class ProviderManager:
    """
    Manages multiple STT providers with automatic fallback and cost tracking.
    """

    def __init__(self):
        self.primary_provider: Optional[STTProvider] = None
        self.fallback_providers: List[STTProvider] = []

        # Usage tracking
        self.usage_records: List[UsageRecord] = []
        self.total_cost: float = 0.0
        self.total_duration: float = 0.0

        # Health monitoring
        self.health_status: Dict[str, ProviderHealth] = {}
        self.health_check_interval: int = 300  # 5 minutes

        # Configuration
        self.auto_fallback: bool = True
        self.max_retries: int = 2

    async def set_primary_provider(
        self,
        provider: STTProvider,
        fallback_chain: Optional[List[STTProvider]] = None
    ):
        """
        Set the primary provider and optional fallback chain.

        Args:
            provider: Primary provider
            fallback_chain: List of fallback providers (in order)
        """
        self.primary_provider = provider
        self.fallback_providers = fallback_chain or []

        logger.info(f"Primary provider set: {provider.config.provider_name}")
        if self.fallback_providers:
            fallback_names = [p.config.provider_name for p in self.fallback_providers]
            logger.info(f"Fallback chain: {fallback_names}")

        # Initialize health status
        await self._update_health_status(provider.config.provider_name)
        for fb in self.fallback_providers:
            await self._update_health_status(fb.config.provider_name)

    async def transcribe(
        self,
        audio: Any,
        language: Optional[str] = None,
        use_fallback: bool = True,
        **kwargs
    ) -> Optional[STTResult]:
        """
        Transcribe audio using primary provider with automatic fallback.

        Args:
            audio: Audio data
            language: Target language
            use_fallback: Whether to use fallback providers on failure
            **kwargs: Provider-specific parameters

        Returns:
            Optional[STTResult]: Transcription result or None
        """
        if not self.primary_provider:
            logger.error("No primary provider set")
            return None

        # Try primary provider
        result = await self._transcribe_with_provider(
            self.primary_provider,
            audio,
            language,
            **kwargs
        )

        if result:
            return result

        # Try fallback providers if enabled
        if use_fallback and self.fallback_providers:
            logger.warning("Primary provider failed, trying fallbacks")

            for i, fallback in enumerate(self.fallback_providers):
                logger.info(f"Trying fallback provider {i+1}: {fallback.config.provider_name}")

                result = await self._transcribe_with_provider(
                    fallback,
                    audio,
                    language,
                    **kwargs
                )

                if result:
                    logger.info(f"Fallback provider succeeded: {fallback.config.provider_name}")
                    return result

        logger.error("All providers failed")
        return None

    async def _transcribe_with_provider(
        self,
        provider: STTProvider,
        audio: Any,
        language: Optional[str] = None,
        **kwargs
    ) -> Optional[STTResult]:
        """
        Transcribe with a specific provider and track usage.

        Args:
            provider: Provider to use
            audio: Audio data
            language: Target language
            **kwargs: Additional parameters

        Returns:
            Optional[STTResult]: Result or None on failure
        """
        provider_name = provider.config.provider_name
        start_time = datetime.now()

        try:
            # Transcribe
            result = await provider.transcribe(audio, language, **kwargs)

            # Calculate duration and cost
            duration = result.duration or 0.0
            cost = await provider.estimate_cost(duration)

            # Record successful usage
            self._record_usage(
                provider_name=provider_name,
                timestamp=start_time,
                duration=duration,
                cost=cost,
                success=True
            )

            # Update health status
            await self._update_health_status(provider_name, is_healthy=True)

            return result

        except Exception as e:
            logger.error(f"Provider {provider_name} failed: {e}")

            # Record failed usage
            self._record_usage(
                provider_name=provider_name,
                timestamp=start_time,
                duration=0.0,
                cost=0.0,
                success=False,
                error=str(e)
            )

            # Update health status
            await self._update_health_status(provider_name, is_healthy=False, error=str(e))

            return None

    def _record_usage(
        self,
        provider_name: str,
        timestamp: datetime,
        duration: float,
        cost: float,
        success: bool,
        error: Optional[str] = None
    ):
        """Record provider usage."""
        record = UsageRecord(
            provider_name=provider_name,
            timestamp=timestamp,
            audio_duration_seconds=duration,
            cost=cost,
            success=success,
            error=error
        )

        self.usage_records.append(record)

        if success:
            self.total_cost += cost
            self.total_duration += duration

    async def _update_health_status(
        self,
        provider_name: str,
        is_healthy: Optional[bool] = None,
        error: Optional[str] = None
    ):
        """Update provider health status."""
        if provider_name not in self.health_status:
            self.health_status[provider_name] = ProviderHealth(
                provider_name=provider_name,
                is_healthy=True,
                last_check=datetime.now()
            )

        health = self.health_status[provider_name]

        if is_healthy is not None:
            health.is_healthy = is_healthy
            health.last_check = datetime.now()

            if is_healthy:
                health.consecutive_failures = 0
                health.last_error = None
            else:
                health.consecutive_failures += 1
                health.last_error = error

    async def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics.

        Returns:
            Dict with usage stats
        """
        # Calculate per-provider stats
        provider_stats = {}

        for record in self.usage_records:
            name = record.provider_name
            if name not in provider_stats:
                provider_stats[name] = {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "total_duration": 0.0,
                    "total_cost": 0.0,
                }

            stats = provider_stats[name]
            stats["total_requests"] += 1

            if record.success:
                stats["successful_requests"] += 1
                stats["total_duration"] += record.audio_duration_seconds
                stats["total_cost"] += record.cost
            else:
                stats["failed_requests"] += 1

        return {
            "total_cost": self.total_cost,
            "total_duration_seconds": self.total_duration,
            "total_duration_minutes": self.total_duration / 60.0,
            "total_requests": len(self.usage_records),
            "provider_stats": provider_stats,
            "health_status": {
                name: {
                    "is_healthy": health.is_healthy,
                    "last_check": health.last_check.isoformat(),
                    "consecutive_failures": health.consecutive_failures,
                    "last_error": health.last_error
                }
                for name, health in self.health_status.items()
            }
        }

    async def get_cost_estimate(
        self,
        duration_seconds: float,
        provider_name: Optional[str] = None
    ) -> float:
        """
        Estimate cost for transcription.

        Args:
            duration_seconds: Audio duration
            provider_name: Provider to estimate for (uses primary if not specified)

        Returns:
            float: Estimated cost
        """
        provider = self.primary_provider

        if provider_name:
            # Find provider by name
            if self.primary_provider.config.provider_name == provider_name:
                provider = self.primary_provider
            else:
                for fb in self.fallback_providers:
                    if fb.config.provider_name == provider_name:
                        provider = fb
                        break

        if not provider:
            return 0.0

        return await provider.estimate_cost(duration_seconds)

    async def check_all_health(self) -> Dict[str, bool]:
        """
        Check health of all providers.

        Returns:
            Dict mapping provider names to health status
        """
        results = {}

        if self.primary_provider:
            is_healthy = await self.primary_provider.health_check()
            await self._update_health_status(
                self.primary_provider.config.provider_name,
                is_healthy=is_healthy
            )
            results[self.primary_provider.config.provider_name] = is_healthy

        for fb in self.fallback_providers:
            is_healthy = await fb.health_check()
            await self._update_health_status(
                fb.config.provider_name,
                is_healthy=is_healthy
            )
            results[fb.config.provider_name] = is_healthy

        return results

    async def switch_provider(self, provider_name: str) -> bool:
        """
        Switch to a different provider.

        Args:
            provider_name: Name of provider to switch to

        Returns:
            bool: True if switch successful
        """
        # Check if it's already primary
        if self.primary_provider and self.primary_provider.config.provider_name == provider_name:
            logger.info(f"Already using {provider_name}")
            return True

        # Check if it's in fallback chain
        for i, fb in enumerate(self.fallback_providers):
            if fb.config.provider_name == provider_name:
                # Promote to primary
                old_primary = self.primary_provider
                self.primary_provider = fb
                self.fallback_providers.pop(i)

                if old_primary:
                    self.fallback_providers.insert(0, old_primary)

                logger.info(f"Switched to provider: {provider_name}")
                return True

        # Provider not found
        logger.error(f"Provider not found: {provider_name}")
        return False

    def export_usage_report(self, filepath: str):
        """
        Export usage report to JSON file.

        Args:
            filepath: Output file path
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_cost": self.total_cost,
            "total_duration_seconds": self.total_duration,
            "total_requests": len(self.usage_records),
            "records": [
                {
                    "provider": r.provider_name,
                    "timestamp": r.timestamp.isoformat(),
                    "duration": r.audio_duration_seconds,
                    "cost": r.cost,
                    "success": r.success,
                    "error": r.error
                }
                for r in self.usage_records
            ]
        }

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Usage report exported to: {filepath}")

    async def cleanup(self):
        """Cleanup all providers."""
        if self.primary_provider:
            await self.primary_provider.cleanup()

        for fb in self.fallback_providers:
            await fb.cleanup()

        logger.info("Provider manager cleaned up")
