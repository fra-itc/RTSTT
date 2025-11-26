#!/usr/bin/env python3
"""
Automated STT Benchmark Runner

Run benchmarks across multiple STT providers with comprehensive metrics collection.

Usage:
    python scripts/run_benchmarks.py --quick
    python scripts/run_benchmarks.py --dataset test_dataset --providers whisper openai
    python scripts/run_benchmarks.py --full --parallel
"""

import sys
import argparse
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.benchmarks import (
    BenchmarkRunner,
    DatasetManager,
    ResourceMonitor,
    CostEstimator
)
from src.core.benchmarks.providers import (
    WhisperProvider,
    OpenAIProvider,
    DeepgramProvider,
    AssemblyAIProvider,
    MistralProvider,
    GoogleAzureProvider,
    VoxtralProvider,
    ParakeetProvider,
    WhisperLiveKitProvider,
    VoskProvider,
    RealtimeSTTProvider
)
from src.core.benchmarks.report_generator import ReportGenerator
from src.core.benchmarks.results_storage import ResultsStorage

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Provider factory
AVAILABLE_PROVIDERS = {
    "whisper": lambda: WhisperProvider(model_size="large-v3"),
    "whisper-medium": lambda: WhisperProvider(model_size="medium"),
    "whisper-small": lambda: WhisperProvider(model_size="small"),
    "openai": lambda: OpenAIProvider(),
    "deepgram": lambda: DeepgramProvider(),
    "assemblyai": lambda: AssemblyAIProvider(),
    "mistral": lambda: MistralProvider(),
    "google": lambda: GoogleAzureProvider(service="google"),
    "azure": lambda: GoogleAzureProvider(service="azure"),
    "voxtral": lambda: VoxtralProvider(),
    "parakeet": lambda: ParakeetProvider(),
    "whisper-livekit": lambda: WhisperLiveKitProvider(),
    "vosk": lambda: VoskProvider(),
    "realtime-stt": lambda: RealtimeSTTProvider(),
}


def create_quick_test_dataset(dataset_manager: DatasetManager) -> str:
    """
    Create a quick test dataset with sample audio.

    Args:
        dataset_manager: DatasetManager instance

    Returns:
        str: Dataset name
    """
    logger.info("Creating quick test dataset...")

    # Create a simple test dataset
    # In practice, you would have actual audio files
    samples = [
        {
            "audio_path": "/path/to/sample1.wav",
            "transcription": "This is a test transcription.",
            "language": "en",
            "speaker": "speaker1"
        },
        # Add more samples as needed
    ]

    dataset_name = "quick_test"

    try:
        dataset_manager.create_dataset(
            dataset_name=dataset_name,
            samples=samples,
            copy_audio=False
        )
    except Exception as e:
        logger.warning(f"Failed to create dataset: {e}")
        # Return empty dataset name if creation fails
        return ""

    return dataset_name


def run_quick_benchmark(args):
    """Run a quick benchmark with a few samples."""
    logger.info("Starting quick benchmark...")

    # Initialize components
    project_root = Path(__file__).parent.parent
    dataset_root = project_root / "benchmarks" / "datasets"
    output_dir = project_root / "benchmarks" / "results"

    dataset_manager = DatasetManager(dataset_root)
    resource_monitor = ResourceMonitor(interval_seconds=1.0)
    cost_estimator = CostEstimator()
    benchmark_runner = BenchmarkRunner(
        dataset_manager=dataset_manager,
        output_dir=output_dir,
        resource_monitor=resource_monitor,
        cost_estimator=cost_estimator
    )

    # Create or load quick test dataset
    dataset_name = "quick_test"

    if not dataset_manager.get_dataset(dataset_name):
        logger.warning(f"Dataset '{dataset_name}' not found. Please create test audio samples first.")
        logger.info("See documentation for dataset creation instructions.")
        return

    # Register providers to test (only Whisper for quick test)
    providers_to_test = ["whisper"]
    if args.providers:
        providers_to_test = args.providers

    providers = []
    for provider_name in providers_to_test:
        if provider_name in AVAILABLE_PROVIDERS:
            try:
                provider = AVAILABLE_PROVIDERS[provider_name]()
                providers.append(provider)
                logger.info(f"Registered provider: {provider}")
            except Exception as e:
                logger.error(f"Failed to create provider '{provider_name}': {e}")

    if not providers:
        logger.error("No providers available to test")
        return

    benchmark_runner.register_providers(providers)

    # Run benchmark
    logger.info(f"Running benchmark on {len(providers)} provider(s)...")
    results = benchmark_runner.run_benchmark(
        dataset_name=dataset_name,
        parallel=args.parallel,
        max_workers=args.max_workers
    )

    # Print summary
    benchmark_runner.print_summary(results)

    # Generate reports
    report_generator = ReportGenerator(output_dir / "reports")
    report_paths = report_generator.generate_all_reports(results, dataset_name)

    logger.info("Reports generated:")
    for format_name, path in report_paths.items():
        logger.info(f"  {format_name}: {path}")

    # Save to database
    db_path = output_dir / "benchmarks.db"
    with ResultsStorage(db_path) as storage:
        run_id = storage.save_benchmark_run(
            results=results,
            dataset_name=dataset_name,
            run_name=args.run_name,
            metadata={
                "quick": True,
                "parallel": args.parallel,
                "providers": providers_to_test
            }
        )
        logger.info(f"Results saved to database (run_id={run_id})")


