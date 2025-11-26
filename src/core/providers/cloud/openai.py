"""
OpenAI Whisper API Provider - Cloud STT using OpenAI's Whisper API.

API Documentation: https://platform.openai.com/docs/guides/speech-to-text
Pricing: $0.006 per minute (rounded to nearest second)
"""

import logging
import asyncio
import aiohttp
from typing import Optional, Union, List, AsyncIterator
from pathlib import Path
import numpy as np
import io
import soundfile as sf

from ..base import (
    CloudSTTProvider,
    STTResult,
    TranscriptionSegment,
    WordTimestamp,
    ProviderConfig,
    ProviderInfo,
    ProviderType,
    ProviderCapability,
)

logger = logging.getLogger(__name__)


class OpenAISTTProvider(CloudSTTProvider):
    """
    OpenAI Whisper API provider.

    Features:
    - Whisper-1 model (based on Whisper Large V2)
    - 99+ languages supported
    - Transcription and translation
    - Word-level timestamps in verbose_json mode
    - Max file size: 25 MB
    - Cost: $0.006 per minute
    """

    SUPPORTED_FORMATS = ["flac", "m4a", "mp3", "mp4", "mpeg", "mpga", "oga", "ogg", "wav", "webm"]
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB
    COST_PER_MINUTE = 0.006  # USD

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = "https://api.openai.com/v1/audio"
        self.model = config.model or "whisper-1"

    async def initialize(self) -> bool:
        """Initialize OpenAI provider and verify API key."""
        if not await self._verify_api_key():
            return False

        # Create aiohttp session
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}"
            }
        )

        # Verify API key works
        is_healthy = await self.health_check()
        if is_healthy:
            self._is_initialized = True
            logger.info("OpenAI Whisper API provider initialized successfully")
        else:
            logger.error("OpenAI API key verification failed")

        return is_healthy

    async def transcribe(
        self,
        audio: Union[str, Path, np.ndarray, bytes],
        language: Optional[str] = None,
        task: str = "transcribe",
        response_format: str = "verbose_json",
        temperature: float = 0.0,
        prompt: Optional[str] = None,
        **kwargs
    ) -> STTResult:
        """
        Transcribe audio using OpenAI Whisper API.

        Args:
            audio: Audio file path, numpy array, or bytes
            language: ISO-639-1 language code (e.g., "it", "en")
            task: "transcribe" or "translate" (translate to English)
            response_format: "json", "text", "srt", "verbose_json", "vtt"
            temperature: Sampling temperature (0-1)
            prompt: Optional text to guide the model's style

        Returns:
            STTResult: Transcription result
        """
        if not self._is_initialized:
            raise RuntimeError("Provider not initialized. Call initialize() first.")

        # Prepare audio data
        audio_data, filename = await self._prepare_audio(audio)

        # Build form data
        data = aiohttp.FormData()
        data.add_field('file', audio_data, filename=filename)
        data.add_field('model', self.model)

        if language:
            data.add_field('language', language)

        data.add_field('response_format', response_format)
        data.add_field('temperature', str(temperature))

        if prompt:
            data.add_field('prompt', prompt)

        # Determine endpoint based on task
        endpoint = f"{self.base_url}/transcriptions" if task == "transcribe" else f"{self.base_url}/translations"

        try:
            async with self.session.post(endpoint, data=data) as response:
                if response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    await self._handle_rate_limit(retry_after)
                    # Retry once
                    return await self.transcribe(audio, language, task, response_format, temperature, prompt, **kwargs)

                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"OpenAI API error ({response.status}): {error_text}")

                result_data = await response.json()

            # Parse response based on format
            return self._parse_response(result_data, response_format)

        except Exception as e:
            logger.error(f"OpenAI transcription failed: {e}")
            raise

    async def transcribe_streaming(
        self,
        audio_stream: AsyncIterator[bytes],
        language: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[STTResult]:
        """
        OpenAI Whisper API does not support native streaming.
        Use the streaming adapter for pseudo-streaming.
        """
        raise NotImplementedError(
            "OpenAI Whisper API does not support native streaming. "
            "Use StreamingAdapter for pseudo-streaming functionality."
        )

    def get_info(self) -> ProviderInfo:
        """Get OpenAI provider information."""
        return ProviderInfo(
            name="OpenAI Whisper API",
            type=ProviderType.CLOUD,
            capabilities=[
                ProviderCapability.BATCH,
                ProviderCapability.WORD_TIMESTAMPS,
                ProviderCapability.TRANSLATION,
                ProviderCapability.LANGUAGE_DETECTION,
            ],
            supported_languages=self._get_supported_languages(),
            models=["whisper-1"],
            cost_per_minute=self.COST_PER_MINUTE,
            latency_ms=2000,  # ~2 seconds typical
            max_audio_length=None,  # Limited by file size (25MB)
            requires_api_key=True,
        )

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible."""
        try:
            # Test with a minimal request (will fail but verify auth)
            async with self.session.get(
                "https://api.openai.com/v1/models",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status in [200, 401, 403]  # Auth errors mean API is reachable
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return False

    async def estimate_cost(self, audio_duration_seconds: float) -> float:
        """
        Estimate cost for transcription.

        Args:
            audio_duration_seconds: Duration in seconds

        Returns:
            float: Estimated cost in USD
        """
        duration_minutes = audio_duration_seconds / 60.0
        # Round up to nearest second (OpenAI's billing unit)
        import math
        duration_seconds_rounded = math.ceil(audio_duration_seconds)
        duration_minutes_rounded = duration_seconds_rounded / 60.0
        return duration_minutes_rounded * self.COST_PER_MINUTE

    async def _prepare_audio(self, audio: Union[str, Path, np.ndarray, bytes]) -> tuple[bytes, str]:
        """
        Prepare audio data for API request.

        Args:
            audio: Audio in various formats

        Returns:
            tuple: (audio_bytes, filename)
        """
        if isinstance(audio, (str, Path)):
            # Read file
            path = Path(audio)
            if not path.exists():
                raise FileNotFoundError(f"Audio file not found: {path}")

            if path.stat().st_size > self.MAX_FILE_SIZE:
                raise ValueError(f"File size exceeds {self.MAX_FILE_SIZE / 1024 / 1024}MB limit")

            with open(path, 'rb') as f:
                audio_bytes = f.read()
            filename = path.name

        elif isinstance(audio, np.ndarray):
            # Convert numpy array to WAV bytes
            buffer = io.BytesIO()
            sf.write(buffer, audio, 16000, format='WAV')
            audio_bytes = buffer.getvalue()
            filename = "audio.wav"

        elif isinstance(audio, bytes):
            audio_bytes = audio
            filename = "audio.wav"

        else:
            raise TypeError(f"Unsupported audio type: {type(audio)}")

        return audio_bytes, filename

    def _parse_response(self, data: dict, response_format: str) -> STTResult:
        """
        Parse OpenAI API response into STTResult.

        Args:
            data: Response JSON data
            response_format: Response format used

        Returns:
            STTResult: Parsed result
        """
        if response_format == "verbose_json":
            # Full response with segments and word timestamps
            text = data.get("text", "")
            language = data.get("language", "unknown")
            duration = data.get("duration")

            segments = []
            for seg in data.get("segments", []):
                # Parse word timestamps if available
                words = None
                if "words" in seg:
                    words = [
                        WordTimestamp(
                            word=w.get("word", ""),
                            start=w.get("start", 0.0),
                            end=w.get("end", 0.0),
                            confidence=w.get("confidence")
                        )
                        for w in seg["words"]
                    ]

                segments.append(TranscriptionSegment(
                    text=seg.get("text", ""),
                    start=seg.get("start", 0.0),
                    end=seg.get("end", 0.0),
                    confidence=seg.get("avg_logprob"),
                    words=words
                ))

            return STTResult(
                text=text,
                segments=segments,
                language=language,
                provider="openai",
                model=self.model,
                duration=duration,
                metadata={"response_format": response_format}
            )

        else:
            # Simple response (json or text)
            text = data.get("text", "") if isinstance(data, dict) else data
            return STTResult(
                text=text,
                segments=[],
                language=data.get("language", "unknown") if isinstance(data, dict) else "unknown",
                provider="openai",
                model=self.model,
                metadata={"response_format": response_format}
            )

    def _get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        # Whisper supports 99+ languages
        return [
            "af", "ar", "hy", "az", "be", "bs", "bg", "ca", "zh", "hr", "cs", "da",
            "nl", "en", "et", "fi", "fr", "gl", "de", "el", "he", "hi", "hu", "is",
            "id", "it", "ja", "kn", "kk", "ko", "lv", "lt", "mk", "ms", "mr", "mi",
            "ne", "no", "fa", "pl", "pt", "ro", "ru", "sr", "sk", "sl", "es", "sw",
            "sv", "tl", "ta", "th", "tr", "uk", "ur", "vi", "cy"
        ]
