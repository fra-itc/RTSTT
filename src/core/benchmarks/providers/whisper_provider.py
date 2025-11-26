"""
Whisper Large-v3 provider implementation.

Uses FasterWhisper for optimized inference.
"""

import logging
import time
from pathlib import Path
from typing import Optional
import numpy as np

from .base_provider import STTProvider, ProviderType, TranscriptionResult

logger = logging.getLogger(__name__)


class WhisperProvider(STTProvider):
    """
    Whisper Large-v3 STT provider using FasterWhisper.

    Features:
    - GPU-accelerated inference
    - Float16 precision
    - Batch processing support
    """

    def __init__(
        self,
        model_size: str = "large-v3",
        device: str = "cuda",
        compute_type: str = "float16",
        **kwargs
    ):
        """
        Initialize WhisperProvider.

        Args:
            model_size: Whisper model size
            device: "cuda" or "cpu"
            compute_type: "float16", "int8", etc.
        """
        super().__init__(
            provider_name="Whisper",
            model_name=model_size,
            provider_type=ProviderType.LOCAL,
            config={
                "device": device,
                "compute_type": compute_type,
                **kwargs
            }
        )

        self.model = None
        self.device = device
        self.compute_type = compute_type
        self.model_size = model_size

    def initialize(self) -> bool:
        """Initialize Whisper model."""
        try:
            from faster_whisper import WhisperModel

            logger.info(f"Loading Whisper {self.model_size} model...")

            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                num_workers=self.config.get("num_workers", 1)
            )

            self._is_initialized = True
            logger.info("Whisper model loaded successfully")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize Whisper: {e}")
            return False

    def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """Transcribe audio file."""
        if not self._is_initialized or self.model is None:
            raise RuntimeError("Provider not initialized")

        start_time = time.time()

        try:
            # Get audio duration
            import wave
            with wave.open(str(audio_path), 'rb') as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                duration_ms = (frames / float(rate)) * 1000

            # Transcribe
            segments, info = self.model.transcribe(
                str(audio_path),
                language=language,
                beam_size=5,
                vad_filter=True
            )

            # Collect segments
            text_parts = []
            all_segments = []

            for segment in segments:
                text_parts.append(segment.text)
                all_segments.append({
                    "text": segment.text,
                    "start": segment.start,
                    "end": segment.end,
                    "confidence": getattr(segment, 'avg_logprob', None)
                })

            full_text = " ".join(text_parts).strip()

            # Calculate confidence (average log probability converted to probability)
            if all_segments and all_segments[0]["confidence"] is not None:
                avg_logprob = sum(s["confidence"] for s in all_segments) / len(all_segments)
                confidence = float(np.exp(avg_logprob))
            else:
                confidence = None

            processing_time_ms = (time.time() - start_time) * 1000

            result = TranscriptionResult(
                text=full_text,
                confidence=confidence,
                language=info.language,
                processing_time_ms=processing_time_ms,
                audio_duration_ms=duration_ms,
                segments=all_segments,
                metadata={
                    "duration": info.duration,
                    "language_probability": info.language_probability
                }
            )

            self._update_metrics(result)

            return result

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def transcribe_stream(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """Transcribe streaming audio."""
        if not self._is_initialized or self.model is None:
            raise RuntimeError("Provider not initialized")

        # For batch processing, Whisper doesn't support true streaming
        # We'll process the chunk as-is
        start_time = time.time()

        try:
            duration_ms = (len(audio_data) / sample_rate) * 1000

            segments, info = self.model.transcribe(
                audio_data,
                language=language,
                beam_size=5
            )

            text_parts = []
            for segment in segments:
                text_parts.append(segment.text)

            full_text = " ".join(text_parts).strip()
            processing_time_ms = (time.time() - start_time) * 1000

            result = TranscriptionResult(
                text=full_text,
                language=info.language,
                processing_time_ms=processing_time_ms,
                audio_duration_ms=duration_ms
            )

            self._update_metrics(result)

            return result

        except Exception as e:
            logger.error(f"Stream transcription failed: {e}")
            raise

    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.model is not None:
            del self.model
            self.model = None

        self._is_initialized = False
        logger.info("Whisper provider cleaned up")

    def get_cost_per_minute(self) -> float:
        """Get cost per minute (free for local)."""
        return 0.0

    def supports_language(self, language: str) -> bool:
        """Check language support."""
        # Whisper supports 99 languages
        supported = [
            "en", "es", "fr", "de", "it", "pt", "nl", "ru", "zh", "ja",
            "ko", "ar", "hi", "tr", "pl", "uk", "sv", "da", "no", "fi"
        ]
        return language in supported
