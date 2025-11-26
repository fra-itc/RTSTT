"""
Results storage for STT benchmarking.

Stores benchmark results in SQLite database for historical tracking and querying.
"""

import logging
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from .metrics import BenchmarkMetrics

logger = logging.getLogger(__name__)


class ResultsStorage:
    """
    Store and query benchmark results using SQLite.

    Features:
    - Persistent storage of benchmark runs
    - Historical tracking
    - Query interface
    - Export to JSON/CSV
    """

    def __init__(self, db_path: Path):
        """
        Initialize ResultsStorage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Enable column access by name

        self._create_tables()

        logger.info(f"ResultsStorage initialized: {self.db_path}")

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Benchmark runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS benchmark_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_name TEXT,
                dataset_name TEXT,
                timestamp TEXT,
                provider_count INTEGER,
                metadata TEXT
            )
        """)

        # Benchmark results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS benchmark_results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER,
                provider_name TEXT,
                model_name TEXT,
                provider_type TEXT,

                wer REAL,
                cer REAL,
                avg_confidence REAL,

                rtfx REAL,
                latency_p50_ms REAL,
                latency_p95_ms REAL,
                latency_p99_ms REAL,
                throughput_hours_per_hour REAL,

                gpu_memory_mb REAL,
                cpu_percent REAL,
                ram_mb REAL,

                cost_per_minute REAL,
                cost_per_hour REAL,

                audio_duration_seconds REAL,
                test_timestamp TEXT,
                hardware TEXT,
                sample_count INTEGER,

                score REAL,

                FOREIGN KEY (run_id) REFERENCES benchmark_runs(run_id)
            )
        """)

        # Create indices
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_provider_name
            ON benchmark_results(provider_name)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON benchmark_results(test_timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_run_id
            ON benchmark_results(run_id)
        """)

        self.conn.commit()

    def save_benchmark_run(
        self,
        results: Dict[str, BenchmarkMetrics],
        dataset_name: str,
        run_name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Save a complete benchmark run.

        Args:
            results: Dict of BenchmarkMetrics
            dataset_name: Name of dataset used
            run_name: Optional name for this run
            metadata: Optional metadata dict

        Returns:
            int: run_id of saved run
        """
        cursor = self.conn.cursor()

        # Generate run name if not provided
        if run_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_name = f"run_{timestamp}"

        # Insert benchmark run
        cursor.execute("""
            INSERT INTO benchmark_runs (run_name, dataset_name, timestamp, provider_count, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            run_name,
            dataset_name,
            datetime.now().isoformat(),
            len(results),
            json.dumps(metadata or {})
        ))

        run_id = cursor.lastrowid

        # Insert individual results
        for key, metrics in results.items():
            cursor.execute("""
                INSERT INTO benchmark_results (
                    run_id, provider_name, model_name, provider_type,
                    wer, cer, avg_confidence,
                    rtfx, latency_p50_ms, latency_p95_ms, latency_p99_ms, throughput_hours_per_hour,
                    gpu_memory_mb, cpu_percent, ram_mb,
                    cost_per_minute, cost_per_hour,
                    audio_duration_seconds, test_timestamp, hardware, sample_count, score
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                metrics.provider_name,
                metrics.model_name,
                metrics.provider_type,
                metrics.wer,
                metrics.cer,
                metrics.avg_confidence,
                metrics.rtfx,
                metrics.latency_p50_ms,
                metrics.latency_p95_ms,
                metrics.latency_p99_ms,
                metrics.throughput_hours_per_hour,
                metrics.gpu_memory_mb,
                metrics.cpu_percent,
                metrics.ram_mb,
                metrics.cost_per_minute,
                metrics.cost_per_hour,
                metrics.audio_duration_seconds,
                metrics.test_timestamp.isoformat(),
                metrics.hardware,
                metrics.sample_count,
                metrics.get_score()
            ))

        self.conn.commit()

        logger.info(
            f"Saved benchmark run '{run_name}' (run_id={run_id}) "
            f"with {len(results)} results"
        )

        return run_id

    def get_run(self, run_id: int) -> Dict:
        """
        Get benchmark run metadata.

        Args:
            run_id: Run ID

        Returns:
            Dict with run metadata
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM benchmark_runs WHERE run_id = ?
        """, (run_id,))

        row = cursor.fetchone()

        if not row:
            return {}

        return {
            "run_id": row["run_id"],
            "run_name": row["run_name"],
            "dataset_name": row["dataset_name"],
            "timestamp": row["timestamp"],
            "provider_count": row["provider_count"],
            "metadata": json.loads(row["metadata"])
        }

    def get_run_results(self, run_id: int) -> List[Dict]:
        """
        Get all results for a specific run.

        Args:
            run_id: Run ID

        Returns:
            List of result dicts
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM benchmark_results WHERE run_id = ?
        """, (run_id,))

        rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append({
                "result_id": row["result_id"],
                "provider_name": row["provider_name"],
                "model_name": row["model_name"],
                "provider_type": row["provider_type"],
                "wer": row["wer"],
                "cer": row["cer"],
                "avg_confidence": row["avg_confidence"],
                "rtfx": row["rtfx"],
                "latency_p50_ms": row["latency_p50_ms"],
                "latency_p95_ms": row["latency_p95_ms"],
                "latency_p99_ms": row["latency_p99_ms"],
                "throughput_hours_per_hour": row["throughput_hours_per_hour"],
                "gpu_memory_mb": row["gpu_memory_mb"],
                "cpu_percent": row["cpu_percent"],
                "ram_mb": row["ram_mb"],
                "cost_per_minute": row["cost_per_minute"],
                "cost_per_hour": row["cost_per_hour"],
                "audio_duration_seconds": row["audio_duration_seconds"],
                "test_timestamp": row["test_timestamp"],
                "hardware": row["hardware"],
                "sample_count": row["sample_count"],
                "score": row["score"],
            })

        return results

    def list_runs(self, limit: int = 50) -> List[Dict]:
        """
        List recent benchmark runs.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of run metadata dicts
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM benchmark_runs
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()

        runs = []
        for row in rows:
            runs.append({
                "run_id": row["run_id"],
                "run_name": row["run_name"],
                "dataset_name": row["dataset_name"],
                "timestamp": row["timestamp"],
                "provider_count": row["provider_count"],
            })

        return runs

    def get_provider_history(
        self,
        provider_name: str,
        model_name: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get historical results for a specific provider.

        Args:
            provider_name: Provider name
            model_name: Model name
            limit: Maximum number of results

        Returns:
            List of result dicts ordered by timestamp
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM benchmark_results
            WHERE provider_name = ? AND model_name = ?
            ORDER BY test_timestamp DESC
            LIMIT ?
        """, (provider_name, model_name, limit))

        rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append({
                "test_timestamp": row["test_timestamp"],
                "wer": row["wer"],
                "cer": row["cer"],
                "rtfx": row["rtfx"],
                "latency_p50_ms": row["latency_p50_ms"],
                "cost_per_hour": row["cost_per_hour"],
                "score": row["score"],
                "hardware": row["hardware"],
                "sample_count": row["sample_count"],
            })

        return results

    def compare_runs(self, run_ids: List[int]) -> Dict[str, List]:
        """
        Compare multiple benchmark runs.

        Args:
            run_ids: List of run IDs to compare

        Returns:
            Dict with comparison data
        """
        comparison = {
            "runs": [],
            "providers": {}
        }

        for run_id in run_ids:
            run_info = self.get_run(run_id)
            if not run_info:
                continue

            comparison["runs"].append(run_info)

            results = self.get_run_results(run_id)

            for result in results:
                key = f"{result['provider_name']}_{result['model_name']}"

                if key not in comparison["providers"]:
                    comparison["providers"][key] = []

                comparison["providers"][key].append({
                    "run_id": run_id,
                    "run_name": run_info["run_name"],
                    **result
                })

        return comparison

    def export_to_csv(self, run_id: int, output_path: Path) -> None:
        """
        Export run results to CSV.

        Args:
            run_id: Run ID
            output_path: Path to output CSV file
        """
        import csv

        results = self.get_run_results(run_id)

        if not results:
            logger.warning(f"No results found for run_id={run_id}")
            return

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

        logger.info(f"Exported run {run_id} to {output_path}")

    def get_best_providers(
        self,
        metric: str = "score",
        limit: int = 10
    ) -> List[Dict]:
        """
        Get best performing providers across all runs.

        Args:
            metric: Metric to rank by
            limit: Number of results to return

        Returns:
            List of provider results
        """
        cursor = self.conn.cursor()

        # Determine sort order
        if metric in ["score", "throughput_hours_per_hour"]:
            order = "DESC"
        else:
            order = "ASC"

        cursor.execute(f"""
            SELECT
                provider_name,
                model_name,
                AVG({metric}) as avg_metric,
                COUNT(*) as run_count,
                MAX(test_timestamp) as latest_test
            FROM benchmark_results
            GROUP BY provider_name, model_name
            ORDER BY avg_metric {order}
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append({
                "provider_name": row["provider_name"],
                "model_name": row["model_name"],
                f"avg_{metric}": row["avg_metric"],
                "run_count": row["run_count"],
                "latest_test": row["latest_test"],
            })

        return results

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
