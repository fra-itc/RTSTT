"""
Base classes and interfaces for provider abstraction layer.

This module defines the abstract base classes that all providers must implement,
along with configuration structures and enums.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime


class ProviderType(str, Enum):
    """Types of providers."""

    LOCAL = "local"
    CLOUD = "cloud"
    HYBRID = "hybrid"


class ProviderCapability(str, Enum):
    """Capabilities that a provider can support."""

    # STT capabilities
    STREAMING_STT = "streaming_stt"
    BATCH_STT = "batch_stt"
    REALTIME_STT = "realtime_stt"
    MULTILINGUAL = "multilingual"
    VAD = "vad"  # Voice Activity Detection
    DIARIZATION = "diarization"  # Speaker diarization
    PUNCTUATION = "punctuation"

    # NLP capabilities
    KEYWORD_EXTRACTION = "keyword_extraction"
    ENTITY_RECOGNITION = "entity_recognition"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    TOPIC_MODELING = "topic_modeling"
    LANGUAGE_DETECTION = "language_detection"

    # Summary capabilities
    EXTRACTIVE_SUMMARY = "extractive_summary"
    ABSTRACTIVE_SUMMARY = "abstractive_summary"
    KEY_POINTS = "key_points"
    ACTION_ITEMS = "action_items"

    # Performance capabilities
    GPU_ACCELERATION = "gpu_acceleration"
    BATCH_PROCESSING = "batch_processing"
    LOW_LATENCY = "low_latency"


@dataclass
class ProviderMetrics:
    """Performance metrics for a provider."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    last_request_time: Optional[datetime] = None
    total_cost_usd: float = 0.0
    total_tokens: int = 0  # For API providers
    total_audio_seconds: float = 0.0  # For STT providers
    error_rate: float = 0.0
    uptime_percentage: float = 100.0


@dataclass
class ProviderConfig:
    """Configuration for a provider."""

    name: str
    provider_type: ProviderType
    enabled: bool = True
    priority: int = 0  # Higher priority = preferred provider
    max_retries: int = 3
    timeout_seconds: float = 30.0

    # Cost configuration
    cost_per_request: float = 0.0  # USD per request
    cost_per_minute: float = 0.0  # USD per minute (for STT)
    cost_per_token: float = 0.0  # USD per token (for NLP/Summary)

    # Rate limiting
    max_requests_per_minute: Optional[int] = None
    max_concurrent_requests: Optional[int] = None

    # Authentication
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None

    # Provider-specific settings
    extra_config: Dict[str, Any] = field(default_factory=dict)

    # Capabilities
    capabilities: List[ProviderCapability] = field(default_factory=list)


class BaseProvider(ABC):
    """Abstract base class for all providers."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.metrics = ProviderMetrics()
        self._is_initialized = False
        self._is_healthy = True

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider (load models, connect to API, etc.)."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the provider and clean up resources."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is healthy and available."""
        pass

    @abstractmethod
    def get_capabilities(self) -> List[ProviderCapability]:
        """Return list of capabilities this provider supports."""
        pass

    @property
    def name(self) -> str:
        """Get provider name."""
        return self.config.name

    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._is_initialized

    @property
    def is_healthy(self) -> bool:
        """Check if provider is healthy."""
        return self._is_healthy

    @property
    def is_available(self) -> bool:
        """Check if provider is available for use."""
        return self.config.enabled and self._is_initialized and self._is_healthy

    def update_metrics(
        self,
        success: bool,
        latency_ms: float,
        cost_usd: float = 0.0,
        tokens: int = 0,
        audio_seconds: float = 0.0
    ) -> None:
        """Update provider metrics."""
        self.metrics.total_requests += 1
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1

        self.metrics.total_latency_ms += latency_ms
        self.metrics.avg_latency_ms = (
            self.metrics.total_latency_ms / self.metrics.total_requests
        )
        self.metrics.total_cost_usd += cost_usd
        self.metrics.total_tokens += tokens
        self.metrics.total_audio_seconds += audio_seconds
        self.metrics.last_request_time = datetime.utcnow()

        if self.metrics.total_requests > 0:
            self.metrics.error_rate = (
                self.metrics.failed_requests / self.metrics.total_requests
            ) * 100


@dataclass
class STTResult:
    """Result from an STT provider."""

    text: str
    language: Optional[str] = None
    confidence: float = 0.0
    words: List[Dict[str, Any]] = field(default_factory=list)  # Word-level timing
    alternatives: List[str] = field(default_factory=list)
    audio_duration_seconds: float = 0.0
    processing_time_ms: float = 0.0
    provider_name: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class STTProvider(BaseProvider):
    """Abstract base class for Speech-to-Text providers."""

    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        sample_rate: int = 16000,
        language: str = "",
        model: str = "",
        **kwargs
    ) -> STTResult:
        """
        Transcribe audio to text.

        Args:
            audio_data: Raw audio bytes (PCM format)
            sample_rate: Audio sample rate in Hz
            language: Language code (e.g., 'en', 'it', 'es') or empty for auto-detect
            model: Model identifier (provider-specific)
            **kwargs: Provider-specific parameters

        Returns:
            STTResult with transcription and metadata
        """
        pass

    @abstractmethod
    async def transcribe_streaming(
        self,
        audio_stream,  # AsyncIterator[bytes]
        sample_rate: int = 16000,
        language: str = "",
        **kwargs
    ):
        """
        Transcribe audio from a stream (for real-time STT).

        Args:
            audio_stream: Async iterator yielding audio chunks
            sample_rate: Audio sample rate in Hz
            language: Language code or empty for auto-detect
            **kwargs: Provider-specific parameters

        Yields:
            Partial STTResults as they become available
        """
        pass


@dataclass
class NLPResult:
    """Result from an NLP provider."""

    keywords: List[Dict[str, Any]] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    sentiment: Dict[str, Any] = field(default_factory=dict)
    topics: List[Dict[str, Any]] = field(default_factory=list)
    language: Optional[str] = None
    processing_time_ms: float = 0.0
    provider_name: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class NLPProvider(BaseProvider):
    """Abstract base class for NLP providers."""

    @abstractmethod
    async def analyze(
        self,
        text: str,
        language: str = "",
        **kwargs
    ) -> NLPResult:
        """
        Analyze text for keywords, entities, sentiment, etc.

        Args:
            text: Input text to analyze
            language: Language code (optional)
            **kwargs: Provider-specific parameters

        Returns:
            NLPResult with analysis results
        """
        pass


@dataclass
class SummaryResult:
    """Result from a Summary provider."""

    summary: str
    key_points: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    confidence: float = 0.0
    processing_time_ms: float = 0.0
    provider_name: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class SummaryProvider(BaseProvider):
    """Abstract base class for Summary providers."""

    @abstractmethod
    async def summarize(
        self,
        text: str,
        max_length: Optional[int] = None,
        style: str = "concise",
        **kwargs
    ) -> SummaryResult:
        """
        Generate summary from text.

        Args:
            text: Input text to summarize
            max_length: Maximum length of summary (in words or sentences)
            style: Summary style ('concise', 'detailed', 'bullet_points', etc.)
            **kwargs: Provider-specific parameters

        Returns:
            SummaryResult with summary and key points
        """
        pass
