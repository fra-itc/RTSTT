"""
Provider Comparison Matrix - Compare features, costs, and performance.

This module provides utilities to compare different STT providers
and help users choose the best one for their needs.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ComparisonCriterion(Enum):
    """Criteria for comparing providers."""
    COST = "cost"
    LATENCY = "latency"
    ACCURACY = "accuracy"
    FEATURES = "features"
    LANGUAGES = "languages"


@dataclass
class ProviderComparison:
    """Comparison data for a single provider."""
    name: str
    type: str  # "local" or "cloud"

    # Cost metrics
    cost_per_minute: Optional[float]  # USD
    cost_per_hour: Optional[float]  # USD
    setup_cost: float = 0.0  # One-time setup cost

    # Performance metrics
    latency_ms: Optional[int]  # Typical latency
    throughput: Optional[str]  # e.g., "real-time", "2x", "5x"

    # Accuracy (if available)
    wer: Optional[float] = None  # Word Error Rate
    cer: Optional[float] = None  # Character Error Rate

    # Capabilities
    streaming: bool = False
    batch: bool = True
    diarization: bool = False
    word_timestamps: bool = False
    punctuation: bool = False
    speaker_labels: bool = False
    translation: bool = False

    # Language support
    num_languages: int = 1
    supports_italian: bool = True
    supports_english: bool = True

    # Technical requirements
    requires_api_key: bool = True
    requires_gpu: bool = False
    max_audio_length: Optional[int] = None  # seconds
    max_file_size: Optional[int] = None  # MB

    # Notes
    notes: str = ""


# Provider comparison data
PROVIDER_COMPARISONS = [
    # Local Whisper Large-v3
    ProviderComparison(
        name="Local Whisper Large-v3",
        type="local",
        cost_per_minute=0.0,
        cost_per_hour=0.0,
        setup_cost=0.0,  # Assuming GPU already available
        latency_ms=300,
        throughput="real-time",
        wer=None,  # Varies by language
        streaming=True,
        batch=True,
        diarization=False,
        word_timestamps=True,
        punctuation=True,
        speaker_labels=False,
        translation=True,
        num_languages=99,
        supports_italian=True,
        supports_english=True,
        requires_api_key=False,
        requires_gpu=True,
        max_audio_length=None,
        max_file_size=None,
        notes="Free, requires NVIDIA GPU with 8GB+ VRAM. Best for privacy and offline use."
    ),

    # OpenAI Whisper API
    ProviderComparison(
        name="OpenAI Whisper API",
        type="cloud",
        cost_per_minute=0.006,
        cost_per_hour=0.36,
        latency_ms=2000,
        throughput="~2x real-time",
        streaming=False,
        batch=True,
        diarization=False,
        word_timestamps=True,
        punctuation=True,
        speaker_labels=False,
        translation=True,
        num_languages=99,
        supports_italian=True,
        supports_english=True,
        requires_api_key=True,
        requires_gpu=False,
        max_audio_length=None,
        max_file_size=25,
        notes="Based on Whisper Large-v2. Simple API, good accuracy, 25MB file limit."
    ),

    # Deepgram Nova-2
    ProviderComparison(
        name="Deepgram Nova-2",
        type="cloud",
        cost_per_minute=0.0043,
        cost_per_hour=0.258,
        latency_ms=50,
        throughput="real-time",
        streaming=True,
        batch=True,
        diarization=True,
        word_timestamps=True,
        punctuation=True,
        speaker_labels=True,
        translation=False,
        num_languages=36,
        supports_italian=True,
        supports_english=True,
        requires_api_key=True,
        requires_gpu=False,
        max_audio_length=None,
        max_file_size=None,
        notes="Ultra-low latency, real-time streaming, speaker diarization. Best for live transcription."
    ),

    # Deepgram Nova-3
    ProviderComparison(
        name="Deepgram Nova-3",
        type="cloud",
        cost_per_minute=0.0059,
        cost_per_hour=0.354,
        latency_ms=50,
        throughput="real-time",
        streaming=True,
        batch=True,
        diarization=True,
        word_timestamps=True,
        punctuation=True,
        speaker_labels=True,
        translation=False,
        num_languages=36,
        supports_italian=True,
        supports_english=True,
        requires_api_key=True,
        requires_gpu=False,
        max_audio_length=None,
        max_file_size=None,
        notes="Most accurate Deepgram model. Excellent for production use."
    ),

    # AssemblyAI Universal-2
    ProviderComparison(
        name="AssemblyAI Universal-2",
        type="cloud",
        cost_per_minute=0.015,
        cost_per_hour=0.90,
        latency_ms=5000,
        throughput="varies",
        streaming=False,  # Has separate real-time API
        batch=True,
        diarization=True,
        word_timestamps=True,
        punctuation=True,
        speaker_labels=True,
        translation=False,
        num_languages=99,
        supports_italian=True,
        supports_english=True,
        requires_api_key=True,
        requires_gpu=False,
        max_audio_length=None,
        max_file_size=None,
        notes="Advanced features: sentiment analysis, entity detection, auto chapters. Higher cost but rich insights."
    ),
]


def get_all_comparisons() -> List[ProviderComparison]:
    """Get all provider comparisons."""
    return PROVIDER_COMPARISONS


def get_comparison_by_name(name: str) -> Optional[ProviderComparison]:
    """Get comparison for a specific provider."""
    for comp in PROVIDER_COMPARISONS:
        if comp.name.lower() == name.lower():
            return comp
    return None


def compare_by_cost(
    duration_minutes: float = 60.0,
    include_local: bool = True
) -> List[Dict[str, Any]]:
    """
    Compare providers by cost.

    Args:
        duration_minutes: Expected usage in minutes per month
        include_local: Include local providers (zero cost)

    Returns:
        List of providers sorted by cost (cheapest first)
    """
    comparisons = []

    for provider in PROVIDER_COMPARISONS:
        if not include_local and provider.type == "local":
            continue

        monthly_cost = (provider.cost_per_minute or 0) * duration_minutes
        total_cost = monthly_cost + provider.setup_cost

        comparisons.append({
            "name": provider.name,
            "type": provider.type,
            "cost_per_minute": provider.cost_per_minute,
            "monthly_cost": monthly_cost,
            "total_cost": total_cost,
            "setup_cost": provider.setup_cost,
        })

    # Sort by total cost
    comparisons.sort(key=lambda x: x["total_cost"])
    return comparisons


def compare_by_latency() -> List[Dict[str, Any]]:
    """
    Compare providers by latency.

    Returns:
        List of providers sorted by latency (fastest first)
    """
    comparisons = []

    for provider in PROVIDER_COMPARISONS:
        if provider.latency_ms is not None:
            comparisons.append({
                "name": provider.name,
                "latency_ms": provider.latency_ms,
                "streaming": provider.streaming,
                "type": provider.type,
            })

    # Sort by latency
    comparisons.sort(key=lambda x: x["latency_ms"])
    return comparisons


def compare_by_features() -> List[Dict[str, Any]]:
    """
    Compare providers by features.

    Returns:
        List of providers with feature scores
    """
    comparisons = []

    for provider in PROVIDER_COMPARISONS:
        # Calculate feature score
        feature_count = sum([
            provider.streaming,
            provider.batch,
            provider.diarization,
            provider.word_timestamps,
            provider.punctuation,
            provider.speaker_labels,
            provider.translation,
        ])

        comparisons.append({
            "name": provider.name,
            "feature_score": feature_count,
            "features": {
                "streaming": provider.streaming,
                "batch": provider.batch,
                "diarization": provider.diarization,
                "word_timestamps": provider.word_timestamps,
                "punctuation": provider.punctuation,
                "speaker_labels": provider.speaker_labels,
                "translation": provider.translation,
            },
            "num_languages": provider.num_languages,
        })

    # Sort by feature score
    comparisons.sort(key=lambda x: x["feature_score"], reverse=True)
    return comparisons


def get_best_for_use_case(
    use_case: str,
    budget_per_hour: Optional[float] = None,
    requires_streaming: bool = False,
    requires_diarization: bool = False,
) -> List[str]:
    """
    Get recommended providers for a specific use case.

    Args:
        use_case: "real-time", "batch", "transcription", "analysis"
        budget_per_hour: Maximum budget per hour (USD)
        requires_streaming: Whether streaming is required
        requires_diarization: Whether speaker diarization is required

    Returns:
        List of recommended provider names
    """
    recommendations = []

    for provider in PROVIDER_COMPARISONS:
        # Check budget
        if budget_per_hour is not None and provider.cost_per_hour is not None:
            if provider.cost_per_hour > budget_per_hour:
                continue

        # Check streaming requirement
        if requires_streaming and not provider.streaming:
            continue

        # Check diarization requirement
        if requires_diarization and not provider.diarization:
            continue

        # Use case specific logic
        if use_case == "real-time":
            if provider.streaming and provider.latency_ms and provider.latency_ms < 1000:
                recommendations.append(provider.name)

        elif use_case == "batch":
            if provider.batch:
                recommendations.append(provider.name)

        elif use_case == "transcription":
            # Simple transcription - prefer low cost
            recommendations.append(provider.name)

        elif use_case == "analysis":
            # Advanced analysis - prefer features
            if provider.diarization or provider.speaker_labels:
                recommendations.append(provider.name)

    return recommendations


def generate_comparison_table() -> str:
    """
    Generate a markdown comparison table.

    Returns:
        str: Markdown formatted table
    """
    lines = [
        "# STT Provider Comparison",
        "",
        "| Provider | Type | Cost/min | Latency | Streaming | Diarization | Languages |",
        "|----------|------|----------|---------|-----------|-------------|-----------|",
    ]

    for provider in PROVIDER_COMPARISONS:
        cost_str = f"${provider.cost_per_minute:.4f}" if provider.cost_per_minute else "Free"
        latency_str = f"{provider.latency_ms}ms" if provider.latency_ms else "N/A"
        streaming_str = "✅" if provider.streaming else "❌"
        diarization_str = "✅" if provider.diarization else "❌"

        line = f"| {provider.name} | {provider.type} | {cost_str} | {latency_str} | {streaming_str} | {diarization_str} | {provider.num_languages}+ |"
        lines.append(line)

    lines.extend([
        "",
        "## Feature Comparison",
        "",
        "| Provider | Word Timestamps | Punctuation | Translation | Speaker Labels |",
        "|----------|-----------------|-------------|-------------|----------------|",
    ])

    for provider in PROVIDER_COMPARISONS:
        timestamps_str = "✅" if provider.word_timestamps else "❌"
        punct_str = "✅" if provider.punctuation else "❌"
        trans_str = "✅" if provider.translation else "❌"
        labels_str = "✅" if provider.speaker_labels else "❌"

        line = f"| {provider.name} | {timestamps_str} | {punct_str} | {trans_str} | {labels_str} |"
        lines.append(line)

    lines.extend([
        "",
        "## Cost Comparison (1 hour of audio)",
        "",
        "| Provider | Cost/hour | Notes |",
        "|----------|-----------|-------|",
    ])

    for provider in PROVIDER_COMPARISONS:
        cost_str = f"${provider.cost_per_hour:.2f}" if provider.cost_per_hour else "Free"
        line = f"| {provider.name} | {cost_str} | {provider.notes[:50]}... |"
        lines.append(line)

    return "\n".join(lines)


def export_comparison_json() -> List[Dict[str, Any]]:
    """Export comparison data as JSON-serializable list."""
    return [asdict(comp) for comp in PROVIDER_COMPARISONS]


# Quick reference
QUICK_RECOMMENDATIONS = {
    "lowest_cost": "Local Whisper Large-v3",
    "lowest_cloud_cost": "Deepgram Nova-2",
    "lowest_latency": "Deepgram Nova-2",
    "most_features": "AssemblyAI Universal-2",
    "best_streaming": "Deepgram Nova-3",
    "best_offline": "Local Whisper Large-v3",
    "best_accuracy": "Deepgram Nova-3",
    "easiest_setup": "OpenAI Whisper API",
}
