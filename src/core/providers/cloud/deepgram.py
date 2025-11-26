"""
Deepgram Nova-3 Provider - Cloud STT with real-time streaming support.

API Documentation: https://developers.deepgram.com/docs
Pricing:
  - Nova-2: $0.0043 per minute
  - Nova-3: $0.0059 per minute (most accurate)
  - Whisper Cloud: $0.0048 per minute
"""

import logging
import asyncio
import aiohttp
import json
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


class DeepgramProvider(CloudSTTProvider):
    """
    Deepgram API provider with streaming support.

    Features:
    - Nova-2, Nova-3, Whisper-Cloud models
    - Real-time streaming transcription
    - Speaker diarization
    - Smart formatting and punctuation
    - 36+ languages
    - Ultra-low latency (~50ms)
    - Cost: $0.0043-0.0059 per minute
    """

    MODELS = {
        "nova-2": 0.0043,  # Cost per minute
        "nova-3": 0.0059,
        "whisper-large": 0.0048,
        "whisper-medium": 0.0036,
        "whisper-small": 0.0024,
        "base": 0.0025,
        "enhanced": 0.0145,
    }

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = "https://api.deepgram.com/v1"
        self.model = config.model or "nova-2"

        if self.model not in self.MODELS:
            logger.warning(f"Unknown model '{self.model}', defaulting to 'nova-2'")
            self.model = "nova-2"

    async def initialize(self) -> bool:
        """Initialize Deepgram provider and verify API key."""
        if not await self._verify_api_key():
            return False

        # Create aiohttp session
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Token {self.api_key}"
            }
        )

        # Verify API key works
        is_healthy = await self.health_check()
        if is_healthy:
            self._is_initialized = True
            logger.info(f"Deepgram provider initialized successfully (model: {self.model})")
        else:
            logger.error("Deepgram API key verification failed")

        return is_healthy

    async def transcribe(
        self,
        audio: Union[str, Path, np.ndarray, bytes],
        language: Optional[str] = None,
        punctuate: bool = True,
        diarize: bool = False,
        smart_format: bool = True,
        utterances: bool = False,
        **kwargs
    ) -> STTResult:
        """
        Transcribe audio using Deepgram API (batch mode).

        Args:
            audio: Audio file path, numpy array, or bytes
            language: Language code (e.g., "it", "en")
            punctuate: Add punctuation
            diarize: Enable speaker diarization
            smart_format: Apply smart formatting
            utterances: Split into utterances

        Returns:
            STTResult: Transcription result
        """
        if not self._is_initialized:
            raise RuntimeError("Provider not initialized. Call initialize() first.")

        # Prepare audio data
        audio_data, content_type = await self._prepare_audio(audio)

        # Build query parameters
        params = {
            "model": self.model,
            "punctuate": str(punctuate).lower(),
            "smart_format": str(smart_format).lower(),
            "diarize": str(diarize).lower(),
            "utterances": str(utterances).lower(),
        }

        if language:
            params["language"] = language

        # Add any additional parameters from config
        params.update(self.config.additional_params)

        endpoint = f"{self.base_url}/listen"

        try:
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": content_type
            }

            async with self.session.post(
                endpoint,
                params=params,
                data=audio_data,
                headers=headers
            ) as response:
                if response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    await self._handle_rate_limit(retry_after)
                    # Retry once
                    return await self.transcribe(audio, language, punctuate, diarize, smart_format, utterances, **kwargs)

                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Deepgram API error ({response.status}): {error_text}")

                result_data = await response.json()

            # Parse response
            return self._parse_response(result_data)

        except Exception as e:
            logger.error(f"Deepgram transcription failed: {e}")
            raise

    async def transcribe_streaming(
        self,
        audio_stream: AsyncIterator[bytes],
        language: Optional[str] = None,
        punctuate: bool = True,
        diarize: bool = False,
        smart_format: bool = True,
        interim_results: bool = True,
        **kwargs
    ) -> AsyncIterator[STTResult]:
        """
        Transcribe audio stream in real-time using Deepgram's WebSocket API.

        Args:
            audio_stream: Async iterator of audio chunks
            language: Language code
            punctuate: Add punctuation
            diarize: Enable speaker diarization
            smart_format: Apply smart formatting
            interim_results: Return interim/partial results

        Yields:
            STTResult: Partial transcription results
        """
        if not self._is_initialized:
            raise RuntimeError("Provider not initialized. Call initialize() first.")

        # Build WebSocket URL with parameters
        params = {
            "model": self.model,
            "punctuate": str(punctuate).lower(),
            "smart_format": str(smart_format).lower(),
            "diarize": str(diarize).lower(),
            "interim_results": str(interim_results).lower(),
            "encoding": "linear16",
            "sample_rate": "16000",
        }

        if language:
            params["language"] = language

        params.update(self.config.additional_params)

        # Build query string
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        ws_url = f"wss://api.deepgram.com/v1/listen?{query_string}"

        try:
            async with self.session.ws_connect(
                ws_url,
                headers={"Authorization": f"Token {self.api_key}"}
            ) as ws:
                logger.info("Deepgram WebSocket connection established")

                # Task to send audio chunks
                async def send_audio():
                    try:
                        async for chunk in audio_stream:
                            if chunk:
                                await ws.send_bytes(chunk)
                        # Send close message
                        await ws.send_bytes(b'{"type": "CloseStream"}')
                    except Exception as e:
                        logger.error(f"Error sending audio: {e}")

                # Task to receive transcriptions
                async def receive_transcriptions():
                    try:
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)

                                # Parse response
                                if "channel" in data:
                                    result = self._parse_streaming_response(data)
                                    if result:
                                        yield result
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                logger.error(f"WebSocket error: {ws.exception()}")
                                break
                    except Exception as e:
                        logger.error(f"Error receiving transcriptions: {e}")

                # Run both tasks concurrently
                send_task = asyncio.create_task(send_audio())

                async for result in receive_transcriptions():
                    yield result

                await send_task

        except Exception as e:
            logger.error(f"Deepgram streaming failed: {e}")
            raise

    def get_info(self) -> ProviderInfo:
        """Get Deepgram provider information."""
        return ProviderInfo(
            name="Deepgram",
            type=ProviderType.CLOUD,
            capabilities=[
                ProviderCapability.STREAMING,
                ProviderCapability.BATCH,
                ProviderCapability.DIARIZATION,
                ProviderCapability.WORD_TIMESTAMPS,
                ProviderCapability.PUNCTUATION,
                ProviderCapability.SPEAKER_LABELS,
                ProviderCapability.LANGUAGE_DETECTION,
            ],
            supported_languages=self._get_supported_languages(),
            models=list(self.MODELS.keys()),
            cost_per_minute=self.MODELS[self.model],
            latency_ms=50,  # Ultra-low latency
            max_audio_length=None,
            requires_api_key=True,
        )

    async def health_check(self) -> bool:
        """Check if Deepgram API is accessible."""
        try:
            # Use the projects endpoint for health check
            async with self.session.get(
                f"{self.base_url}/projects",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status in [200, 401]  # Either success or auth issue means API is up
        except Exception as e:
            logger.error(f"Deepgram health check failed: {e}")
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
        cost_per_minute = self.MODELS[self.model]
        return duration_minutes * cost_per_minute

    async def _prepare_audio(self, audio: Union[str, Path, np.ndarray, bytes]) -> tuple[bytes, str]:
        """
        Prepare audio data for API request.

        Args:
            audio: Audio in various formats

        Returns:
            tuple: (audio_bytes, content_type)
        """
        if isinstance(audio, (str, Path)):
            # Read file
            path = Path(audio)
            if not path.exists():
                raise FileNotFoundError(f"Audio file not found: {path}")

            with open(path, 'rb') as f:
                audio_bytes = f.read()

            # Determine content type from extension
            ext = path.suffix.lower()
            content_types = {
                ".wav": "audio/wav",
                ".mp3": "audio/mp3",
                ".flac": "audio/flac",
                ".ogg": "audio/ogg",
                ".webm": "audio/webm",
            }
            content_type = content_types.get(ext, "audio/wav")

        elif isinstance(audio, np.ndarray):
            # Convert numpy array to WAV bytes
            buffer = io.BytesIO()
            sf.write(buffer, audio, 16000, format='WAV')
            audio_bytes = buffer.getvalue()
            content_type = "audio/wav"

        elif isinstance(audio, bytes):
            audio_bytes = audio
            content_type = "audio/wav"

        else:
            raise TypeError(f"Unsupported audio type: {type(audio)}")

        return audio_bytes, content_type

    def _parse_response(self, data: dict) -> STTResult:
        """
        Parse Deepgram API response into STTResult.

        Args:
            data: Response JSON data

        Returns:
            STTResult: Parsed result
        """
        try:
            results = data.get("results", {})
            channels = results.get("channels", [])

            if not channels:
                return STTResult(
                    text="",
                    segments=[],
                    language="unknown",
                    provider="deepgram",
                    model=self.model
                )

            channel = channels[0]
            alternatives = channel.get("alternatives", [])

            if not alternatives:
                return STTResult(
                    text="",
                    segments=[],
                    language="unknown",
                    provider="deepgram",
                    model=self.model
                )

            alternative = alternatives[0]
            transcript = alternative.get("transcript", "")
            confidence = alternative.get("confidence", 0.0)

            # Parse words for word-level timestamps
            segments = []
            words_data = alternative.get("words", [])

            if words_data:
                # Group words into segments (sentences)
                current_segment_words = []

                for word_data in words_data:
                    word_obj = WordTimestamp(
                        word=word_data.get("word", ""),
                        start=word_data.get("start", 0.0),
                        end=word_data.get("end", 0.0),
                        confidence=word_data.get("confidence")
                    )
                    current_segment_words.append(word_obj)

                    # End segment on punctuation or every ~10 words
                    if (word_data.get("punctuated_word", "").endswith((".", "!", "?")) or
                        len(current_segment_words) >= 10):

                        if current_segment_words:
                            segment_text = " ".join([w.word for w in current_segment_words])
                            segments.append(TranscriptionSegment(
                                text=segment_text,
                                start=current_segment_words[0].start,
                                end=current_segment_words[-1].end,
                                confidence=sum(w.confidence or 0 for w in current_segment_words) / len(current_segment_words) if any(w.confidence for w in current_segment_words) else None,
                                speaker=word_data.get("speaker"),
                                words=current_segment_words
                            ))
                            current_segment_words = []

                # Add remaining words as final segment
                if current_segment_words:
                    segment_text = " ".join([w.word for w in current_segment_words])
                    segments.append(TranscriptionSegment(
                        text=segment_text,
                        start=current_segment_words[0].start,
                        end=current_segment_words[-1].end,
                        confidence=sum(w.confidence or 0 for w in current_segment_words) / len(current_segment_words) if any(w.confidence for w in current_segment_words) else None,
                        words=current_segment_words
                    ))

            # Get detected language
            detected_language = results.get("channels", [{}])[0].get("detected_language", "unknown")

            return STTResult(
                text=transcript,
                segments=segments,
                language=detected_language,
                provider="deepgram",
                model=self.model,
                confidence=confidence,
                duration=data.get("metadata", {}).get("duration"),
                metadata={
                    "model_info": data.get("metadata", {}).get("model_info"),
                    "request_id": data.get("metadata", {}).get("request_id")
                }
            )

        except Exception as e:
            logger.error(f"Failed to parse Deepgram response: {e}")
            raise

    def _parse_streaming_response(self, data: dict) -> Optional[STTResult]:
        """
        Parse streaming WebSocket response.

        Args:
            data: WebSocket message data

        Returns:
            Optional[STTResult]: Parsed result or None if no transcript
        """
        try:
            channel = data.get("channel", {})
            alternatives = channel.get("alternatives", [])

            if not alternatives:
                return None

            alternative = alternatives[0]
            transcript = alternative.get("transcript", "")

            if not transcript:
                return None

            is_final = data.get("is_final", False)
            speech_final = data.get("speech_final", False)

            # Parse words
            words = []
            for word_data in alternative.get("words", []):
                words.append(WordTimestamp(
                    word=word_data.get("word", ""),
                    start=word_data.get("start", 0.0),
                    end=word_data.get("end", 0.0),
                    confidence=word_data.get("confidence")
                ))

            # Create single segment for streaming result
            segment = TranscriptionSegment(
                text=transcript,
                start=words[0].start if words else 0.0,
                end=words[-1].end if words else 0.0,
                confidence=alternative.get("confidence"),
                words=words if words else None
            )

            return STTResult(
                text=transcript,
                segments=[segment],
                language=channel.get("detected_language", "unknown"),
                provider="deepgram",
                model=self.model,
                confidence=alternative.get("confidence"),
                metadata={
                    "is_final": is_final,
                    "speech_final": speech_final,
                    "duration": data.get("duration"),
                }
            )

        except Exception as e:
            logger.error(f"Failed to parse streaming response: {e}")
            return None

    def _get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        # Deepgram supports 36+ languages
        return [
            "en", "es", "fr", "de", "it", "pt", "nl", "hi", "ja", "zh", "ko",
            "ru", "ar", "tr", "pl", "uk", "vi", "id", "th", "cs", "da", "fi",
            "el", "he", "hu", "no", "ro", "sv", "bg", "ca", "hr", "et", "lt",
            "lv", "sk", "sl", "ta"
        ]
