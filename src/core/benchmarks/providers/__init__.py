"""
STT Provider implementations for benchmarking.

Supports 11 different providers:
- Local: Whisper Large-v3, Voxtral Mini, Parakeet, WhisperLiveKit, Vosk, RealtimeSTT
- Cloud: OpenAI, Deepgram, AssemblyAI, Mistral, Google/Azure
"""

from .base_provider import STTProvider, ProviderType, TranscriptionResult
from .whisper_provider import WhisperProvider
from .voxtral_provider import VoxtralProvider
from .parakeet_provider import ParakeetProvider
from .whisper_livekit_provider import WhisperLiveKitProvider
from .vosk_provider import VoskProvider
from .realtime_stt_provider import RealtimeSTTProvider
from .openai_provider import OpenAIProvider
from .deepgram_provider import DeepgramProvider
from .assemblyai_provider import AssemblyAIProvider
from .mistral_provider import MistralProvider
from .google_azure_provider import GoogleAzureProvider

__all__ = [
    'STTProvider',
    'ProviderType',
    'TranscriptionResult',
    'WhisperProvider',
    'VoxtralProvider',
    'ParakeetProvider',
    'WhisperLiveKitProvider',
    'VoskProvider',
    'RealtimeSTTProvider',
    'OpenAIProvider',
    'DeepgramProvider',
    'AssemblyAIProvider',
    'MistralProvider',
    'GoogleAzureProvider',
]
