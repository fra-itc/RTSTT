"""OpenAI Whisper API provider."""

import logging
import time
from pathlib import Path
from typing import Optional
import numpy as np

from .base_provider import STTProvider, ProviderType, TranscriptionResult

logger = logging.getLogger(__name__)


class OpenAIProvider(STTProvider):
    """OpenAI Whisper API provider."""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(
            provider_name="OpenAI",
            model_name="Whisper-1",
            provider_type=ProviderType.CLOUD,
            config={"api_key": api_key, **kwargs}
        )
        self.api_key = api_key
        self.client = None

    def initialize(self) -> bool:
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
            self._is_initialized = True
            logger.info("OpenAI provider initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            return False

    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> TranscriptionResult:
        if not self._is_initialized:
            raise RuntimeError("Provider not initialized")

        start_time = time.time()
        
        try:
            with open(audio_path, 'rb') as audio_file:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language
                )
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Get audio duration
            import wave
            with wave.open(str(audio_path), 'rb') as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                duration_ms = (frames / float(rate)) * 1000
            
            result = TranscriptionResult(
                text=response.text,
                processing_time_ms=processing_time_ms,
                audio_duration_ms=duration_ms,
                language=language or "en"
            )
            
            self._update_metrics(result)
            return result
            
        except Exception as e:
            logger.error(f"OpenAI transcription failed: {e}")
            raise

    def transcribe_stream(self, audio_data: np.ndarray, sample_rate: int, language: Optional[str] = None) -> TranscriptionResult:
        raise NotImplementedError("OpenAI does not support streaming")

    def cleanup(self) -> None:
        self.client = None
        self._is_initialized = False

    def get_cost_per_minute(self) -> float:
        return 0.006  # $0.006 per minute

    def supports_language(self, language: str) -> bool:
        return True  # Supports 99 languages
