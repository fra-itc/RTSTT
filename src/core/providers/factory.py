"""
Provider Factory - Create and manage STT providers.

This module provides a centralized way to create and manage different
STT providers, with configuration management and health monitoring.
"""

import logging
from typing import Dict, Optional, Type, List
from enum import Enum

from .base import STTProvider, ProviderConfig, ProviderInfo
from .cloud.openai import OpenAISTTProvider
from .cloud.deepgram import DeepgramProvider
from .cloud.assemblyai import AssemblyAIProvider
from .local.whisper_local import LocalWhisperProvider

logger = logging.getLogger(__name__)


class ProviderName(Enum):
    """Enumeration of available providers."""
    LOCAL_WHISPER = "local_whisper"
    OPENAI = "openai"
    DEEPGRAM = "deepgram"
    ASSEMBLYAI = "assemblyai"


class ProviderRegistry:
    """
    Registry of available STT providers.

    Manages provider classes and their instantiation.
    """

    # Map of provider names to classes
    _providers: Dict[str, Type[STTProvider]] = {
        ProviderName.LOCAL_WHISPER.value: LocalWhisperProvider,
        ProviderName.OPENAI.value: OpenAISTTProvider,
        ProviderName.DEEPGRAM.value: DeepgramProvider,
        ProviderName.ASSEMBLYAI.value: AssemblyAIProvider,
    }

    # Active provider instances
    _instances: Dict[str, STTProvider] = {}

    @classmethod
    def register(cls, name: str, provider_class: Type[STTProvider]):
        """
        Register a new provider.

        Args:
            name: Provider name
            provider_class: Provider class
        """
        cls._providers[name] = provider_class
        logger.info(f"Registered provider: {name}")

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available provider names."""
        return list(cls._providers.keys())

    @classmethod
    def get_provider_class(cls, name: str) -> Optional[Type[STTProvider]]:
        """
        Get provider class by name.

        Args:
            name: Provider name

        Returns:
            Optional[Type[STTProvider]]: Provider class or None
        """
        return cls._providers.get(name)

    @classmethod
    async def create_provider(
        cls,
        name: str,
        config: Optional[ProviderConfig] = None,
        auto_initialize: bool = True,
        cache: bool = True
    ) -> Optional[STTProvider]:
        """
        Create a provider instance.

        Args:
            name: Provider name
            config: Provider configuration (uses defaults if not provided)
            auto_initialize: Automatically initialize the provider
            cache: Cache the instance for reuse

        Returns:
            Optional[STTProvider]: Provider instance or None if creation failed
        """
        # Check if we have a cached instance
        if cache and name in cls._instances:
            logger.info(f"Returning cached provider: {name}")
            return cls._instances[name]

        # Get provider class
        provider_class = cls._providers.get(name)
        if not provider_class:
            logger.error(f"Unknown provider: {name}")
            return None

        # Create config if not provided
        if config is None:
            config = ProviderConfig(provider_name=name)

        try:
            # Instantiate provider
            provider = provider_class(config)

            # Initialize if requested
            if auto_initialize:
                success = await provider.initialize()
                if not success:
                    logger.error(f"Failed to initialize provider: {name}")
                    return None

            # Cache if requested
            if cache:
                cls._instances[name] = provider

            logger.info(f"Created provider: {name}")
            return provider

        except Exception as e:
            logger.error(f"Failed to create provider {name}: {e}")
            return None

    @classmethod
    async def get_or_create_provider(
        cls,
        name: str,
        config: Optional[ProviderConfig] = None
    ) -> Optional[STTProvider]:
        """
        Get cached provider or create new one.

        Args:
            name: Provider name
            config: Provider configuration

        Returns:
            Optional[STTProvider]: Provider instance
        """
        if name in cls._instances:
            return cls._instances[name]

        return await cls.create_provider(name, config, auto_initialize=True, cache=True)

    @classmethod
    async def cleanup_provider(cls, name: str):
        """
        Cleanup and remove a provider instance.

        Args:
            name: Provider name
        """
        if name in cls._instances:
            await cls._instances[name].cleanup()
            del cls._instances[name]
            logger.info(f"Cleaned up provider: {name}")

    @classmethod
    async def cleanup_all(cls):
        """Cleanup all provider instances."""
        for name in list(cls._instances.keys()):
            await cls.cleanup_provider(name)


class ProviderFactory:
    """
    Factory for creating STT providers with common configurations.
    """

    @staticmethod
    async def create_local_whisper(
        model: str = "large-v3",
        language: Optional[str] = None,
        device: str = "cuda"
    ) -> Optional[LocalWhisperProvider]:
        """
        Create local Whisper provider.

        Args:
            model: Model name
            language: Default language
            device: Device to use

        Returns:
            Optional[LocalWhisperProvider]: Provider instance
        """
        config = ProviderConfig(
            provider_name=ProviderName.LOCAL_WHISPER.value,
            model=model,
            language=language,
            additional_params={"device": device}
        )

        return await ProviderRegistry.create_provider(
            ProviderName.LOCAL_WHISPER.value,
            config,
            auto_initialize=True
        )

    @staticmethod
    async def create_openai(
        api_key: str,
        model: str = "whisper-1",
        language: Optional[str] = None
    ) -> Optional[OpenAISTTProvider]:
        """
        Create OpenAI Whisper API provider.

        Args:
            api_key: OpenAI API key
            model: Model name
            language: Default language

        Returns:
            Optional[OpenAISTTProvider]: Provider instance
        """
        config = ProviderConfig(
            provider_name=ProviderName.OPENAI.value,
            api_key=api_key,
            model=model,
            language=language
        )

        return await ProviderRegistry.create_provider(
            ProviderName.OPENAI.value,
            config,
            auto_initialize=True
        )

    @staticmethod
    async def create_deepgram(
        api_key: str,
        model: str = "nova-2",
        language: Optional[str] = None,
        enable_diarization: bool = False
    ) -> Optional[DeepgramProvider]:
        """
        Create Deepgram provider.

        Args:
            api_key: Deepgram API key
            model: Model name (nova-2, nova-3, whisper-large, etc.)
            language: Default language
            enable_diarization: Enable speaker diarization

        Returns:
            Optional[DeepgramProvider]: Provider instance
        """
        config = ProviderConfig(
            provider_name=ProviderName.DEEPGRAM.value,
            api_key=api_key,
            model=model,
            language=language,
            additional_params={
                "diarize": enable_diarization,
                "punctuate": True,
                "smart_format": True
            }
        )

        return await ProviderRegistry.create_provider(
            ProviderName.DEEPGRAM.value,
            config,
            auto_initialize=True
        )

    @staticmethod
    async def create_assemblyai(
        api_key: str,
        model: str = "best",
        language: Optional[str] = None,
        enable_speaker_labels: bool = False,
        enable_sentiment: bool = False
    ) -> Optional[AssemblyAIProvider]:
        """
        Create AssemblyAI provider.

        Args:
            api_key: AssemblyAI API key
            model: Model name
            language: Default language
            enable_speaker_labels: Enable speaker diarization
            enable_sentiment: Enable sentiment analysis

        Returns:
            Optional[AssemblyAIProvider]: Provider instance
        """
        config = ProviderConfig(
            provider_name=ProviderName.ASSEMBLYAI.value,
            api_key=api_key,
            model=model,
            language=language,
            additional_params={
                "speaker_labels": enable_speaker_labels,
                "sentiment_analysis": enable_sentiment
            }
        )

        return await ProviderRegistry.create_provider(
            ProviderName.ASSEMBLYAI.value,
            config,
            auto_initialize=True
        )

    @staticmethod
    async def create_from_env(provider_name: str) -> Optional[STTProvider]:
        """
        Create provider from environment variables.

        Looks for:
        - {PROVIDER}_API_KEY
        - {PROVIDER}_MODEL
        - {PROVIDER}_LANGUAGE

        Args:
            provider_name: Provider name

        Returns:
            Optional[STTProvider]: Provider instance
        """
        import os

        provider_upper = provider_name.upper()

        api_key = os.getenv(f"{provider_upper}_API_KEY")
        model = os.getenv(f"{provider_upper}_MODEL")
        language = os.getenv(f"{provider_upper}_LANGUAGE")

        config = ProviderConfig(
            provider_name=provider_name,
            api_key=api_key,
            model=model,
            language=language
        )

        return await ProviderRegistry.create_provider(
            provider_name,
            config,
            auto_initialize=True
        )


class ProviderSelector:
    """
    Helper to select the best provider based on requirements.
    """

    @staticmethod
    async def select_provider(
        requirements: Dict[str, any],
        available_providers: Optional[List[str]] = None
    ) -> Optional[STTProvider]:
        """
        Select and create best provider based on requirements.

        Args:
            requirements: Dict with keys like:
                - streaming: bool
                - diarization: bool
                - max_cost_per_minute: float
                - min_accuracy: float
                - requires_offline: bool
            available_providers: List of provider names to consider

        Returns:
            Optional[STTProvider]: Selected provider instance
        """
        if available_providers is None:
            available_providers = ProviderRegistry.get_available_providers()

        # Filter providers based on requirements
        candidates = []

        for name in available_providers:
            provider_class = ProviderRegistry.get_provider_class(name)
            if not provider_class:
                continue

            # Create temporary instance to get info
            temp_config = ProviderConfig(provider_name=name)
            temp_provider = provider_class(temp_config)
            info = temp_provider.get_info()

            # Check requirements
            if requirements.get("streaming") and ProviderCapability.STREAMING not in info.capabilities:
                continue

            if requirements.get("diarization") and ProviderCapability.DIARIZATION not in info.capabilities:
                continue

            max_cost = requirements.get("max_cost_per_minute")
            if max_cost is not None and info.cost_per_minute and info.cost_per_minute > max_cost:
                continue

            if requirements.get("requires_offline") and info.requires_api_key:
                continue

            candidates.append((name, info))

        if not candidates:
            logger.warning("No providers match requirements")
            return None

        # Sort by cost (prefer lower cost)
        candidates.sort(key=lambda x: x[1].cost_per_minute or 0)

        # Create the best candidate
        selected_name = candidates[0][0]
        logger.info(f"Selected provider: {selected_name}")

        return await ProviderRegistry.get_or_create_provider(selected_name)
