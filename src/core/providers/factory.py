"""
Provider factory for creating and managing provider instances.
"""

import logging
from typing import Dict, List, Optional, Type, Union

from .base import (
    BaseProvider,
    STTProvider,
    NLPProvider,
    SummaryProvider,
    ProviderConfig,
    ProviderType,
)
from .exceptions import ProviderNotFoundError, ProviderConfigurationError

logger = logging.getLogger(__name__)


class ProviderFactory:
    """
    Factory for creating and managing provider instances.

    Supports registration of providers and creates instances based on configuration.
    """

    def __init__(self):
        self._stt_providers: Dict[str, Type[STTProvider]] = {}
        self._nlp_providers: Dict[str, Type[NLPProvider]] = {}
        self._summary_providers: Dict[str, Type[SummaryProvider]] = {}
        self._instances: Dict[str, BaseProvider] = {}

    def register_stt_provider(
        self,
        name: str,
        provider_class: Type[STTProvider]
    ) -> None:
        """
        Register an STT provider class.

        Args:
            name: Unique name for the provider
            provider_class: Provider class (must inherit from STTProvider)
        """
        if not issubclass(provider_class, STTProvider):
            raise ProviderConfigurationError(
                f"Provider class must inherit from STTProvider: {provider_class}"
            )

        self._stt_providers[name] = provider_class
        logger.info(f"Registered STT provider: {name}")

    def register_nlp_provider(
        self,
        name: str,
        provider_class: Type[NLPProvider]
    ) -> None:
        """
        Register an NLP provider class.

        Args:
            name: Unique name for the provider
            provider_class: Provider class (must inherit from NLPProvider)
        """
        if not issubclass(provider_class, NLPProvider):
            raise ProviderConfigurationError(
                f"Provider class must inherit from NLPProvider: {provider_class}"
            )

        self._nlp_providers[name] = provider_class
        logger.info(f"Registered NLP provider: {name}")

    def register_summary_provider(
        self,
        name: str,
        provider_class: Type[SummaryProvider]
    ) -> None:
        """
        Register a Summary provider class.

        Args:
            name: Unique name for the provider
            provider_class: Provider class (must inherit from SummaryProvider)
        """
        if not issubclass(provider_class, SummaryProvider):
            raise ProviderConfigurationError(
                f"Provider class must inherit from SummaryProvider: {provider_class}"
            )

        self._summary_providers[name] = provider_class
        logger.info(f"Registered Summary provider: {name}")

    async def create_stt_provider(
        self,
        config: ProviderConfig,
        initialize: bool = True
    ) -> STTProvider:
        """
        Create an STT provider instance.

        Args:
            config: Provider configuration
            initialize: Whether to initialize the provider

        Returns:
            Initialized STT provider instance
        """
        if config.name not in self._stt_providers:
            available = ", ".join(self._stt_providers.keys())
            raise ProviderNotFoundError(
                f"STT provider '{config.name}' not found. Available: {available}",
                provider_name=config.name
            )

        provider_class = self._stt_providers[config.name]
        provider = provider_class(config)

        if initialize:
            await provider.initialize()

        # Cache instance
        instance_key = f"stt:{config.name}"
        self._instances[instance_key] = provider

        logger.info(f"Created STT provider: {config.name}")
        return provider

    async def create_nlp_provider(
        self,
        config: ProviderConfig,
        initialize: bool = True
    ) -> NLPProvider:
        """
        Create an NLP provider instance.

        Args:
            config: Provider configuration
            initialize: Whether to initialize the provider

        Returns:
            Initialized NLP provider instance
        """
        if config.name not in self._nlp_providers:
            available = ", ".join(self._nlp_providers.keys())
            raise ProviderNotFoundError(
                f"NLP provider '{config.name}' not found. Available: {available}",
                provider_name=config.name
            )

        provider_class = self._nlp_providers[config.name]
        provider = provider_class(config)

        if initialize:
            await provider.initialize()

        # Cache instance
        instance_key = f"nlp:{config.name}"
        self._instances[instance_key] = provider

        logger.info(f"Created NLP provider: {config.name}")
        return provider

    async def create_summary_provider(
        self,
        config: ProviderConfig,
        initialize: bool = True
    ) -> SummaryProvider:
        """
        Create a Summary provider instance.

        Args:
            config: Provider configuration
            initialize: Whether to initialize the provider

        Returns:
            Initialized Summary provider instance
        """
        if config.name not in self._summary_providers:
            available = ", ".join(self._summary_providers.keys())
            raise ProviderNotFoundError(
                f"Summary provider '{config.name}' not found. Available: {available}",
                provider_name=config.name
            )

        provider_class = self._summary_providers[config.name]
        provider = provider_class(config)

        if initialize:
            await provider.initialize()

        # Cache instance
        instance_key = f"summary:{config.name}"
        self._instances[instance_key] = provider

        logger.info(f"Created Summary provider: {config.name}")
        return provider

    def get_instance(self, service_type: str, name: str) -> Optional[BaseProvider]:
        """
        Get cached provider instance.

        Args:
            service_type: Type of service ('stt', 'nlp', 'summary')
            name: Provider name

        Returns:
            Provider instance or None if not found
        """
        instance_key = f"{service_type}:{name}"
        return self._instances.get(instance_key)

    def list_stt_providers(self) -> List[str]:
        """List registered STT provider names."""
        return list(self._stt_providers.keys())

    def list_nlp_providers(self) -> List[str]:
        """List registered NLP provider names."""
        return list(self._nlp_providers.keys())

    def list_summary_providers(self) -> List[str]:
        """List registered Summary provider names."""
        return list(self._summary_providers.keys())

    async def shutdown_all(self) -> None:
        """Shutdown all provider instances and clean up resources."""
        for instance_key, provider in list(self._instances.items()):
            try:
                await provider.shutdown()
                logger.info(f"Shutdown provider: {instance_key}")
            except Exception as e:
                logger.error(f"Error shutting down {instance_key}: {e}")

        self._instances.clear()


# Global factory instance
_global_factory: Optional[ProviderFactory] = None


def get_factory() -> ProviderFactory:
    """Get the global provider factory instance."""
    global _global_factory
    if _global_factory is None:
        _global_factory = ProviderFactory()
    return _global_factory


def register_default_providers():
    """Register all default providers with the factory."""
    factory = get_factory()

    # Import and register local providers
    try:
        from .local.whisper_local import WhisperLocalProvider
        factory.register_stt_provider("whisper-local", WhisperLocalProvider)
    except ImportError:
        logger.warning("WhisperLocalProvider not available")

    # Import and register cloud providers
    try:
        from .cloud.openai import OpenAISTTProvider, OpenAINLPProvider, OpenAISummaryProvider
        factory.register_stt_provider("openai-whisper", OpenAISTTProvider)
        factory.register_nlp_provider("openai-gpt4", OpenAINLPProvider)
        factory.register_summary_provider("openai-gpt4", OpenAISummaryProvider)
    except ImportError:
        logger.warning("OpenAI providers not available")

    try:
        from .cloud.deepgram import DeepgramProvider
        factory.register_stt_provider("deepgram-nova3", DeepgramProvider)
    except ImportError:
        logger.warning("Deepgram provider not available")

    # Add more provider imports as they are implemented

    logger.info("Default providers registered")
