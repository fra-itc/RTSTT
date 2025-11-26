"""STT Provider Adapters - Convert between different provider interfaces."""

from .streaming_adapter import StreamingAdapter, ChunkedStreamingAdapter

__all__ = [
    "StreamingAdapter",
    "ChunkedStreamingAdapter",
]
