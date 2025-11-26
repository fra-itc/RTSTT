"""
Exception classes for provider abstraction layer.
"""


class ProviderError(Exception):
    """Base exception for all provider-related errors."""

    def __init__(self, message: str, provider_name: str = None, **kwargs):
        self.provider_name = provider_name
        self.details = kwargs
        super().__init__(message)


class ProviderNotFoundError(ProviderError):
    """Raised when a requested provider is not available."""

    pass


class ProviderNotAvailableError(ProviderError):
    """Raised when a provider is registered but temporarily unavailable."""

    pass


class ProviderTimeoutError(ProviderError):
    """Raised when a provider operation times out."""

    pass


class ProviderQuotaExceededError(ProviderError):
    """Raised when a provider's quota or rate limit is exceeded."""

    pass


class ProviderAuthenticationError(ProviderError):
    """Raised when provider authentication fails."""

    pass


class ProviderConfigurationError(ProviderError):
    """Raised when a provider has invalid configuration."""

    pass


class ProviderResponseError(ProviderError):
    """Raised when a provider returns an invalid or unexpected response."""

    pass
