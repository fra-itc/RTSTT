"""
Resource monitoring for STT benchmarking.

Monitors:
- GPU usage (NVIDIA GPUs via nvidia-smi or pynvml)
- CPU usage (psutil)
- Memory usage (RAM)
- Disk I/O
"""

import logging
import time
import subprocess
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ResourceSnapshot:
    """Single snapshot of resource usage."""
    timestamp: float
    gpu_memory_used_mb: float = 0.0
    gpu_memory_total_mb: float = 0.0
    gpu_utilization_percent: float = 0.0
    cpu_percent: float = 0.0
    ram_used_mb: float = 0.0
    ram_total_mb: float = 0.0


@dataclass
class ResourceStats:
    """Aggregated resource statistics."""
    avg_gpu_memory_mb: float = 0.0
    max_gpu_memory_mb: float = 0.0
    avg_gpu_utilization: float = 0.0
    avg_cpu_percent: float = 0.0
    max_cpu_percent: float = 0.0
    avg_ram_mb: float = 0.0
    max_ram_mb: float = 0.0
    snapshots: List[ResourceSnapshot] = field(default_factory=list)


class ResourceMonitor:
    """
    Monitor system resources during benchmarking.

    Can run in background thread to continuously monitor resources.
    """

    def __init__(self, interval_seconds: float = 1.0):
        """
        Initialize ResourceMonitor.

        Args:
            interval_seconds: Sampling interval for monitoring
        """
        self.interval_seconds = interval_seconds
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.snapshots: List[ResourceSnapshot] = []

        # Try to import psutil
        try:
            import psutil
            self.psutil = psutil
        except ImportError:
            logger.warning("psutil not installed. CPU/RAM monitoring disabled.")
            self.psutil = None

        # Check for NVIDIA GPU
        self.has_nvidia_gpu = self._check_nvidia_gpu()

        logger.info(f"ResourceMonitor initialized (GPU: {self.has_nvidia_gpu})")

    def _check_nvidia_gpu(self) -> bool:
        """Check if NVIDIA GPU is available."""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def get_gpu_info(self) -> Dict[str, Any]:
        """
        Get GPU information.

        Returns:
            Dict with GPU details
        """
        if not self.has_nvidia_gpu:
            return {"available": False}

        try:
            result = subprocess.run(
                [
                    'nvidia-smi',
                    '--query-gpu=name,memory.total,driver_version,compute_cap',
                    '--format=csv,noheader'
                ],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                parts = result.stdout.strip().split(',')
                return {
                    "available": True,
                    "name": parts[0].strip(),
                    "memory_total_mb": float(parts[1].strip().split()[0]),
                    "driver_version": parts[2].strip(),
                    "compute_capability": parts[3].strip(),
                }
        except Exception as e:
            logger.warning(f"Failed to get GPU info: {e}")

        return {"available": False}

    def take_snapshot(self) -> ResourceSnapshot:
        """
        Take a single snapshot of current resource usage.

        Returns:
            ResourceSnapshot
        """
        snapshot = ResourceSnapshot(timestamp=time.time())

        # Get GPU usage
        if self.has_nvidia_gpu:
            try:
                result = subprocess.run(
                    [
                        'nvidia-smi',
                        '--query-gpu=memory.used,memory.total,utilization.gpu',
                        '--format=csv,noheader,nounits'
                    ],
                    capture_output=True,
                    text=True,
                    timeout=2
                )

                if result.returncode == 0:
                    parts = result.stdout.strip().split(',')
                    snapshot.gpu_memory_used_mb = float(parts[0].strip())
                    snapshot.gpu_memory_total_mb = float(parts[1].strip())
                    snapshot.gpu_utilization_percent = float(parts[2].strip())
            except Exception as e:
                logger.debug(f"Failed to get GPU snapshot: {e}")

        # Get CPU and RAM usage
        if self.psutil:
            try:
                snapshot.cpu_percent = self.psutil.cpu_percent(interval=0.1)

                mem = self.psutil.virtual_memory()
                snapshot.ram_used_mb = mem.used / (1024 * 1024)
                snapshot.ram_total_mb = mem.total / (1024 * 1024)
            except Exception as e:
                logger.debug(f"Failed to get CPU/RAM snapshot: {e}")

        return snapshot

    def start_monitoring(self) -> None:
        """Start continuous monitoring in background thread."""
        if self.is_monitoring:
            logger.warning("Monitoring already started")
            return

        self.is_monitoring = True
        self.snapshots = []

        def monitor_loop():
            while self.is_monitoring:
                snapshot = self.take_snapshot()
                self.snapshots.append(snapshot)
                time.sleep(self.interval_seconds)

        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()

        logger.info("Started resource monitoring")

    def stop_monitoring(self) -> ResourceStats:
        """
        Stop monitoring and return statistics.

        Returns:
            ResourceStats: Aggregated statistics
        """
        if not self.is_monitoring:
            logger.warning("Monitoring not started")
            return ResourceStats()

        self.is_monitoring = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)

        logger.info(f"Stopped resource monitoring ({len(self.snapshots)} snapshots)")

        return self.calculate_stats()

    def calculate_stats(self) -> ResourceStats:
        """
        Calculate statistics from snapshots.

        Returns:
            ResourceStats
        """
        if not self.snapshots:
            return ResourceStats()

        stats = ResourceStats()

        # Calculate averages and max values
        gpu_memory = [s.gpu_memory_used_mb for s in self.snapshots if s.gpu_memory_used_mb > 0]
        gpu_util = [s.gpu_utilization_percent for s in self.snapshots if s.gpu_utilization_percent > 0]
        cpu_util = [s.cpu_percent for s in self.snapshots if s.cpu_percent > 0]
        ram_used = [s.ram_used_mb for s in self.snapshots if s.ram_used_mb > 0]

        if gpu_memory:
            stats.avg_gpu_memory_mb = sum(gpu_memory) / len(gpu_memory)
            stats.max_gpu_memory_mb = max(gpu_memory)

        if gpu_util:
            stats.avg_gpu_utilization = sum(gpu_util) / len(gpu_util)

        if cpu_util:
            stats.avg_cpu_percent = sum(cpu_util) / len(cpu_util)
            stats.max_cpu_percent = max(cpu_util)

        if ram_used:
            stats.avg_ram_mb = sum(ram_used) / len(ram_used)
            stats.max_ram_mb = max(ram_used)

        stats.snapshots = self.snapshots

        return stats

    def get_current_usage(self) -> Dict[str, Any]:
        """
        Get current resource usage.

        Returns:
            Dict with current usage
        """
        snapshot = self.take_snapshot()

        return {
            "timestamp": snapshot.timestamp,
            "gpu_memory_mb": snapshot.gpu_memory_used_mb,
            "gpu_memory_percent": (
                (snapshot.gpu_memory_used_mb / snapshot.gpu_memory_total_mb * 100)
                if snapshot.gpu_memory_total_mb > 0 else 0
            ),
            "gpu_utilization": snapshot.gpu_utilization_percent,
            "cpu_percent": snapshot.cpu_percent,
            "ram_mb": snapshot.ram_used_mb,
            "ram_percent": (
                (snapshot.ram_used_mb / snapshot.ram_total_mb * 100)
                if snapshot.ram_total_mb > 0 else 0
            ),
        }

    def clear_snapshots(self) -> None:
        """Clear all snapshots."""
        self.snapshots = []

    def __enter__(self):
        """Context manager entry."""
        self.start_monitoring()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_monitoring()
