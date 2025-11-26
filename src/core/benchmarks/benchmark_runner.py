"""
Benchmark Runner for STT model comparison.

Orchestrates benchmarking across multiple providers, collecting metrics,
and generating comparison reports.
"""

import logging
import time
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .providers.base_provider import STTProvider, TranscriptionResult
from .dataset_manager import DatasetManager, AudioSample
from .metrics import BenchmarkMetrics, calculate_wer, calculate_cer, calculate_rtfx
from .resource_monitor import ResourceMonitor
from .cost_estimator import CostEstimator

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """
    Orchestrate STT benchmarking across multiple providers.

    Features:
    - Run benchmarks on multiple providers in parallel
    - Collect comprehensive metrics
    - Track resource usage
    - Generate comparison reports
    - Save results for later analysis
    """

    def __init__(
        self,
        dataset_manager: DatasetManager,
        output_dir: Path,
        resource_monitor: Optional[ResourceMonitor] = None,
        cost_estimator: Optional[CostEstimator] = None
    ):
        """
        Initialize BenchmarkRunner.

        Args:
            dataset_manager: DatasetManager instance
            output_dir: Directory for saving results
            resource_monitor: Optional ResourceMonitor instance
            cost_estimator: Optional CostEstimator instance
        """
        self.dataset_manager = dataset_manager
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.resource_monitor = resource_monitor or ResourceMonitor()
        self.cost_estimator = cost_estimator or CostEstimator()

        self.providers: List[STTProvider] = []
        self.results: Dict[str, BenchmarkMetrics] = {}

        logger.info(f"BenchmarkRunner initialized (output: {self.output_dir})")

    def register_provider(self, provider: STTProvider) -> None:
        """
        Register a provider for benchmarking.

        Args:
            provider: STTProvider instance
        """
        self.providers.append(provider)
        logger.info(f"Registered provider: {provider}")

    def register_providers(self, providers: List[STTProvider]) -> None:
        """
        Register multiple providers.

        Args:
            providers: List of STTProvider instances
        """
        for provider in providers:
            self.register_provider(provider)

    def benchmark_provider(
        self,
        provider: STTProvider,
        samples: List[AudioSample],
        language: Optional[str] = None
    ) -> BenchmarkMetrics:
        """
        Benchmark a single provider on a dataset.

        Args:
            provider: STTProvider to benchmark
            samples: List of AudioSample to process
            language: Optional language hint

        Returns:
            BenchmarkMetrics with results
        """
        logger.info(f"Benchmarking {provider} on {len(samples)} samples...")

        # Initialize provider
        try:
            provider.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize {provider}: {e}")
            return BenchmarkMetrics(
                provider_name=provider.provider_name,
                model_name=provider.model_name,
                provider_type=provider.provider_type.value
            )

        # Create metrics object
        metrics = BenchmarkMetrics(
            provider_name=provider.provider_name,
            model_name=provider.model_name,
            provider_type=provider.provider_type.value,
            hardware=self._get_hardware_info()
        )

        # Start resource monitoring
        self.resource_monitor.start_monitoring()

        total_audio_duration = 0.0
        successful_transcriptions = 0

        # Process each sample
        for i, sample in enumerate(samples):
            logger.info(
                f"[{provider}] Processing sample {i+1}/{len(samples)}: "
                f"{sample.audio_path.name} ({sample.duration_seconds:.1f}s)"
            )

            try:
                # Transcribe
                start_time = time.time()
                result = provider.transcribe(
                    sample.audio_path,
                    language=language or sample.language
                )
                processing_time = time.time() - start_time

                # Update result timing if not set
                if result.processing_time_ms == 0:
                    result.processing_time_ms = processing_time * 1000
                if result.audio_duration_ms == 0:
                    result.audio_duration_ms = sample.duration_seconds * 1000

                # Calculate WER and CER
                wer = calculate_wer(sample.transcription, result.text)
                cer = calculate_cer(sample.transcription, result.text)

                # Collect metrics
                metrics.wer_per_sample.append(wer)
                metrics.cer_per_sample.append(cer)
                metrics.latencies_ms.append(result.processing_time_ms)

                if result.confidence:
                    if metrics.avg_confidence == 0:
                        metrics.avg_confidence = result.confidence
                    else:
                        metrics.avg_confidence = (
                            metrics.avg_confidence * successful_transcriptions +
                            result.confidence
                        ) / (successful_transcriptions + 1)

                total_audio_duration += sample.duration_seconds
                successful_transcriptions += 1

                logger.debug(
                    f"Sample {i+1}: WER={wer:.3f}, CER={cer:.3f}, "
                    f"RTFx={result.rtfx:.3f}, Latency={result.processing_time_ms:.0f}ms"
                )

            except Exception as e:
                logger.error(f"Failed to transcribe sample {i+1}: {e}")
                # Add placeholder metrics for failed sample
                metrics.wer_per_sample.append(1.0)  # 100% error
                metrics.cer_per_sample.append(1.0)

        # Stop resource monitoring
        resource_stats = self.resource_monitor.stop_monitoring()

        # Update metrics with resource usage
        metrics.gpu_memory_mb = resource_stats.max_gpu_memory_mb
        metrics.cpu_percent = resource_stats.avg_cpu_percent
        metrics.ram_mb = resource_stats.avg_ram_mb

        # Calculate derived metrics
        metrics.audio_duration_seconds = total_audio_duration
        metrics.sample_count = len(samples)

        if metrics.latencies_ms:
            total_processing_time = sum(metrics.latencies_ms) / 1000  # Convert to seconds
            metrics.rtfx = calculate_rtfx(total_audio_duration, total_processing_time)

        metrics.calculate_derived_metrics()

        # Get cost information
        cost_breakdown = self.cost_estimator.get_cost_breakdown(
            provider.provider_name,
            provider.model_name
        )
        if cost_breakdown:
            metrics.cost_per_minute = cost_breakdown.cost_per_minute
            metrics.cost_per_hour = cost_breakdown.cost_per_hour

        logger.info(
            f"Completed benchmarking {provider}: "
            f"WER={metrics.wer:.3f}, RTFx={metrics.rtfx:.3f}, "
            f"Score={metrics.get_score():.1f}/10"
        )

        # Cleanup provider
        try:
            provider.cleanup()
        except Exception as e:
            logger.warning(f"Failed to cleanup {provider}: {e}")

        return metrics

    def run_benchmark(
        self,
        dataset_name: str,
        providers: Optional[List[STTProvider]] = None,
        language: Optional[str] = None,
        parallel: bool = False,
        max_workers: int = 3
    ) -> Dict[str, BenchmarkMetrics]:
        """
        Run benchmark on multiple providers.

        Args:
            dataset_name: Name of dataset to use
            providers: Optional list of providers. Uses all registered if None.
            language: Optional language hint
            parallel: Whether to run providers in parallel
            max_workers: Max parallel workers (if parallel=True)

        Returns:
            Dict mapping provider names to BenchmarkMetrics
        """
        # Load dataset
        samples = self.dataset_manager.get_dataset(dataset_name)
        if not samples:
            logger.error(f"Dataset '{dataset_name}' is empty or not loaded")
            return {}

        logger.info(f"Running benchmark on dataset '{dataset_name}' ({len(samples)} samples)")

        # Use registered providers if not specified
        if providers is None:
            providers = self.providers

        if not providers:
            logger.error("No providers registered")
            return {}

        results = {}

        if parallel:
            # Run providers in parallel
            logger.info(f"Running {len(providers)} providers in parallel (max_workers={max_workers})")

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_provider = {
                    executor.submit(self.benchmark_provider, provider, samples, language): provider
                    for provider in providers
                }

                for future in as_completed(future_to_provider):
                    provider = future_to_provider[future]
                    try:
                        metrics = future.result()
                        key = f"{provider.provider_name}_{provider.model_name}"
                        results[key] = metrics
                        self.results[key] = metrics
                    except Exception as e:
                        logger.error(f"Provider {provider} failed: {e}")
        else:
            # Run providers sequentially
            logger.info(f"Running {len(providers)} providers sequentially")

            for provider in providers:
                try:
                    metrics = self.benchmark_provider(provider, samples, language)
                    key = f"{provider.provider_name}_{provider.model_name}"
                    results[key] = metrics
                    self.results[key] = metrics
                except Exception as e:
                    logger.error(f"Provider {provider} failed: {e}")

        logger.info(f"Benchmark completed: {len(results)} providers tested")

        # Save results
        self.save_results(results, dataset_name)

        return results

    def save_results(
        self,
        results: Dict[str, BenchmarkMetrics],
        dataset_name: str
    ) -> Path:
        """
        Save benchmark results to JSON file.

        Args:
            results: Dict of BenchmarkMetrics
            dataset_name: Name of dataset

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_{dataset_name}_{timestamp}.json"
        output_path = self.output_dir / filename

        data = {
            "dataset_name": dataset_name,
            "timestamp": timestamp,
            "provider_count": len(results),
            "results": {
                key: metrics.to_dict()
                for key, metrics in results.items()
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved benchmark results to {output_path}")

        return output_path

    def load_results(self, results_path: Path) -> Dict[str, BenchmarkMetrics]:
        """
        Load benchmark results from JSON file.

        Args:
            results_path: Path to results JSON

        Returns:
            Dict of BenchmarkMetrics
        """
        with open(results_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        results = {}
        for key, metrics_dict in data.get("results", {}).items():
            # Reconstruct BenchmarkMetrics from dict
            metrics = BenchmarkMetrics(
                provider_name=metrics_dict["provider_name"],
                model_name=metrics_dict["model_name"],
                **{k: v for k, v in metrics_dict.items()
                   if k not in ["provider_name", "model_name"]}
            )
            results[key] = metrics

        logger.info(f"Loaded {len(results)} results from {results_path}")

        return results

    def get_rankings(
        self,
        results: Optional[Dict[str, BenchmarkMetrics]] = None,
        metric: str = "score"
    ) -> List[tuple]:
        """
        Get provider rankings by a specific metric.

        Args:
            results: Optional results dict. Uses self.results if None.
            metric: Metric to rank by ("score", "wer", "rtfx", "cost_per_hour")

        Returns:
            List of (provider_key, metrics, metric_value) tuples, sorted
        """
        if results is None:
            results = self.results

        if not results:
            return []

        rankings = []

        for key, metrics in results.items():
            if metric == "score":
                value = metrics.get_score()
                reverse = True  # Higher score is better
            elif metric == "wer":
                value = metrics.wer
                reverse = False  # Lower WER is better
            elif metric == "cer":
                value = metrics.cer
                reverse = False
            elif metric == "rtfx":
                value = metrics.rtfx
                reverse = False  # Lower RTFx is better
            elif metric == "cost_per_hour":
                value = metrics.cost_per_hour
                reverse = False  # Lower cost is better
            elif metric == "latency_p50_ms":
                value = metrics.latency_p50_ms
                reverse = False
            else:
                logger.warning(f"Unknown metric: {metric}")
                continue

            rankings.append((key, metrics, value))

        # Sort
        rankings.sort(key=lambda x: x[2], reverse=reverse)

        return rankings

    def _get_hardware_info(self) -> str:
        """Get hardware information string."""
        gpu_info = self.resource_monitor.get_gpu_info()

        if gpu_info.get("available"):
            return gpu_info.get("name", "Unknown GPU")
        else:
            return "CPU"

    def print_summary(self, results: Optional[Dict[str, BenchmarkMetrics]] = None) -> None:
        """
        Print a summary of benchmark results.

        Args:
            results: Optional results dict. Uses self.results if None.
        """
        if results is None:
            results = self.results

        if not results:
            logger.warning("No results to display")
            return

        print("\n" + "="*80)
        print("BENCHMARK SUMMARY")
        print("="*80)

        # Overall rankings by score
        rankings = self.get_rankings(results, metric="score")

        print(f"\nOverall Rankings (by Score):")
        print(f"{'Rank':<6} {'Provider':<30} {'Score':<8} {'WER':<8} {'RTFx':<8} {'Cost/hr':<10}")
        print("-" * 80)

        for rank, (key, metrics, score) in enumerate(rankings, 1):
            provider_name = f"{metrics.provider_name} {metrics.model_name}"
            print(
                f"{rank:<6} {provider_name:<30} {score:<8.1f} "
                f"{metrics.wer*100:<7.1f}% {metrics.rtfx:<8.3f} "
                f"${metrics.cost_per_hour:<9.2f}"
            )

        # Accuracy rankings
        print(f"\nAccuracy Rankings (by WER):")
        accuracy_rankings = self.get_rankings(results, metric="wer")
        for rank, (key, metrics, wer) in enumerate(accuracy_rankings[:5], 1):
            provider_name = f"{metrics.provider_name} {metrics.model_name}"
            print(f"  {rank}. {provider_name}: {wer*100:.2f}% WER")

        # Speed rankings
        print(f"\nSpeed Rankings (by RTFx):")
        speed_rankings = self.get_rankings(results, metric="rtfx")
        for rank, (key, metrics, rtfx) in enumerate(speed_rankings[:5], 1):
            provider_name = f"{metrics.provider_name} {metrics.model_name}"
            print(f"  {rank}. {provider_name}: {rtfx:.3f}x real-time")

        # Cost rankings
        print(f"\nCost Rankings (per hour):")
        cost_rankings = self.get_rankings(results, metric="cost_per_hour")
        for rank, (key, metrics, cost) in enumerate(cost_rankings[:5], 1):
            provider_name = f"{metrics.provider_name} {metrics.model_name}"
            if cost == 0:
                print(f"  {rank}. {provider_name}: FREE")
            else:
                print(f"  {rank}. {provider_name}: ${cost:.2f}/hour")

        print("="*80 + "\n")
