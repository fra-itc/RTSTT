"""
Report generator for STT benchmarking.

Generates comprehensive comparison reports in multiple formats:
- HTML with interactive charts
- Markdown for documentation
- CSV for data analysis
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .metrics import BenchmarkMetrics

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generate benchmark comparison reports.

    Features:
    - HTML reports with charts
    - Markdown reports
    - CSV exports
    - Comparison tables
    - Visualizations
    """

    def __init__(self, output_dir: Path):
        """
        Initialize ReportGenerator.

        Args:
            output_dir: Directory for saving reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"ReportGenerator initialized: {self.output_dir}")

    def generate_markdown_report(
        self,
        results: Dict[str, BenchmarkMetrics],
        dataset_name: str,
        output_filename: Optional[str] = None
    ) -> Path:
        """
        Generate Markdown report.

        Args:
            results: Dict of BenchmarkMetrics
            dataset_name: Dataset name
            output_filename: Optional output filename

        Returns:
            Path to generated report
        """
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"benchmark_report_{timestamp}.md"

        output_path = self.output_dir / output_filename

        # Sort by overall score
        sorted_results = sorted(
            results.items(),
            key=lambda x: x[1].get_score(),
            reverse=True
        )

        # Generate report
        lines = [
            "# STT Model Benchmark Results",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Dataset:** {dataset_name}",
            f"**Providers Tested:** {len(results)}",
            ""
        ]

        # Get hardware info from first result
        if sorted_results:
            hardware = sorted_results[0][1].hardware
            lines.append(f"**Hardware:** {hardware}")
            lines.append("")

        # Summary table
        lines.extend([
            "## Summary",
            "",
            "| Rank | Provider | Model | WER | Latency | Cost/hr | RTFx | Score |",
            "|------|----------|-------|-----|---------|---------|------|-------|"
        ])

        for rank, (key, metrics) in enumerate(sorted_results, 1):
            latency = f"{metrics.latency_p50_ms:.0f}ms"
            cost = f"${metrics.cost_per_hour:.2f}" if metrics.cost_per_hour > 0 else "FREE"

            lines.append(
                f"| {rank} | {metrics.provider_name} | {metrics.model_name} | "
                f"{metrics.wer*100:.1f}% | {latency} | {cost} | "
                f"{metrics.rtfx:.2f} | {metrics.get_score():.1f} |"
            )

        lines.append("")

        # Detailed analysis
        lines.extend([
            "## Detailed Analysis",
            ""
        ])

        # Accuracy rankings
        lines.extend([
            "### Accuracy Rankings (by WER)",
            ""
        ])

        accuracy_sorted = sorted(results.items(), key=lambda x: x[1].wer)
        for rank, (key, metrics) in enumerate(accuracy_sorted[:10], 1):
            lines.append(
                f"{rank}. **{metrics.provider_name} {metrics.model_name}**: "
                f"{metrics.wer*100:.2f}% WER, {metrics.cer*100:.2f}% CER"
            )

        lines.append("")

        # Speed rankings
        lines.extend([
            "### Speed Rankings (by RTFx)",
            ""
        ])

        speed_sorted = sorted(results.items(), key=lambda x: x[1].rtfx)
        for rank, (key, metrics) in enumerate(speed_sorted[:10], 1):
            throughput = f"{metrics.throughput_hours_per_hour:.1f}x" if metrics.throughput_hours_per_hour > 0 else "N/A"
            lines.append(
                f"{rank}. **{metrics.provider_name} {metrics.model_name}**: "
                f"{metrics.rtfx:.3f}x real-time (throughput: {throughput})"
            )

        lines.append("")

        # Cost rankings
        lines.extend([
            "### Cost Rankings (per hour)",
            ""
        ])

        cost_sorted = sorted(results.items(), key=lambda x: x[1].cost_per_hour)
        for rank, (key, metrics) in enumerate(cost_sorted[:10], 1):
            if metrics.cost_per_hour == 0:
                cost_str = "FREE (local model)"
            else:
                cost_str = f"${metrics.cost_per_hour:.2f}/hour (${metrics.cost_per_minute:.4f}/min)"

            lines.append(
                f"{rank}. **{metrics.provider_name} {metrics.model_name}**: {cost_str}"
            )

        lines.append("")

        # Recommendations
        lines.extend([
            "## Recommendations",
            ""
        ])

        # Best for real-time
        realtime_best = sorted(
            [m for m in results.values() if m.latency_p50_ms > 0],
            key=lambda x: x.latency_p50_ms
        )
        if realtime_best:
            best = realtime_best[0]
            lines.append(
                f"**Best for Real-time:** {best.provider_name} {best.model_name} "
                f"({best.latency_p50_ms:.0f}ms latency)"
            )

        # Best for batch
        batch_best = sorted(
            results.values(),
            key=lambda x: x.rtfx if x.rtfx > 0 else float('inf')
        )
        if batch_best:
            best = batch_best[0]
            lines.append(
                f"**Best for Batch:** {best.provider_name} {best.model_name} "
                f"({best.rtfx:.3f}x RTFx)"
            )

        # Best for budget
        free_models = [m for m in results.values() if m.cost_per_hour == 0]
        if free_models:
            best = sorted(free_models, key=lambda x: x.wer)[0]
            lines.append(
                f"**Best for Budget:** {best.provider_name} {best.model_name} "
                f"(FREE, {best.wer*100:.1f}% WER)"
            )

        # Best overall
        if sorted_results:
            best = sorted_results[0][1]
            lines.append(
                f"**Best Overall:** {best.provider_name} {best.model_name} "
                f"(Score: {best.get_score():.1f}/10)"
            )

        lines.append("")

        # Provider type breakdown
        lines.extend([
            "## Provider Type Breakdown",
            ""
        ])

        local_providers = [m for m in results.values() if m.provider_type == "local"]
        cloud_providers = [m for m in results.values() if m.provider_type == "cloud"]

        lines.append(f"**Local Models:** {len(local_providers)}")
        lines.append(f"**Cloud APIs:** {len(cloud_providers)}")
        lines.append("")

        if local_providers:
            avg_wer_local = sum(m.wer for m in local_providers) / len(local_providers)
            lines.append(f"Local models average WER: {avg_wer_local*100:.2f}%")

        if cloud_providers:
            avg_wer_cloud = sum(m.wer for m in cloud_providers) / len(cloud_providers)
            lines.append(f"Cloud APIs average WER: {avg_wer_cloud*100:.2f}%")

        # Write report
        content = "\n".join(lines)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Generated Markdown report: {output_path}")

        return output_path

    def generate_csv_export(
        self,
        results: Dict[str, BenchmarkMetrics],
        output_filename: Optional[str] = None
    ) -> Path:
        """
        Export results to CSV.

        Args:
            results: Dict of BenchmarkMetrics
            output_filename: Optional output filename

        Returns:
            Path to CSV file
        """
        import csv

        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"benchmark_results_{timestamp}.csv"

        output_path = self.output_dir / output_filename

        # Define CSV columns
        columns = [
            "provider_name",
            "model_name",
            "provider_type",
            "wer",
            "cer",
            "avg_confidence",
            "rtfx",
            "latency_p50_ms",
            "latency_p95_ms",
            "latency_p99_ms",
            "throughput_hours_per_hour",
            "gpu_memory_mb",
            "cpu_percent",
            "ram_mb",
            "cost_per_minute",
            "cost_per_hour",
            "audio_duration_seconds",
            "sample_count",
            "score"
        ]

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()

            for key, metrics in results.items():
                row = {
                    "provider_name": metrics.provider_name,
                    "model_name": metrics.model_name,
                    "provider_type": metrics.provider_type,
                    "wer": metrics.wer,
                    "cer": metrics.cer,
                    "avg_confidence": metrics.avg_confidence,
                    "rtfx": metrics.rtfx,
                    "latency_p50_ms": metrics.latency_p50_ms,
                    "latency_p95_ms": metrics.latency_p95_ms,
                    "latency_p99_ms": metrics.latency_p99_ms,
                    "throughput_hours_per_hour": metrics.throughput_hours_per_hour,
                    "gpu_memory_mb": metrics.gpu_memory_mb,
                    "cpu_percent": metrics.cpu_percent,
                    "ram_mb": metrics.ram_mb,
                    "cost_per_minute": metrics.cost_per_minute,
                    "cost_per_hour": metrics.cost_per_hour,
                    "audio_duration_seconds": metrics.audio_duration_seconds,
                    "sample_count": metrics.sample_count,
                    "score": metrics.get_score()
                }
                writer.writerow(row)

        logger.info(f"Generated CSV export: {output_path}")

        return output_path

    def generate_json_export(
        self,
        results: Dict[str, BenchmarkMetrics],
        dataset_name: str,
        output_filename: Optional[str] = None
    ) -> Path:
        """
        Export results to JSON.

        Args:
            results: Dict of BenchmarkMetrics
            dataset_name: Dataset name
            output_filename: Optional output filename

        Returns:
            Path to JSON file
        """
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"benchmark_results_{timestamp}.json"

        output_path = self.output_dir / output_filename

        data = {
            "dataset_name": dataset_name,
            "timestamp": datetime.now().isoformat(),
            "provider_count": len(results),
            "results": {}
        }

        for key, metrics in results.items():
            data["results"][key] = metrics.to_dict()
            data["results"][key]["score"] = metrics.get_score()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Generated JSON export: {output_path}")

        return output_path

    def generate_html_report(
        self,
        results: Dict[str, BenchmarkMetrics],
        dataset_name: str,
        output_filename: Optional[str] = None
    ) -> Path:
        """
        Generate HTML report with charts.

        Args:
            results: Dict of BenchmarkMetrics
            dataset_name: Dataset name
            output_filename: Optional output filename

        Returns:
            Path to HTML file
        """
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"benchmark_report_{timestamp}.html"

        output_path = self.output_dir / output_filename

        # Prepare data for charts
        sorted_results = sorted(
            results.items(),
            key=lambda x: x[1].get_score(),
            reverse=True
        )

        provider_labels = [f"{m.provider_name} {m.model_name}" for _, m in sorted_results]
        wer_data = [m.wer * 100 for _, m in sorted_results]
        rtfx_data = [m.rtfx for _, m in sorted_results]
        cost_data = [m.cost_per_hour for _, m in sorted_results]
        score_data = [m.get_score() for _, m in sorted_results]
        latency_data = [m.latency_p50_ms for _, m in sorted_results]

        # Generate HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>STT Benchmark Report - {dataset_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1, h2 {{
            color: #333;
        }}
        .header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #4CAF50;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .rank-1 {{
            background: #fff9c4;
        }}
        .rank-2 {{
            background: #f0f4c3;
        }}
        .rank-3 {{
            background: #e6ee9c;
        }}
        canvas {{
            max-height: 400px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>STT Model Benchmark Results</h1>
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Dataset:</strong> {dataset_name}</p>
        <p><strong>Providers Tested:</strong> {len(results)}</p>
    </div>

    <div class="chart-container">
        <h2>Overall Score Comparison</h2>
        <canvas id="scoreChart"></canvas>
    </div>

    <div class="chart-container">
        <h2>Word Error Rate (WER)</h2>
        <canvas id="werChart"></canvas>
    </div>

    <div class="chart-container">
        <h2>Real-Time Factor (RTFx)</h2>
        <canvas id="rtfxChart"></canvas>
    </div>

    <div class="chart-container">
        <h2>Cost per Hour</h2>
        <canvas id="costChart"></canvas>
    </div>

    <div class="chart-container">
        <h2>Latency Comparison (p50)</h2>
        <canvas id="latencyChart"></canvas>
    </div>

    <div class="chart-container">
        <h2>Detailed Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Provider</th>
                    <th>Model</th>
                    <th>WER</th>
                    <th>Latency</th>
                    <th>RTFx</th>
                    <th>Cost/hr</th>
                    <th>Score</th>
                </tr>
            </thead>
            <tbody>
"""

        for rank, (key, metrics) in enumerate(sorted_results, 1):
            row_class = f"rank-{rank}" if rank <= 3 else ""
            cost_str = f"${metrics.cost_per_hour:.2f}" if metrics.cost_per_hour > 0 else "FREE"

            html += f"""
                <tr class="{row_class}">
                    <td>{rank}</td>
                    <td>{metrics.provider_name}</td>
                    <td>{metrics.model_name}</td>
                    <td>{metrics.wer*100:.2f}%</td>
                    <td>{metrics.latency_p50_ms:.0f}ms</td>
                    <td>{metrics.rtfx:.3f}</td>
                    <td>{cost_str}</td>
                    <td>{metrics.get_score():.1f}/10</td>
                </tr>
"""

        html += """
            </tbody>
        </table>
    </div>

    <script>
        const labels = """ + json.dumps(provider_labels) + """;
        const werData = """ + json.dumps(wer_data) + """;
        const rtfxData = """ + json.dumps(rtfx_data) + """;
        const costData = """ + json.dumps(cost_data) + """;
        const scoreData = """ + json.dumps(score_data) + """;
        const latencyData = """ + json.dumps(latency_data) + """;

        // Score chart
        new Chart(document.getElementById('scoreChart'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Overall Score (0-10)',
                    data: scoreData,
                    backgroundColor: 'rgba(76, 175, 80, 0.6)',
                    borderColor: 'rgba(76, 175, 80, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 10
                    }
                }
            }
        });

        // WER chart
        new Chart(document.getElementById('werChart'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Word Error Rate (%)',
                    data: werData,
                    backgroundColor: 'rgba(244, 67, 54, 0.6)',
                    borderColor: 'rgba(244, 67, 54, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        // RTFx chart
        new Chart(document.getElementById('rtfxChart'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Real-Time Factor (lower is better)',
                    data: rtfxData,
                    backgroundColor: 'rgba(33, 150, 243, 0.6)',
                    borderColor: 'rgba(33, 150, 243, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        // Cost chart
        new Chart(document.getElementById('costChart'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Cost per Hour (USD)',
                    data: costData,
                    backgroundColor: 'rgba(255, 193, 7, 0.6)',
                    borderColor: 'rgba(255, 193, 7, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        // Latency chart
        new Chart(document.getElementById('latencyChart'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Median Latency (ms)',
                    data: latencyData,
                    backgroundColor: 'rgba(156, 39, 176, 0.6)',
                    borderColor: 'rgba(156, 39, 176, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    </script>
</body>
</html>
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"Generated HTML report: {output_path}")

        return output_path

    def generate_all_reports(
        self,
        results: Dict[str, BenchmarkMetrics],
        dataset_name: str
    ) -> Dict[str, Path]:
        """
        Generate all report formats.

        Args:
            results: Dict of BenchmarkMetrics
            dataset_name: Dataset name

        Returns:
            Dict mapping format names to file paths
        """
        paths = {}

        paths["markdown"] = self.generate_markdown_report(results, dataset_name)
        paths["csv"] = self.generate_csv_export(results)
        paths["json"] = self.generate_json_export(results, dataset_name)
        paths["html"] = self.generate_html_report(results, dataset_name)

        logger.info(f"Generated all report formats: {list(paths.keys())}")

        return paths
