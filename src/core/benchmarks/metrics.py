"""
Metrics calculation for STT benchmarking.

Provides functions to calculate:
- Word Error Rate (WER)
- Character Error Rate (CER)
- Real-Time Factor (RTFx)
- Confidence scores
- Latency percentiles
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkMetrics:
    """
    Comprehensive metrics for STT model benchmarking.

    Tracks accuracy, performance, resource usage, and cost.
    """
    provider_name: str
    model_name: str

    # Accuracy metrics
    wer: float = 0.0  # Word Error Rate (lower is better)
    cer: float = 0.0  # Character Error Rate (lower is better)
    avg_confidence: float = 0.0  # Average confidence score

    # Performance metrics
    rtfx: float = 0.0  # Real-Time Factor (lower is better, <1.0 = faster than real-time)
    latency_p50_ms: float = 0.0  # Median latency
    latency_p95_ms: float = 0.0  # 95th percentile latency
    latency_p99_ms: float = 0.0  # 99th percentile latency
    throughput_hours_per_hour: float = 0.0  # Audio hours processed per wall-clock hour

    # Resource usage
    gpu_memory_mb: float = 0.0  # GPU memory usage
    cpu_percent: float = 0.0  # CPU usage percentage
    ram_mb: float = 0.0  # RAM usage

    # Cost metrics
    cost_per_minute: float = 0.0  # USD per minute of audio
    cost_per_hour: float = 0.0  # USD per hour of audio

    # Metadata
    audio_duration_seconds: float = 0.0  # Total audio processed
    test_timestamp: datetime = field(default_factory=datetime.now)
    hardware: str = "Unknown"  # GPU model or "CPU"
    provider_type: str = "local"  # "local" or "cloud"

    # Detailed results
    sample_count: int = 0
    latencies_ms: List[float] = field(default_factory=list)
    wer_per_sample: List[float] = field(default_factory=list)
    cer_per_sample: List[float] = field(default_factory=list)

    def calculate_derived_metrics(self) -> None:
        """Calculate derived metrics from raw data."""
        if self.latencies_ms:
            self.latency_p50_ms = float(np.percentile(self.latencies_ms, 50))
            self.latency_p95_ms = float(np.percentile(self.latencies_ms, 95))
            self.latency_p99_ms = float(np.percentile(self.latencies_ms, 99))

        if self.wer_per_sample:
            self.wer = float(np.mean(self.wer_per_sample))

        if self.cer_per_sample:
            self.cer = float(np.mean(self.cer_per_sample))

        if self.cost_per_minute > 0:
            self.cost_per_hour = self.cost_per_minute * 60

        # Calculate throughput: how many audio hours can be processed per wall-clock hour
        if self.rtfx > 0:
            self.throughput_hours_per_hour = 1.0 / self.rtfx

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "wer": self.wer,
            "cer": self.cer,
            "avg_confidence": self.avg_confidence,
            "rtfx": self.rtfx,
            "latency_p50_ms": self.latency_p50_ms,
            "latency_p95_ms": self.latency_p95_ms,
            "latency_p99_ms": self.latency_p99_ms,
            "throughput_hours_per_hour": self.throughput_hours_per_hour,
            "gpu_memory_mb": self.gpu_memory_mb,
            "cpu_percent": self.cpu_percent,
            "ram_mb": self.ram_mb,
            "cost_per_minute": self.cost_per_minute,
            "cost_per_hour": self.cost_per_hour,
            "audio_duration_seconds": self.audio_duration_seconds,
            "test_timestamp": self.test_timestamp.isoformat(),
            "hardware": self.hardware,
            "provider_type": self.provider_type,
            "sample_count": self.sample_count,
        }

    def get_score(self) -> float:
        """
        Calculate overall score (0-10) based on multiple factors.

        Weighs accuracy (40%), speed (30%), and cost (30%).
        """
        # Accuracy score (based on WER, lower is better)
        # Excellent: <5% WER = 10, Good: 5-10% = 8, Fair: 10-20% = 5, Poor: >20% = 0
        if self.wer <= 0.05:
            accuracy_score = 10.0
        elif self.wer <= 0.10:
            accuracy_score = 10.0 - ((self.wer - 0.05) / 0.05) * 2.0
        elif self.wer <= 0.20:
            accuracy_score = 8.0 - ((self.wer - 0.10) / 0.10) * 3.0
        else:
            accuracy_score = max(0.0, 5.0 - ((self.wer - 0.20) / 0.10))

        # Speed score (based on RTFx and latency)
        # Real-time streaming: <100ms latency, RTFx < 0.1 = 10
        # Fast batch: RTFx < 0.5 = 8
        # Moderate: RTFx < 1.0 = 5
        # Slow: RTFx > 1.0 = 0-3
        if self.latency_p50_ms < 100 and self.rtfx < 0.1:
            speed_score = 10.0
        elif self.rtfx < 0.5:
            speed_score = 8.0 + (0.5 - self.rtfx) * 4.0
        elif self.rtfx < 1.0:
            speed_score = 5.0 + (1.0 - self.rtfx) * 6.0
        else:
            speed_score = max(0.0, 5.0 - (self.rtfx - 1.0) * 2.0)

        # Cost score (based on cost per hour)
        # Free: 10, <$0.10/hr: 9, <$0.50/hr: 7, <$1/hr: 5, >$1/hr: 0-3
        if self.cost_per_hour == 0:
            cost_score = 10.0
        elif self.cost_per_hour < 0.10:
            cost_score = 9.0
        elif self.cost_per_hour < 0.50:
            cost_score = 7.0 - ((self.cost_per_hour - 0.10) / 0.40) * 2.0
        elif self.cost_per_hour < 1.0:
            cost_score = 5.0 - ((self.cost_per_hour - 0.50) / 0.50) * 2.0
        else:
            cost_score = max(0.0, 3.0 - (self.cost_per_hour - 1.0))

        # Weighted average
        total_score = (accuracy_score * 0.4) + (speed_score * 0.3) + (cost_score * 0.3)
        return round(total_score, 2)


def calculate_wer(reference: str, hypothesis: str) -> float:
    """
    Calculate Word Error Rate using Levenshtein distance.

    WER = (Substitutions + Deletions + Insertions) / Total Words in Reference

    Args:
        reference: Ground truth transcription
        hypothesis: Model's transcription

    Returns:
        float: WER as a decimal (0.0 = perfect, 1.0 = completely wrong)
    """
    # Normalize: lowercase and split into words
    ref_words = reference.lower().split()
    hyp_words = hypothesis.lower().split()

    # Handle edge cases
    if len(ref_words) == 0:
        return 1.0 if len(hyp_words) > 0 else 0.0

    # Calculate Levenshtein distance at word level
    distance = _levenshtein_distance(ref_words, hyp_words)

    # WER = edit distance / reference length
    wer = distance / len(ref_words)

    return min(wer, 1.0)  # Cap at 1.0


def calculate_cer(reference: str, hypothesis: str) -> float:
    """
    Calculate Character Error Rate using Levenshtein distance.

    CER = (Substitutions + Deletions + Insertions) / Total Characters in Reference

    Args:
        reference: Ground truth transcription
        hypothesis: Model's transcription

    Returns:
        float: CER as a decimal (0.0 = perfect, 1.0 = completely wrong)
    """
    # Normalize: lowercase and remove spaces for character-level comparison
    ref_chars = list(reference.lower().replace(" ", ""))
    hyp_chars = list(hypothesis.lower().replace(" ", ""))

    # Handle edge cases
    if len(ref_chars) == 0:
        return 1.0 if len(hyp_chars) > 0 else 0.0

    # Calculate Levenshtein distance at character level
    distance = _levenshtein_distance(ref_chars, hyp_chars)

    # CER = edit distance / reference length
    cer = distance / len(ref_chars)

    return min(cer, 1.0)  # Cap at 1.0


def calculate_rtfx(audio_duration_seconds: float, processing_time_seconds: float) -> float:
    """
    Calculate Real-Time Factor.

    RTFx = processing_time / audio_duration
    - RTFx < 1.0: Faster than real-time (can process audio faster than it plays)
    - RTFx = 1.0: Exactly real-time
    - RTFx > 1.0: Slower than real-time

    Args:
        audio_duration_seconds: Duration of audio in seconds
        processing_time_seconds: Time taken to process in seconds

    Returns:
        float: Real-Time Factor
    """
    if audio_duration_seconds <= 0:
        return 0.0

    return processing_time_seconds / audio_duration_seconds


def _levenshtein_distance(seq1: List[str], seq2: List[str]) -> int:
    """
    Calculate Levenshtein distance between two sequences.

    Dynamic programming implementation.

    Args:
        seq1: First sequence (reference)
        seq2: Second sequence (hypothesis)

    Returns:
        int: Edit distance
    """
    m, n = len(seq1), len(seq2)

    # Create DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Initialize base cases
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    # Fill DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]  # No operation needed
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],      # Deletion
                    dp[i][j - 1],      # Insertion
                    dp[i - 1][j - 1]   # Substitution
                )

    return dp[m][n]


def calculate_latency_percentiles(latencies_ms: List[float]) -> Dict[str, float]:
    """
    Calculate latency percentiles.

    Args:
        latencies_ms: List of latency measurements in milliseconds

    Returns:
        Dict with p50, p95, p99 percentiles
    """
    if not latencies_ms:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0}

    return {
        "p50": float(np.percentile(latencies_ms, 50)),
        "p95": float(np.percentile(latencies_ms, 95)),
        "p99": float(np.percentile(latencies_ms, 99)),
    }


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison.

    - Lowercase
    - Remove extra whitespace
    - Remove punctuation (optional)

    Args:
        text: Input text

    Returns:
        str: Normalized text
    """
    import re

    # Lowercase
    text = text.lower()

    # Remove punctuation (keep apostrophes for contractions)
    text = re.sub(r'[^\w\s\']', '', text)

    # Normalize whitespace
    text = ' '.join(text.split())

    return text.strip()
