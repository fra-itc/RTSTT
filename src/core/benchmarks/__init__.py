"""
Benchmarking framework for STT model comparison.

This module provides comprehensive benchmarking capabilities for comparing
11 different STT models across accuracy, performance, cost, and resource usage.
"""

from .providers.base_provider import STTProvider, ProviderType
from .metrics import BenchmarkMetrics, calculate_wer, calculate_cer, calculate_rtfx
from .benchmark_runner import BenchmarkRunner
from .dataset_manager import DatasetManager
from .resource_monitor import ResourceMonitor
from .cost_estimator import CostEstimator

__all__ = [
    'STTProvider',
    'ProviderType',
    'BenchmarkMetrics',
    'BenchmarkRunner',
    'DatasetManager',
    'ResourceMonitor',
    'CostEstimator',
    'calculate_wer',
    'calculate_cer',
    'calculate_rtfx',
]
