"""
STTProvider Base Class - Abstract provider interface for STT services.

This module defines the base abstraction for all STT providers (local and cloud).
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, AsyncIterator, Union
from pathlib import Path
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """Types of STT providers."""
    LOCAL = "local"
    CLOUD = "cloud"


class ProviderCapability(Enum):
    """Capabilities that providers may support."""
    STREAMING = "streaming"
    BATCH = "batch"
    DIARIZATION = "diarization"
    WORD_TIMESTAMPS = "word_timestamps"
    PUNCTUATION = "punctuation"
    SPEAKER_LABELS = "speaker_labels"
    TRANSLATION = "translation"
    LANGUAGE_DETECTION = "language_detection"
    CUSTOM_VOCABULARY = "custom_vocabulary"
    PROFANITY_FILTER = "profanity_filter"


@dataclass
class WordTimestamp:
    """Word-level timestamp information."""
    word: str
    start: float
    end: float
    confidence: Optional[float] = None


@dataclass
class TranscriptionSegment:
    """Represents a single transcription segment with timing information."""
    text: str
    start: float
    end: float
    confidence: Optional[float] = None
    speaker: Optional[str] = None
    words: Optional[List[WordTimestamp]] = None


@dataclass
class STTResult:
    """Standardized STT result across all providers."""
    text: str
    segments: List[TranscriptionSegment]
    language: str
    provider: str
    model: str
    duration: Optional[float] = None
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderConfig:
    """Configuration for STT provider."""
    provider_name: str
    api_key: Optional[str] = None
    model: Optional[str] = None
    language: Optional[str] = None
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderInfo:
    """Information about a provider's capabilities and pricing."""
    name: str
    type: ProviderType
    capabilities: List[ProviderCapability]
    supported_languages: List[str]
    models: List[str]
    cost_per_minute: Optional[float] = None  # USD per minute
    latency_ms: Optional[int] = None  # Typical latency in milliseconds
    max_audio_length: Optional[int] = None  # Max audio length in seconds
    requires_api_key: bool = False


class STTProvider(ABC):
    """
    Abstract base class for all STT providers.

    All STT providers (local and cloud) must implement this interface.
    """

    def __init__(self, config: ProviderConfig):
        """
        Initialize the STT provider.

        Args:
            config: Provider configuration
        """
        self.config = config
        self._is_initialized = False
        logger.info(f"Initializing {config.provider_name} provider")

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the provider (load models, verify API keys, etc.).

        Returns:
            bool: True if initialization successful
        """
        pass

    @abstractmethod
    async def transcribe(
        self,
        audio: Union[str, Path, np.ndarray, bytes],
        language: Optional[str] = None,
        **kwargs
    ) -> STTResult:
        """
        Transcribe audio to text (batch mode).

        Args:
            audio: Audio data (file path, numpy array, or bytes)
            language: Target language code (e.g., "it", "en")
            **kwargs: Provider-specific parameters

        Returns:
            STTResult: Transcription result
        """
        pass

    @abstractmethod
    async def transcribe_streaming(
        self,
        audio_stream: AsyncIterator[bytes],
        language: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[STTResult]:
        """
        Transcribe audio stream in real-time.

        Args:
            audio_stream: Async iterator of audio chunks
            language: Target language code
            **kwargs: Provider-specific parameters

        Yields:
            STTResult: Partial transcription results
        """
        pass

    @abstractmethod
    def get_info(self) -> ProviderInfo:
        """
        Get provider information and capabilities.

        Returns:
            ProviderInfo: Provider details
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if provider is healthy and available.

        Returns:
            bool: True if provider is healthy
        """
        pass

    @abstractmethod
    async def estimate_cost(self, audio_duration_seconds: float) -> float:
        """
        Estimate cost for transcribing audio of given duration.

        Args:
            audio_duration_seconds: Duration of audio in seconds

        Returns:
            float: Estimated cost in USD
        """
        pass

    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._is_initialized

    async def cleanup(self):
        """Cleanup provider resources."""
        logger.info(f"Cleaning up {self.config.provider_name} provider")
        self._is_initialized = False


class CloudSTTProvider(STTProvider):
    """
    Base class for cloud-based STT providers.

    Provides common functionality for cloud providers (API calls, rate limiting, etc.).
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.base_url: Optional[str] = None
        self.session = None  # aiohttp session

    async def _verify_api_key(self) -> bool:
        """
        Verify API key is valid.

        Returns:
            bool: True if API key is valid
        """
        if not self.api_key:
            logger.error(f"{self.config.provider_name}: API key is required")
            return False
        return True

    async def _handle_rate_limit(self, retry_after: int):
        """
        Handle rate limit responses.

        Args:
            retry_after: Seconds to wait before retrying
        """
        import asyncio
        logger.warning(f"{self.config.provider_name}: Rate limited. Retrying after {retry_after}s")
        await asyncio.sleep(retry_after)

    async def cleanup(self):
        """Cleanup HTTP session and resources."""
        if self.session:
            await self.session.close()
            self.session = None
        await super().cleanup()


class LocalSTTProvider(STTProvider):
    """
    Base class for local STT providers.

    Provides common functionality for local providers (model loading, GPU management, etc.).
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.model = None
        self.device = "cuda"  # or "cpu"

    async def _load_model(self):
        """Load the model into memory."""
        pass

    async def cleanup(self):
        """Cleanup model and GPU resources."""
        if self.model:
            del self.model
            self.model = None
        await super().cleanup()
