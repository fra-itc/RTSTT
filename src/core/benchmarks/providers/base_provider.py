"""
Base provider abstraction for STT benchmarking.

Defines the common interface that all STT providers must implement.
"""

import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """Type of STT provider."""
    LOCAL = "local"
    CLOUD = "cloud"


@dataclass
class TranscriptionResult:
    """Result from STT transcription with timing and metadata."""
    text: str
    confidence: Optional[float] = None
    language: Optional[str] = None
    processing_time_ms: float = 0.0
    audio_duration_ms: float = 0.0
    segments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def rtfx(self) -> float:
        """Real-Time Factor: processing_time / audio_duration."""
        if self.audio_duration_ms > 0:
            return self.processing_time_ms / self.audio_duration_ms
        return 0.0


class STTProvider(ABC):
    """
    Abstract base class for all STT providers.

    All providers (local and cloud) must implement this interface to be
    benchmarked consistently.
    """

    def __init__(
        self,
        provider_name: str,
        model_name: str,
        provider_type: ProviderType,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize STT provider.

        Args:
            provider_name: Human-readable provider name (e.g., "Deepgram")
            model_name: Specific model name (e.g., "Nova-3")
            provider_type: LOCAL or CLOUD
            config: Provider-specific configuration
        """
        self.provider_name = provider_name
        self.model_name = model_name
        self.provider_type = provider_type
        self.config = config or {}
        self._is_initialized = False

        # Metrics tracking
        self.total_audio_processed_ms = 0.0
        self.total_processing_time_ms = 0.0
        self.transcription_count = 0

        logger.info(f"Initializing {provider_name} ({model_name}) - {provider_type.value}")

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the provider (load model, authenticate API, etc.).

        Returns:
            bool: True if initialization successful
        """
        pass

    @abstractmethod
    def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio file to text.

        Args:
            audio_path: Path to audio file
            language: Optional language hint (ISO 639-1 code)

        Returns:
            TranscriptionResult: Transcription with timing and metadata
        """
        pass

    @abstractmethod
    def transcribe_stream(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcribe streaming audio data.

        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate in Hz
            language: Optional language hint

        Returns:
            TranscriptionResult: Transcription with timing
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """
        Cleanup resources (unload model, close connections, etc.).
        """
        pass

    @abstractmethod
    def get_cost_per_minute(self) -> float:
        """
        Get cost per minute of audio in USD.

        Returns:
            float: Cost in USD (0.0 for local models)
        """
        pass

    @abstractmethod
    def supports_language(self, language: str) -> bool:
        """
        Check if provider supports a specific language.

        Args:
            language: ISO 639-1 language code

        Returns:
            bool: True if language is supported
        """
        pass

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get summary of collected metrics.

        Returns:
            Dict with metrics data
        """
        avg_rtfx = 0.0
        if self.total_audio_processed_ms > 0:
            avg_rtfx = self.total_processing_time_ms / self.total_audio_processed_ms

        return {
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "provider_type": self.provider_type.value,
            "transcription_count": self.transcription_count,
            "total_audio_processed_seconds": self.total_audio_processed_ms / 1000,
            "total_processing_time_seconds": self.total_processing_time_ms / 1000,
            "average_rtfx": avg_rtfx,
            "cost_per_minute": self.get_cost_per_minute(),
        }

    def _update_metrics(self, result: TranscriptionResult) -> None:
        """
        Update internal metrics tracking.

        Args:
            result: TranscriptionResult to extract metrics from
        """
        self.total_audio_processed_ms += result.audio_duration_ms
        self.total_processing_time_ms += result.processing_time_ms
        self.transcription_count += 1

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get provider information.

        Returns:
            Dict with provider details
        """
        return {
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "provider_type": self.provider_type.value,
            "is_initialized": self._is_initialized,
            "config": self.config,
        }

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()

    def __repr__(self) -> str:
        return f"{self.provider_name}({self.model_name})"