def run_full_benchmark(args):
    """Run a full benchmark with all providers and datasets."""
    logger.info("Starting full benchmark...")

    # Initialize components
    project_root = Path(__file__).parent.parent
    dataset_root = project_root / "benchmarks" / "datasets"
    output_dir = project_root / "benchmarks" / "results"

    dataset_manager = DatasetManager(dataset_root)
    resource_monitor = ResourceMonitor(interval_seconds=1.0)
    cost_estimator = CostEstimator()
    benchmark_runner = BenchmarkRunner(
        dataset_manager=dataset_manager,
        output_dir=output_dir,
        resource_monitor=resource_monitor,
        cost_estimator=cost_estimator
    )

    # Load dataset
    dataset_name = args.dataset
    if not dataset_manager.get_dataset(dataset_name):
        logger.error(f"Dataset '{dataset_name}' not found")
        return

    # Register all providers (or specified ones)
    providers_to_test = args.providers or list(AVAILABLE_PROVIDERS.keys())

    providers = []
    for provider_name in providers_to_test:
        if provider_name in AVAILABLE_PROVIDERS:
            try:
                provider = AVAILABLE_PROVIDERS[provider_name]()
                providers.append(provider)
                logger.info(f"Registered provider: {provider}")
            except Exception as e:
                logger.error(f"Failed to create provider '{provider_name}': {e}")

    if not providers:
        logger.error("No providers available to test")
        return

    benchmark_runner.register_providers(providers)

    # Run benchmark
    logger.info(f"Running benchmark on {len(providers)} provider(s)...")
    results = benchmark_runner.run_benchmark(
        dataset_name=dataset_name,
        parallel=args.parallel,
        max_workers=args.max_workers
    )

    # Print summary
    benchmark_runner.print_summary(results)

    # Generate reports
    report_generator = ReportGenerator(output_dir / "reports")
    report_paths = report_generator.generate_all_reports(results, dataset_name)

    logger.info("Reports generated:")
    for format_name, path in report_paths.items():
        logger.info(f"  {format_name}: {path}")

    # Save to database
    db_path = output_dir / "benchmarks.db"
    with ResultsStorage(db_path) as storage:
        run_id = storage.save_benchmark_run(
            results=results,
            dataset_name=dataset_name,
            run_name=args.run_name,
            metadata={
                "full": True,
                "parallel": args.parallel,
                "providers": providers_to_test
            }
        )
        logger.info(f"Results saved to database (run_id={run_id})")

    logger.info("Full benchmark completed!")


def list_providers(args):
    """List all available providers."""
    print("\nAvailable STT Providers:")
    print("=" * 60)

    local_providers = []
    cloud_providers = []

    for name, factory in AVAILABLE_PROVIDERS.items():
        try:
            provider = factory()
            if provider.provider_type.value == "local":
                local_providers.append((name, provider))
            else:
                cloud_providers.append((name, provider))
        except Exception as e:
            logger.warning(f"Failed to create provider '{name}': {e}")

    print("\nLocal Models:")
    for name, provider in sorted(local_providers, key=lambda x: x[0]):
        print(f"  - {name:<20} ({provider.provider_name} {provider.model_name})")

    print("\nCloud APIs:")
    for name, provider in sorted(cloud_providers, key=lambda x: x[0]):
        cost = provider.get_cost_per_minute() * 60
        print(f"  - {name:<20} ({provider.provider_name} {provider.model_name}) - ${cost:.2f}/hr")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Run STT model benchmarks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick test with Whisper only
  python scripts/run_benchmarks.py --quick

  # Full benchmark with all providers
  python scripts/run_benchmarks.py --full --dataset standard_test

  # Benchmark specific providers
  python scripts/run_benchmarks.py --dataset test --providers whisper openai deepgram

  # Parallel execution
  python scripts/run_benchmarks.py --full --parallel --max-workers 3

  # List available providers
  python scripts/run_benchmarks.py --list
        """
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick benchmark (5 samples, fast providers)"
    )

    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full benchmark (all samples, all providers)"
    )

    parser.add_argument(
        "--dataset",
        type=str,
        default="quick_test",
        help="Dataset name to use"
    )

    parser.add_argument(
        "--providers",
        nargs="+",
        help="Specific providers to test (space-separated)"
    )

    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run providers in parallel"
    )

    parser.add_argument(
        "--max-workers",
        type=int,
        default=3,
        help="Maximum parallel workers (default: 3)"
    )

    parser.add_argument(
        "--run-name",
        type=str,
        help="Custom name for this benchmark run"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available providers"
    )

    args = parser.parse_args()

    # Handle commands
    if args.list:
        list_providers(args)
    elif args.quick:
        run_quick_benchmark(args)
    elif args.full:
        run_full_benchmark(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
