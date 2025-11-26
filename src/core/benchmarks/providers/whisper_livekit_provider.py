"""WhisperLiveKit provider."""
import logging
from pathlib import Path
from typing import Optional
import numpy as np
from .base_provider import STTProvider, ProviderType, TranscriptionResult

logger = logging.getLogger(__name__)

class WhisperLiveKitProvider(STTProvider):
    def __init__(self, **kwargs):
        super().__init__("WhisperLiveKit", "Base", ProviderType.LOCAL, kwargs)

    def initialize(self) -> bool:
        self._is_initialized = True
        return True

    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> TranscriptionResult:
        raise NotImplementedError("WhisperLiveKit provider not yet implemented")

    def transcribe_stream(self, audio_data: np.ndarray, sample_rate: int, language: Optional[str] = None) -> TranscriptionResult:
        raise NotImplementedError()

    def cleanup(self) -> None:
        pass

    def get_cost_per_minute(self) -> float:
        return 0.0

    def supports_language(self, language: str) -> bool:
        return True
