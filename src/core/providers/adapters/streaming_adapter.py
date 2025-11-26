"""
Streaming Adapter - Convert batch STT APIs to pseudo-streaming.

This adapter allows batch-only APIs (like OpenAI Whisper and AssemblyAI)
to provide a streaming-like experience by buffering audio chunks and
processing them in overlapping batches.
"""

import logging
import asyncio
from typing import AsyncIterator, Optional
from collections import deque
import io
import numpy as np

from ..base import STTProvider, STTResult

logger = logging.getLogger(__name__)


class StreamingAdapter:
    """
    Adapter that converts batch STT providers to pseudo-streaming.

    Strategy:
    1. Buffer incoming audio chunks
    2. When buffer reaches threshold, process accumulated audio
    3. Emit partial results with timestamps
    4. Use overlapping windows to avoid missing words at boundaries
    5. Deduplicate results based on timestamps
    """

    def __init__(
        self,
        provider: STTProvider,
        chunk_duration_ms: int = 3000,  # Process every 3 seconds
        overlap_ms: int = 500,  # 500ms overlap to avoid boundary issues
        sample_rate: int = 16000,
        min_buffer_ms: int = 1000,  # Minimum buffer before first transcription
    ):
        """
        Initialize streaming adapter.

        Args:
            provider: Batch STT provider to adapt
            chunk_duration_ms: Duration of audio to accumulate before processing
            overlap_ms: Overlap between chunks to avoid boundary issues
            sample_rate: Audio sample rate
            min_buffer_ms: Minimum buffer duration before starting
        """
        self.provider = provider
        self.chunk_duration_ms = chunk_duration_ms
        self.overlap_ms = overlap_ms
        self.sample_rate = sample_rate
        self.min_buffer_ms = min_buffer_ms

        # Calculate buffer sizes in samples
        self.chunk_size = int(chunk_duration_ms * sample_rate / 1000)
        self.overlap_size = int(overlap_ms * sample_rate / 1000)
        self.min_buffer_size = int(min_buffer_ms * sample_rate / 1000)

        # Audio buffer
        self.buffer = deque()
        self.buffer_samples = 0

        # Track what we've already transcribed
        self.last_end_time = 0.0
        self.cumulative_offset = 0.0

    async def transcribe_streaming(
        self,
        audio_stream: AsyncIterator[bytes],
        language: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[STTResult]:
        """
        Convert batch transcription to streaming.

        Args:
            audio_stream: Async iterator of audio chunks (bytes)
            language: Target language
            **kwargs: Provider-specific parameters

        Yields:
            STTResult: Partial transcription results
        """
        try:
            async for chunk in audio_stream:
                if not chunk:
                    continue

                # Convert bytes to numpy array (assuming 16-bit PCM)
                audio_array = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0

                # Add to buffer
                self.buffer.append(audio_array)
                self.buffer_samples += len(audio_array)

                # Check if we have enough audio to process
                if self.buffer_samples >= self.chunk_size:
                    # Process current buffer
                    result = await self._process_buffer(language, **kwargs)

                    if result and result.text.strip():
                        yield result

                    # Remove processed samples, keep overlap
                    self._trim_buffer()

            # Process remaining audio at end of stream
            if self.buffer_samples >= self.min_buffer_size:
                result = await self._process_buffer(language, is_final=True, **kwargs)
                if result and result.text.strip():
                    yield result

        except Exception as e:
            logger.error(f"Streaming adapter error: {e}")
            raise
        finally:
            # Cleanup
            self.buffer.clear()
            self.buffer_samples = 0

    async def _process_buffer(
        self,
        language: Optional[str] = None,
        is_final: bool = False,
        **kwargs
    ) -> Optional[STTResult]:
        """
        Process accumulated audio buffer.

        Args:
            language: Target language
            is_final: Whether this is the final chunk
            **kwargs: Provider parameters

        Returns:
            Optional[STTResult]: Transcription result or None
        """
        try:
            # Concatenate buffer into single array
            audio_array = np.concatenate(list(self.buffer))

            # Transcribe
            result = await self.provider.transcribe(
                audio_array,
                language=language,
                **kwargs
            )

            if not result or not result.text.strip():
                return None

            # Adjust timestamps to account for cumulative offset
            adjusted_segments = []
            for segment in result.segments:
                # Only include segments that are after our last transcribed time
                # (accounting for overlap)
                segment_start = segment.start + self.cumulative_offset

                if segment_start >= self.last_end_time - (self.overlap_ms / 1000.0):
                    adjusted_segment = TranscriptionSegment(
                        text=segment.text,
                        start=segment_start,
                        end=segment.end + self.cumulative_offset,
                        confidence=segment.confidence,
                        speaker=segment.speaker,
                        words=[
                            WordTimestamp(
                                word=w.word,
                                start=w.start + self.cumulative_offset,
                                end=w.end + self.cumulative_offset,
                                confidence=w.confidence
                            )
                            for w in (segment.words or [])
                        ] if segment.words else None
                    )
                    adjusted_segments.append(adjusted_segment)

                    # Update last end time
                    self.last_end_time = adjusted_segment.end

            if not adjusted_segments:
                return None

            # Build result with adjusted timestamps
            adjusted_result = STTResult(
                text=" ".join([s.text for s in adjusted_segments]),
                segments=adjusted_segments,
                language=result.language,
                provider=result.provider,
                model=result.model,
                confidence=result.confidence,
                metadata={
                    **result.metadata,
                    "streaming_adapter": True,
                    "is_final": is_final
                }
            )

            return adjusted_result

        except Exception as e:
            logger.error(f"Buffer processing error: {e}")
            return None

    def _trim_buffer(self):
        """
        Remove processed samples from buffer, keeping overlap.
        """
        # Calculate how many samples to remove
        samples_to_remove = self.buffer_samples - self.overlap_size

        if samples_to_remove <= 0:
            return

        # Update cumulative offset
        self.cumulative_offset += samples_to_remove / self.sample_rate

        # Remove samples from front of buffer
        removed = 0
        while removed < samples_to_remove and self.buffer:
            chunk = self.buffer[0]
            if removed + len(chunk) <= samples_to_remove:
                # Remove entire chunk
                self.buffer.popleft()
                removed += len(chunk)
            else:
                # Remove partial chunk
                keep_samples = len(chunk) - (samples_to_remove - removed)
                self.buffer[0] = chunk[-keep_samples:]
                removed = samples_to_remove

        self.buffer_samples -= samples_to_remove


# Import for type hints
from ..base import TranscriptionSegment, WordTimestamp


class ChunkedStreamingAdapter(StreamingAdapter):
    """
    Enhanced streaming adapter with fixed-size chunks.

    Better for real-time applications where consistent latency is important.
    """

    def __init__(
        self,
        provider: STTProvider,
        chunk_duration_ms: int = 2000,  # 2 second chunks
        **kwargs
    ):
        super().__init__(
            provider=provider,
            chunk_duration_ms=chunk_duration_ms,
            **kwargs
        )

    async def transcribe_streaming(
        self,
        audio_stream: AsyncIterator[bytes],
        language: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[STTResult]:
        """
        Process audio in fixed-size chunks with low latency.

        Args:
            audio_stream: Async iterator of audio chunks
            language: Target language
            **kwargs: Provider parameters

        Yields:
            STTResult: Partial results at regular intervals
        """
        try:
            async for chunk in audio_stream:
                if not chunk:
                    continue

                # Convert bytes to numpy array
                audio_array = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0

                # Add to buffer
                self.buffer.append(audio_array)
                self.buffer_samples += len(audio_array)

                # Process when we reach chunk size (not before)
                if self.buffer_samples >= self.chunk_size:
                    result = await self._process_buffer(language, **kwargs)

                    if result and result.text.strip():
                        yield result

                    # Clear buffer completely (no overlap for fixed chunks)
                    self.cumulative_offset += self.buffer_samples / self.sample_rate
                    self.buffer.clear()
                    self.buffer_samples = 0

            # Final chunk
            if self.buffer_samples > 0:
                result = await self._process_buffer(language, is_final=True, **kwargs)
                if result and result.text.strip():
                    yield result

        except Exception as e:
            logger.error(f"Chunked streaming error: {e}")
            raise
        finally:
            self.buffer.clear()
            self.buffer_samples = 0
