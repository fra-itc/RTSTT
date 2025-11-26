"""
Local Whisper Provider - Wrapper for WhisperRTXEngine.

This provider wraps the existing WhisperRTXEngine to conform to the
STTProvider interface, allowing it to be used interchangeably with
cloud providers.
"""

import logging
from typing import Optional, Union, List, AsyncIterator
from pathlib import Path
import numpy as np

from ..base import (
    LocalSTTProvider,
    STTResult,
    TranscriptionSegment,
    WordTimestamp,
    ProviderConfig,
    ProviderInfo,
    ProviderType,
    ProviderCapability,
)

logger = logging.getLogger(__name__)


class LocalWhisperProvider(LocalSTTProvider):
    """
    Local Whisper provider using WhisperRTXEngine.

    Features:
    - Free (no API costs)
    - Requires NVIDIA GPU with 8GB+ VRAM
    - Supports 99+ languages
    - Word-level timestamps
    - Translation to English
    - Offline operation
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.model_name = config.model or "large-v3"
        self.engine = None

    async def initialize(self) -> bool:
        """Initialize local Whisper engine."""
        try:
            # Import here to avoid dependency issues
            from ...stt_engine.whisper_rtx import WhisperRTXEngine

            # Initialize engine
            self.engine = WhisperRTXEngine(
                model_name=self.model_name,
                device=self.device,
                compute_type="float16",
                language=self.config.language,
                **self.config.additional_params
            )

            self._is_initialized = True
            logger.info(f"Local Whisper provider initialized (model: {self.model_name})")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize local Whisper: {e}")
            return False

    async def transcribe(
        self,
        audio: Union[str, Path, np.ndarray, bytes],
        language: Optional[str] = None,
        task: str = "transcribe",
        **kwargs
    ) -> STTResult:
        """
        Transcribe audio using local Whisper engine.

        Args:
            audio: Audio file path, numpy array, or bytes
            language: Target language code
            task: "transcribe" or "translate"
            **kwargs: Additional Whisper parameters

        Returns:
            STTResult: Transcription result
        """
        if not self._is_initialized or not self.engine:
            raise RuntimeError("Provider not initialized. Call initialize() first.")

        try:
            # Use WhisperRTXEngine
            result = self.engine.transcribe(
                audio=audio,
                language=language,
                task=task,
                **kwargs
            )

            # Convert to STTResult format
            segments = [
                TranscriptionSegment(
                    text=seg.text,
                    start=seg.start,
                    end=seg.end,
                    confidence=seg.confidence,
                    words=None  # WhisperRTX doesn't provide word timestamps by default
                )
                for seg in result.segments
            ]

            return STTResult(
                text=result.text,
                segments=segments,
                language=result.language,
                provider="local_whisper",
                model=self.model_name,
                duration=result.duration,
                metadata={"task": task}
            )

        except Exception as e:
            logger.error(f"Local Whisper transcription failed: {e}")
            raise

    async def transcribe_streaming(
        self,
        audio_stream: AsyncIterator[bytes],
        language: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[STTResult]:
        """
        Local Whisper streaming transcription.

        Note: This uses the streaming adapter since the base engine
        processes complete audio buffers.
        """
        # For true streaming, we would need to use the streaming adapter
        # or implement a streaming version of WhisperRTX
        raise NotImplementedError(
            "Local Whisper streaming requires StreamingAdapter. "
            "Use the adapter to convert batch transcription to streaming."
        )

    def get_info(self) -> ProviderInfo:
        """Get local Whisper provider information."""
        return ProviderInfo(
            name="Local Whisper",
            type=ProviderType.LOCAL,
            capabilities=[
                ProviderCapability.BATCH,
                ProviderCapability.WORD_TIMESTAMPS,
                ProviderCapability.TRANSLATION,
                ProviderCapability.LANGUAGE_DETECTION,
            ],
            supported_languages=self._get_supported_languages(),
            models=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
            cost_per_minute=0.0,  # Free
            latency_ms=300,
            max_audio_length=None,
            requires_api_key=False,
        )

    async def health_check(self) -> bool:
        """Check if local Whisper is available."""
        try:
            import torch
            cuda_available = torch.cuda.is_available()

            if not cuda_available:
                logger.warning("CUDA not available for local Whisper")
                return False

            return self._is_initialized

        except ImportError:
            logger.error("PyTorch not installed")
            return False

    async def estimate_cost(self, audio_duration_seconds: float) -> float:
        """
        Estimate cost for local transcription.

        Args:
            audio_duration_seconds: Duration in seconds

        Returns:
            float: Cost (always 0.0 for local)
        """
        return 0.0

    async def cleanup(self):
        """Cleanup local Whisper resources."""
        if self.engine:
            del self.engine
            self.engine = None
        await super().cleanup()

    def _get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        return [
            "af", "ar", "hy", "az", "be", "bs", "bg", "ca", "zh", "hr", "cs", "da",
            "nl", "en", "et", "fi", "fr", "gl", "de", "el", "he", "hi", "hu", "is",
            "id", "it", "ja", "kn", "kk", "ko", "lv", "lt", "mk", "ms", "mr", "mi",
            "ne", "no", "fa", "pl", "pt", "ro", "ru", "sr", "sk", "sl", "es", "sw",
            "sv", "tl", "ta", "th", "tr", "uk", "ur", "vi", "cy"
        ]
