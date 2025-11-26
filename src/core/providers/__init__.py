"""STT Providers - Abstraction layer for Speech-to-Text services."""

from .base import (
    STTProvider,
    CloudSTTProvider,
    LocalSTTProvider,
    STTResult,
    TranscriptionSegment,
    WordTimestamp,
    ProviderConfig,
    ProviderInfo,
    ProviderType,
    ProviderCapability,
)

__all__ = [
    "STTProvider",
    "CloudSTTProvider",
    "LocalSTTProvider",
    "STTResult",
    "TranscriptionSegment",
    "WordTimestamp",
    "ProviderConfig",
    "ProviderInfo",
    "ProviderType",
    "ProviderCapability",
]
