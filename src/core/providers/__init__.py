"""
Provider abstraction layer for RTSTT services.

This module provides a unified interface for different service providers
(STT, NLP, Summary) supporting both local and cloud implementations.
"""

from .base import (
    BaseProvider,
    STTProvider,
    NLPProvider,
    SummaryProvider,
    ProviderConfig,
    ProviderType,
    ProviderCapability,
)
from .factory import ProviderFactory
from .selector import ProviderSelector
from .exceptions import (
    ProviderError,
    ProviderNotFoundError,
    ProviderTimeoutError,
    ProviderQuotaExceededError,
)

__all__ = [
    # Base classes
    "BaseProvider",
    "STTProvider",
    "NLPProvider",
    "SummaryProvider",
    "ProviderConfig",
    "ProviderType",
    "ProviderCapability",
    # Factory and selector
    "ProviderFactory",
    "ProviderSelector",
    # Exceptions
    "ProviderError",
    "ProviderNotFoundError",
    "ProviderTimeoutError",
    "ProviderQuotaExceededError",
]
