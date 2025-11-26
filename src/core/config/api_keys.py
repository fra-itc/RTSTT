"""
Secure API key management with encryption.

This module provides secure storage and retrieval of API keys for external LLM providers.
Keys are encrypted at rest using Fernet symmetric encryption.
"""

import os
import json
import logging
from typing import Optional, Dict
from pathlib import Path
from cryptography.fernet import Fernet
from datetime import datetime

logger = logging.getLogger(__name__)


class APIKeyManager:
    """
    Manages API keys with encryption for external LLM providers.

    Keys are stored encrypted on disk and can also be loaded from environment variables.
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the API key manager.

        Args:
            storage_path: Path to store encrypted keys. Defaults to ~/.rtstt/api_keys.enc
        """
        if storage_path is None:
            home = Path.home()
            storage_dir = home / ".rtstt"
            storage_dir.mkdir(parents=True, exist_ok=True)
            storage_path = str(storage_dir / "api_keys.enc")

        self.storage_path = storage_path
        self._keys: Dict[str, str] = {}
        self._cipher = self._get_or_create_cipher()

        # Load keys from storage
        self._load_keys()

        # Load from environment variables (takes precedence)
        self._load_from_env()

    def _get_or_create_cipher(self) -> Fernet:
        """Get or create the encryption cipher."""
        key_file = Path(self.storage_path).parent / ".encryption_key"

        if key_file.exists():
            with open(key_file, "rb") as f:
                key = f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            # Restrict permissions
            os.chmod(key_file, 0o600)
            logger.info(f"Generated new encryption key at {key_file}")

        return Fernet(key)

    def _load_keys(self) -> None:
        """Load encrypted keys from storage."""
        if not os.path.exists(self.storage_path):
            logger.info("No stored API keys found")
            return

        try:
            with open(self.storage_path, "rb") as f:
                encrypted_data = f.read()

            if not encrypted_data:
                return

            decrypted_data = self._cipher.decrypt(encrypted_data)
            self._keys = json.loads(decrypted_data.decode())
            logger.info(f"Loaded {len(self._keys)} API keys from storage")
        except Exception as e:
            logger.error(f"Error loading API keys: {e}")
            self._keys = {}

    def _save_keys(self) -> None:
        """Save encrypted keys to storage."""
        try:
            data = json.dumps(self._keys).encode()
            encrypted_data = self._cipher.encrypt(data)

            with open(self.storage_path, "wb") as f:
                f.write(encrypted_data)

            # Restrict permissions
            os.chmod(self.storage_path, 0o600)
            logger.info("API keys saved to storage")
        except Exception as e:
            logger.error(f"Error saving API keys: {e}")

    def _load_from_env(self) -> None:
        """Load API keys from environment variables."""
        env_keys = {
            "openai": "OPENAI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "deepgram": "DEEPGRAM_API_KEY",
        }

        for provider, env_var in env_keys.items():
            value = os.getenv(env_var)
            if value:
                self._keys[provider] = value
                logger.info(f"Loaded {provider} API key from environment")

    def set_key(self, provider: str, api_key: str) -> None:
        """
        Set an API key for a provider.

        Args:
            provider: Provider name (e.g., 'openai', 'openrouter')
            api_key: The API key to store
        """
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty")

        self._keys[provider] = api_key.strip()
        self._save_keys()
        logger.info(f"Set API key for provider: {provider}")

    def get_key(self, provider: str) -> Optional[str]:
        """
        Get an API key for a provider.

        Args:
            provider: Provider name

        Returns:
            API key or None if not found
        """
        return self._keys.get(provider)

    def remove_key(self, provider: str) -> bool:
        """
        Remove an API key for a provider.

        Args:
            provider: Provider name

        Returns:
            True if key was removed, False if not found
        """
        if provider in self._keys:
            del self._keys[provider]
            self._save_keys()
            logger.info(f"Removed API key for provider: {provider}")
            return True
        return False

    def has_key(self, provider: str) -> bool:
        """
        Check if an API key exists for a provider.

        Args:
            provider: Provider name

        Returns:
            True if key exists
        """
        return provider in self._keys and bool(self._keys[provider])

    def list_providers(self) -> list[str]:
        """
        List all providers with stored keys.

        Returns:
            List of provider names
        """
        return list(self._keys.keys())

    def validate_key(self, provider: str, api_key: Optional[str] = None) -> bool:
        """
        Validate an API key format (basic validation).

        Args:
            provider: Provider name
            api_key: Optional key to validate. If not provided, validates stored key.

        Returns:
            True if key appears valid
        """
        key = api_key if api_key is not None else self.get_key(provider)

        if not key:
            return False

        # Basic validation rules
        if provider == "openai":
            return key.startswith("sk-") and len(key) > 20
        elif provider == "openrouter":
            return key.startswith("sk-or-") and len(key) > 20
        elif provider == "anthropic":
            return key.startswith("sk-ant-") and len(key) > 20
        elif provider == "deepgram":
            return len(key) > 20

        # Default: just check it's not empty
        return len(key) > 10

    def clear_all(self) -> None:
        """Clear all stored API keys."""
        self._keys = {}
        self._save_keys()
        logger.info("Cleared all API keys")

    def export_keys(self, include_sensitive: bool = False) -> Dict[str, any]:
        """
        Export key information for UI display.

        Args:
            include_sensitive: If True, include masked keys

        Returns:
            Dictionary with key information
        """
        result = {}
        for provider, key in self._keys.items():
            result[provider] = {
                "has_key": True,
                "valid": self.validate_key(provider),
                "last_updated": datetime.utcnow().isoformat()
            }

            if include_sensitive:
                # Mask the key for display
                if len(key) > 8:
                    masked = key[:4] + "*" * (len(key) - 8) + key[-4:]
                else:
                    masked = "*" * len(key)
                result[provider]["masked_key"] = masked

        return result


# Global instance
_global_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    """Get the global API key manager instance."""
    global _global_manager
    if _global_manager is None:
        _global_manager = APIKeyManager()
    return _global_manager
