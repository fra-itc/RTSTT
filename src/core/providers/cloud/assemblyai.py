"""
AssemblyAI Provider - Cloud STT with advanced features.

API Documentation: https://www.assemblyai.com/docs
Pricing: $0.00025 per second (~$0.015 per minute)

Features:
- Speaker diarization
- Auto chapters
- Sentiment analysis
- Entity detection
- Content moderation
- Topic detection
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


class AssemblyAIProvider(CloudSTTProvider):
    """
    AssemblyAI API provider.

    Features:
    - Universal-2 model (most accurate)
    - Speaker diarization
    - Auto chapters and paragraphs
    - Sentiment analysis
    - Entity detection
    - Content safety labels
    - 99+ languages
    - Cost: $0.00025 per second (~$0.015/min)

    Two-step process:
    1. Upload audio file
    2. Create and poll transcription job
    """

    COST_PER_SECOND = 0.00025  # $0.015 per minute
    COST_PER_MINUTE = 0.015
    MAX_POLL_ATTEMPTS = 300  # 5 minutes max (1 second intervals)

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = "https://api.assemblyai.com/v2"
        self.model = config.model or "best"  # "best" or "nano"

    async def initialize(self) -> bool:
        """Initialize AssemblyAI provider and verify API key."""
        if not await self._verify_api_key():
            return False

        # Create aiohttp session
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": self.api_key
            }
        )

        # Verify API key works
        is_healthy = await self.health_check()
        if is_healthy:
            self._is_initialized = True
            logger.info("AssemblyAI provider initialized successfully")
        else:
            logger.error("AssemblyAI API key verification failed")

        return is_healthy

    async def transcribe(
        self,
        audio: Union[str, Path, np.ndarray, bytes],
        language: Optional[str] = None,
        speaker_labels: bool = False,
        auto_chapters: bool = False,
        sentiment_analysis: bool = False,
        entity_detection: bool = False,
        content_safety: bool = False,
        auto_highlights: bool = False,
        **kwargs
    ) -> STTResult:
        """
        Transcribe audio using AssemblyAI API.

        Args:
            audio: Audio file path, numpy array, or bytes
            language: Language code (optional, auto-detected if not specified)
            speaker_labels: Enable speaker diarization
            auto_chapters: Automatically detect chapters
            sentiment_analysis: Analyze sentiment
            entity_detection: Detect entities (names, organizations, etc.)
            content_safety: Content moderation labels
            auto_highlights: Extract key phrases

        Returns:
            STTResult: Transcription result
        """
        if not self._is_initialized:
            raise RuntimeError("Provider not initialized. Call initialize() first.")

        try:
            # Step 1: Upload audio
            audio_url = await self._upload_audio(audio)

            # Step 2: Create transcription job
            transcript_id = await self._create_transcription(
                audio_url,
                language=language,
                speaker_labels=speaker_labels,
                auto_chapters=auto_chapters,
                sentiment_analysis=sentiment_analysis,
                entity_detection=entity_detection,
                content_safety_labels=content_safety,
                auto_highlights=auto_highlights,
                **kwargs
            )

            # Step 3: Poll for completion
            result_data = await self._poll_transcription(transcript_id)

            # Parse response
            return self._parse_response(result_data)

        except Exception as e:
            logger.error(f"AssemblyAI transcription failed: {e}")
            raise

    async def transcribe_streaming(
        self,
        audio_stream: AsyncIterator[bytes],
        language: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[STTResult]:
        """
        AssemblyAI supports real-time streaming via WebSocket.
        This is a separate endpoint from the batch API.
        """
        if not self._is_initialized:
            raise RuntimeError("Provider not initialized. Call initialize() first.")

        # Real-time WebSocket endpoint
        # Note: Real-time API uses different pricing and setup
        # For now, raise NotImplementedError and suggest using streaming adapter

        raise NotImplementedError(
            "AssemblyAI real-time streaming requires separate setup. "
            "Use StreamingAdapter for pseudo-streaming functionality with batch API."
        )

    def get_info(self) -> ProviderInfo:
        """Get AssemblyAI provider information."""
        return ProviderInfo(
            name="AssemblyAI",
            type=ProviderType.CLOUD,
            capabilities=[
                ProviderCapability.BATCH,
                ProviderCapability.DIARIZATION,
                ProviderCapability.WORD_TIMESTAMPS,
                ProviderCapability.PUNCTUATION,
                ProviderCapability.SPEAKER_LABELS,
                ProviderCapability.LANGUAGE_DETECTION,
            ],
            supported_languages=self._get_supported_languages(),
            models=["best", "nano"],
            cost_per_minute=self.COST_PER_MINUTE,
            latency_ms=5000,  # ~5 seconds typical
            max_audio_length=None,
            requires_api_key=True,
        )

    async def health_check(self) -> bool:
        """Check if AssemblyAI API is accessible."""
        try:
            # Test with transcript list endpoint
            async with self.session.get(
                f"{self.base_url}/transcript",
                params={"limit": 1},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"AssemblyAI health check failed: {e}")
            return False

    async def estimate_cost(self, audio_duration_seconds: float) -> float:
        """
        Estimate cost for transcription.

        Args:
            audio_duration_seconds: Duration in seconds

        Returns:
            float: Estimated cost in USD
        """
        return audio_duration_seconds * self.COST_PER_SECOND

    async def _upload_audio(self, audio: Union[str, Path, np.ndarray, bytes]) -> str:
        """
        Upload audio file to AssemblyAI.

        Args:
            audio: Audio in various formats

        Returns:
            str: Upload URL
        """
        # Prepare audio data
        audio_data = await self._prepare_audio(audio)

        # Upload to AssemblyAI
        upload_url = f"{self.base_url}/upload"

        try:
            async with self.session.post(
                upload_url,
                data=audio_data,
                headers={
                    "Authorization": self.api_key,
                    "Content-Type": "application/octet-stream"
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Upload failed ({response.status}): {error_text}")

                result = await response.json()
                audio_url = result.get("upload_url")

                if not audio_url:
                    raise RuntimeError("No upload URL returned")

                logger.info(f"Audio uploaded successfully: {audio_url}")
                return audio_url

        except Exception as e:
            logger.error(f"Audio upload failed: {e}")
            raise

    async def _create_transcription(
        self,
        audio_url: str,
        language: Optional[str] = None,
        **options
    ) -> str:
        """
        Create transcription job.

        Args:
            audio_url: URL of uploaded audio
            language: Language code
            **options: Transcription options

        Returns:
            str: Transcript ID
        """
        # Build request payload
        payload = {
            "audio_url": audio_url,
        }

        # Add language if specified
        if language:
            # AssemblyAI uses language codes like "en", "es", "fr", etc.
            payload["language_code"] = language

        # Add optional features
        if options.get("speaker_labels"):
            payload["speaker_labels"] = True

        if options.get("auto_chapters"):
            payload["auto_chapters"] = True

        if options.get("sentiment_analysis"):
            payload["sentiment_analysis"] = True

        if options.get("entity_detection"):
            payload["entity_detection"] = True

        if options.get("content_safety_labels"):
            payload["content_safety_labels"] = True

        if options.get("auto_highlights"):
            payload["auto_highlights"] = True

        # Add any additional parameters
        for key, value in self.config.additional_params.items():
            payload[key] = value

        try:
            async with self.session.post(
                f"{self.base_url}/transcript",
                json=payload
            ) as response:
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    raise RuntimeError(f"Transcription creation failed ({response.status}): {error_text}")

                result = await response.json()
                transcript_id = result.get("id")

                if not transcript_id:
                    raise RuntimeError("No transcript ID returned")

                logger.info(f"Transcription job created: {transcript_id}")
                return transcript_id

        except Exception as e:
            logger.error(f"Transcription creation failed: {e}")
            raise

    async def _poll_transcription(self, transcript_id: str) -> dict:
        """
        Poll transcription until complete.

        Args:
            transcript_id: Transcript ID to poll

        Returns:
            dict: Completed transcription data
        """
        poll_url = f"{self.base_url}/transcript/{transcript_id}"

        for attempt in range(self.MAX_POLL_ATTEMPTS):
            try:
                async with self.session.get(poll_url) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(f"Polling failed ({response.status}): {error_text}")

                    data = await response.json()
                    status = data.get("status")

                    if status == "completed":
                        logger.info(f"Transcription completed: {transcript_id}")
                        return data

                    elif status == "error":
                        error = data.get("error", "Unknown error")
                        raise RuntimeError(f"Transcription failed: {error}")

                    elif status in ["queued", "processing"]:
                        # Still processing, wait and retry
                        await asyncio.sleep(1)
                        continue

                    else:
                        raise RuntimeError(f"Unknown status: {status}")

            except Exception as e:
                if attempt == self.MAX_POLL_ATTEMPTS - 1:
                    raise
                logger.warning(f"Poll attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(1)

        raise RuntimeError(f"Transcription timed out after {self.MAX_POLL_ATTEMPTS} seconds")

    async def _prepare_audio(self, audio: Union[str, Path, np.ndarray, bytes]) -> bytes:
        """
        Prepare audio data for upload.

        Args:
            audio: Audio in various formats

        Returns:
            bytes: Audio bytes
        """
        if isinstance(audio, (str, Path)):
            # Read file
            path = Path(audio)
            if not path.exists():
                raise FileNotFoundError(f"Audio file not found: {path}")

            with open(path, 'rb') as f:
                return f.read()

        elif isinstance(audio, np.ndarray):
            # Convert numpy array to WAV bytes
            buffer = io.BytesIO()
            sf.write(buffer, audio, 16000, format='WAV')
            return buffer.getvalue()

        elif isinstance(audio, bytes):
            return audio

        else:
            raise TypeError(f"Unsupported audio type: {type(audio)}")

    def _parse_response(self, data: dict) -> STTResult:
        """
        Parse AssemblyAI API response into STTResult.

        Args:
            data: Response JSON data

        Returns:
            STTResult: Parsed result
        """
        try:
            text = data.get("text", "")
            confidence = data.get("confidence")
            language = data.get("language_code", "unknown")

            # Parse words for segments
            segments = []
            words_data = data.get("words", [])

            if words_data:
                # Group words into segments based on speaker or pauses
                current_segment_words = []
                current_speaker = None

                for word_data in words_data:
                    speaker = word_data.get("speaker")
                    word_obj = WordTimestamp(
                        word=word_data.get("text", ""),
                        start=word_data.get("start", 0.0) / 1000.0,  # Convert ms to seconds
                        end=word_data.get("end", 0.0) / 1000.0,
                        confidence=word_data.get("confidence")
                    )

                    # Start new segment on speaker change
                    if speaker != current_speaker and current_segment_words:
                        segment_text = " ".join([w.word for w in current_segment_words])
                        segments.append(TranscriptionSegment(
                            text=segment_text,
                            start=current_segment_words[0].start,
                            end=current_segment_words[-1].end,
                            confidence=sum(w.confidence or 0 for w in current_segment_words) / len(current_segment_words) if any(w.confidence for w in current_segment_words) else None,
                            speaker=f"Speaker {current_speaker}" if current_speaker is not None else None,
                            words=current_segment_words
                        ))
                        current_segment_words = []

                    current_segment_words.append(word_obj)
                    current_speaker = speaker

                # Add final segment
                if current_segment_words:
                    segment_text = " ".join([w.word for w in current_segment_words])
                    segments.append(TranscriptionSegment(
                        text=segment_text,
                        start=current_segment_words[0].start,
                        end=current_segment_words[-1].end,
                        confidence=sum(w.confidence or 0 for w in current_segment_words) / len(current_segment_words) if any(w.confidence for w in current_segment_words) else None,
                        speaker=f"Speaker {current_speaker}" if current_speaker is not None else None,
                        words=current_segment_words
                    ))

            # Parse utterances if available (speaker diarization)
            elif "utterances" in data and data["utterances"]:
                for utterance in data["utterances"]:
                    segments.append(TranscriptionSegment(
                        text=utterance.get("text", ""),
                        start=utterance.get("start", 0.0) / 1000.0,
                        end=utterance.get("end", 0.0) / 1000.0,
                        confidence=utterance.get("confidence"),
                        speaker=f"Speaker {utterance.get('speaker')}" if utterance.get('speaker') is not None else None
                    ))

            # Build metadata
            metadata = {
                "id": data.get("id"),
                "audio_duration": data.get("audio_duration"),
            }

            if "chapters" in data and data["chapters"]:
                metadata["chapters"] = data["chapters"]

            if "sentiment_analysis_results" in data:
                metadata["sentiment"] = data["sentiment_analysis_results"]

            if "entities" in data:
                metadata["entities"] = data["entities"]

            if "content_safety_labels" in data:
                metadata["content_safety"] = data["content_safety_labels"]

            return STTResult(
                text=text,
                segments=segments,
                language=language,
                provider="assemblyai",
                model=self.model,
                confidence=confidence,
                duration=data.get("audio_duration"),
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Failed to parse AssemblyAI response: {e}")
            raise

    def _get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        # AssemblyAI supports 99+ languages
        return [
            "en", "es", "fr", "de", "it", "pt", "nl", "hi", "ja", "zh", "ko",
            "ru", "ar", "tr", "pl", "uk", "vi", "id", "th", "cs", "da", "fi",
            "el", "he", "hu", "no", "ro", "sv", "bg", "ca", "hr", "et", "lt",
            "lv", "sk", "sl", "ta", "te", "mr", "kn", "ml", "bn", "ur", "fa",
            "af", "sq", "am", "hy", "az", "eu", "be", "bs", "my", "gl", "ka",
            "gu", "is", "ga", "jv", "kk", "km", "ky", "lo", "mk", "mg", "ms",
            "mt", "mi", "mn", "ne", "ps", "pa", "si", "so", "su", "sw", "tl",
            "tg", "uz", "cy", "yi", "zu"
        ]
