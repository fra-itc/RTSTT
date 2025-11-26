"""Deepgram Nova-3 provider."""
import logging
import time
from pathlib import Path
from typing import Optional
import numpy as np
from .base_provider import STTProvider, ProviderType, TranscriptionResult

logger = logging.getLogger(__name__)

class DeepgramProvider(STTProvider):
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__("Deepgram", "Nova-3", ProviderType.CLOUD, {"api_key": api_key, **kwargs})
        self.api_key = api_key

    def initialize(self) -> bool:
        self._is_initialized = True
        return True

    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> TranscriptionResult:
        # TODO: Implement Deepgram API integration
        raise NotImplementedError("Deepgram provider not yet implemented")

    def transcribe_stream(self, audio_data: np.ndarray, sample_rate: int, language: Optional[str] = None) -> TranscriptionResult:
        raise NotImplementedError()

    def cleanup(self) -> None:
        self._is_initialized = False

    def get_cost_per_minute(self) -> float:
        return 0.0043

    def supports_language(self, language: str) -> bool:
        return True
