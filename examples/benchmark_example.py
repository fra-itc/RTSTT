#!/usr/bin/env python3
"""
Example: How to use the STT Benchmarking Framework

This example demonstrates:
1. Creating a test dataset
2. Registering STT providers
3. Running benchmarks
4. Generating reports
5. Querying results from database
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.benchmarks import (
    BenchmarkRunner,
    DatasetManager,
    ResourceMonitor,
    CostEstimator
)
from src.core.benchmarks.providers import WhisperProvider
from src.core.benchmarks.report_generator import ReportGenerator
from src.core.benchmarks.results_storage import ResultsStorage


def example_basic_benchmark():
    """Example 1: Basic benchmark with Whisper."""
    print("=" * 80)
    print("Example 1: Basic Benchmark")
    print("=" * 80)

    # Initialize components
    project_root = Path(__file__).parent.parent
    dataset_root = project_root / "benchmarks" / "datasets"
    output_dir = project_root / "benchmarks" / "results" / "examples"

    # Create dataset manager
    dataset_manager = DatasetManager(dataset_root)

    # Create a simple test dataset
    print("\n1. Creating test dataset...")
    samples = [
        {
            "audio_path": str(dataset_root / "sample_audio" / "test1.wav"),
            "transcription": "This is a test transcription.",
            "language": "en"
        }
    ]

    # Note: This will fail if audio files don't exist - that's expected
    try:
        dataset_manager.create_dataset("example_test", samples, copy_audio=False)
        print("   ✓ Dataset created")
    except Exception as e:
        print(f"   ⚠ Dataset creation skipped: {e}")
        print("   (This is expected if you don't have test audio files)")

    # Initialize benchmark components
    print("\n2. Initializing benchmark runner...")
    resource_monitor = ResourceMonitor()
    cost_estimator = CostEstimator()

    runner = BenchmarkRunner(
        dataset_manager=dataset_manager,
        output_dir=output_dir,
        resource_monitor=resource_monitor,
        cost_estimator=cost_estimator
    )

    # Register Whisper provider
    print("\n3. Registering Whisper provider...")
    whisper = WhisperProvider(model_size="large-v3", device="cuda")
    runner.register_provider(whisper)
    print("   ✓ Whisper Large-v3 registered")

    # Run benchmark (will skip if no dataset)
    print("\n4. Running benchmark...")
    print("   (Skipped - create actual audio files first)")
    # results = runner.run_benchmark("example_test")

    print("\n✓ Example 1 complete")


def example_multiple_providers():
    """Example 2: Benchmark multiple providers."""
    print("\n" + "=" * 80)
    print("Example 2: Multiple Providers")
    print("=" * 80)

    project_root = Path(__file__).parent.parent

    # Create providers
    print("\n1. Creating provider instances...")

    providers = [
        WhisperProvider(model_size="large-v3"),
        WhisperProvider(model_size="medium"),
        # Uncomment if you have API keys:
        # OpenAIProvider(api_key="sk-..."),
        # DeepgramProvider(api_key="..."),
    ]

    print(f"   ✓ Created {len(providers)} providers")

    # Show provider info
    print("\n2. Provider information:")
    for provider in providers:
        info = provider.get_provider_info()
        cost = provider.get_cost_per_minute() * 60  # Cost per hour
        print(f"   - {provider}: ${cost:.2f}/hour" if cost > 0 else f"   - {provider}: FREE")

    print("\n✓ Example 2 complete")


def example_cost_analysis():
    """Example 3: Cost comparison analysis."""
    print("\n" + "=" * 80)
    print("Example 3: Cost Analysis")
    print("=" * 80)

    from src.core.benchmarks import CostEstimator

    print("\n1. Initializing cost estimator...")
    estimator = CostEstimator(
        electricity_rate_per_kwh=0.15,
        gpu_cost=1500.0,
        gpu_lifetime_years=3.0
    )

    # Compare costs for different usage levels
    print("\n2. Cost comparison for 100 hours of audio:")
    print("-" * 80)

    comparison = estimator.compare_costs(
        audio_hours=100,
        providers=[
            ("Whisper", "Large-v3"),
            ("OpenAI", "Whisper-1"),
            ("Deepgram", "Nova-3"),
            ("AssemblyAI", "Universal-2"),
        ]
    )

    print(f"{'Provider':<25} {'Type':<10} {'API Cost':<12} {'Infra Cost':<12} {'Total':<12}")
    print("-" * 80)

    for item in comparison:
        provider = f"{item['provider_name']} {item['model_name']}"
        print(
            f"{provider:<25} "
            f"{item['pricing_model']:<10} "
            f"${item['api_cost']:<11.2f} "
            f"${item['infrastructure_cost']:<11.2f} "
            f"${item['total_cost']:<11.2f}"
        )

    # Break-even analysis
    print("\n3. Break-even analysis (Cloud vs. Local):")
    print("-" * 80)

    breakeven = estimator.calculate_breakeven(
        cloud_provider="Deepgram",
        cloud_model="Nova-3",
        local_provider="Whisper",
        local_model="Large-v3"
    )

    if breakeven:
        print(f"   Break-even at: {breakeven:.0f} hours")
        print(f"   After {breakeven:.0f} hours, local hosting becomes cheaper")
    else:
        print("   Cloud is cheaper for all usage levels")

    # Monthly cost estimate
    print("\n4. Monthly cost estimates (5 hours/day):")
    print("-" * 80)

    for provider_name, model_name in [("Whisper", "Large-v3"), ("Deepgram", "Nova-3"), ("OpenAI", "Whisper-1")]:
        monthly = estimator.estimate_monthly_cost(provider_name, model_name, hours_per_day=5)
        if monthly:
            print(
                f"   {provider_name} {model_name}: "
                f"${monthly['total_monthly_cost']:.2f}/month"
            )

    print("\n✓ Example 3 complete")


def example_metrics_calculation():
    """Example 4: Calculate WER and CER."""
    print("\n" + "=" * 80)
    print("Example 4: Metrics Calculation")
    print("=" * 80)

    from src.core.benchmarks.metrics import calculate_wer, calculate_cer, calculate_rtfx

    # Example transcriptions
    reference = "The quick brown fox jumps over the lazy dog"
    hypotheses = [
        "The quick brown fox jumps over the lazy dog",  # Perfect
        "The quick brown fox jumped over the lazy dog",  # One error
        "The quick brown fox jumps over lazy dog",  # Two errors
        "A quick brown fox jumps over the lazy dog",  # Substitution
    ]

    print("\n1. Word Error Rate (WER) calculations:")
    print(f"   Reference: '{reference}'")
    print("-" * 80)

    for i, hyp in enumerate(hypotheses, 1):
        wer = calculate_wer(reference, hyp)
        cer = calculate_cer(reference, hyp)
        print(f"   Hypothesis {i}: '{hyp}'")
        print(f"      WER: {wer*100:.2f}%, CER: {cer*100:.2f}%")

    # RTFx calculation
    print("\n2. Real-Time Factor (RTFx) calculations:")
    print("-" * 80)

    examples = [
        (60.0, 30.0, "Faster than real-time"),
        (60.0, 60.0, "Exactly real-time"),
        (60.0, 120.0, "Slower than real-time"),
    ]

    for audio_duration, processing_time, description in examples:
        rtfx = calculate_rtfx(audio_duration, processing_time)
        print(f"   Audio: {audio_duration}s, Processing: {processing_time}s")
        print(f"      RTFx: {rtfx:.2f}x ({description})")

    print("\n✓ Example 4 complete")


def example_resource_monitoring():
    """Example 5: Resource monitoring."""
    print("\n" + "=" * 80)
    print("Example 5: Resource Monitoring")
    print("=" * 80)

    from src.core.benchmarks import ResourceMonitor
    import time

    print("\n1. Initializing resource monitor...")
    monitor = ResourceMonitor(interval_seconds=0.5)

    # Get GPU info
    gpu_info = monitor.get_gpu_info()
    print("\n2. GPU Information:")
    if gpu_info.get("available"):
        print(f"   Name: {gpu_info.get('name')}")
        print(f"   Memory: {gpu_info.get('memory_total_mb')} MB")
        print(f"   Driver: {gpu_info.get('driver_version')}")
    else:
        print("   No NVIDIA GPU detected")

    # Take snapshot
    print("\n3. Current resource usage:")
    snapshot = monitor.take_snapshot()
    print(f"   GPU Memory: {snapshot.gpu_memory_used_mb:.0f} MB")
    print(f"   CPU: {snapshot.cpu_percent:.1f}%")
    print(f"   RAM: {snapshot.ram_used_mb:.0f} MB")

    # Monitor for a few seconds
    print("\n4. Monitoring for 3 seconds...")
    monitor.start_monitoring()
    time.sleep(3)
    stats = monitor.stop_monitoring()

    print(f"   Avg GPU Memory: {stats.avg_gpu_memory_mb:.0f} MB")
    print(f"   Max GPU Memory: {stats.max_gpu_memory_mb:.0f} MB")
    print(f"   Avg CPU: {stats.avg_cpu_percent:.1f}%")
    print(f"   Snapshots collected: {len(stats.snapshots)}")

    print("\n✓ Example 5 complete")


def example_results_storage():
    """Example 6: Store and query results."""
    print("\n" + "=" * 80)
    print("Example 6: Results Storage")
    print("=" * 80)

    project_root = Path(__file__).parent.parent
    db_path = project_root / "benchmarks" / "results" / "examples" / "example.db"

    print("\n1. Initializing results storage...")
    with ResultsStorage(db_path) as storage:
        # List runs
        print("\n2. Listing recent benchmark runs:")
        runs = storage.list_runs(limit=5)

        if runs:
            for run in runs:
                print(f"   - Run {run['run_id']}: {run['run_name']} ({run['timestamp']})")
        else:
            print("   No runs found (database is empty)")

        # Get best providers
        print("\n3. Best providers by WER:")
        best = storage.get_best_providers(metric="wer", limit=5)

        if best:
            for item in best:
                print(
                    f"   - {item['provider_name']} {item['model_name']}: "
                    f"{item['avg_wer']*100:.2f}% WER"
                )
        else:
            print("   No results available")

    print("\n✓ Example 6 complete")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("STT Benchmarking Framework - Examples")
    print("=" * 80)

    try:
        example_basic_benchmark()
        example_multiple_providers()
        example_cost_analysis()
        example_metrics_calculation()
        example_resource_monitoring()
        example_results_storage()

        print("\n" + "=" * 80)
        print("All examples completed successfully!")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Create actual test audio files")
        print("2. Run: python scripts/create_test_dataset.py")
        print("3. Run: python scripts/run_benchmarks.py --quick")
        print("4. View reports in benchmarks/results/reports/")
        print()

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
