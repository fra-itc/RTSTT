"""
Audio capture drivers

Platform-specific audio capture implementations.
"""

from typing import Dict, Type

# Import drivers as they are implemented
# from .wasapi_driver import WASAPIDriver
# from .pulseaudio_driver import PulseAudioDriver
# from .alsa_driver import ALSADriver
# from .portaudio_driver import PortAudioDriver
from .mock_driver import MockAudioDriver

# Driver registry for factory
AVAILABLE_DRIVERS: Dict[str, Type] = {
    'mock': MockAudioDriver,
}

__all__ = [
    'MockAudioDriver',
    'AVAILABLE_DRIVERS',
]
