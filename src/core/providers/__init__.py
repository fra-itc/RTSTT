"""
Provider abstraction layer for RTSTT.

This package provides a unified interface for different service providers (local, cloud, hybrid).
"""

from .base import (
    BaseProvider,
    NLPProvider,
    SummaryProvider,
    NLPResult,
    SummaryResult,
    ProviderConfig,
    ProviderType,
    ProviderCapability,
    ProviderMetrics,
)
from .exceptions import (
    ProviderError,
    ProviderNotFoundError,
    ProviderNotAvailableError,
    ProviderTimeoutError,
    ProviderQuotaExceededError,
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderResponseError,
)
from .factory import (
    ProviderFactory,
    get_factory,
    register_default_providers,
)

__all__ = [
    # Base classes
    "BaseProvider",
    "NLPProvider",
    "SummaryProvider",
    # Results
    "NLPResult",
    "SummaryResult",
    # Config
    "ProviderConfig",
    "ProviderType",
    "ProviderCapability",
    "ProviderMetrics",
    # Exceptions
    "ProviderError",
    "ProviderNotFoundError",
    "ProviderNotAvailableError",
    "ProviderTimeoutError",
    "ProviderQuotaExceededError",
    "ProviderAuthenticationError",
    "ProviderConfigurationError",
    "ProviderResponseError",
    # Factory
    "ProviderFactory",
    "get_factory",
    "register_default_providers",
]
