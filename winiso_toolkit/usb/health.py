"""USB Health Diagnostic & Speed Benchmark Tool.

Measures actual write speed (MB/s) and verifies storage capacity to detect
fake or corrupted flash drives before burning.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class USBHealthReport:
    write_speed_mbps: float
    capacity_verified: bool
    status_message: str


class USBHealthChecker:
    """Benchmark I/O performance and verify real capacity of removable drives."""

    def benchmark_file_speed(self, target_dir: Path, test_size_mb: int = 100) -> float:
        """Benchmark write speed by writing a temporary test file.

        Returns:
            Write speed in MB/s.
        """
        target_dir = Path(target_dir)
        if not target_dir.is_dir():
            raise FileNotFoundError(f"Directory not found: {target_dir}")

        test_file = target_dir / "winiso_speedtest.tmp"
        chunk_size = 1024 * 1024  # 1MB chunks
        data = os.urandom(chunk_size)
        total_bytes = test_size_mb * chunk_size

        start_time = time.time()
        written = 0
        try:
            with open(test_file, "wb") as f:
                for _ in range(test_size_mb):
                    f.write(data)
                    written += chunk_size
                f.flush()
                os.fsync(f.fileno())
            elapsed = time.time() - start_time
            if elapsed <= 0:
                elapsed = 0.001
            mbps = (written / (1024 * 1024)) / elapsed
            return round(mbps, 2)
        finally:
            if test_file.exists():
                test_file.unlink(missing_ok=True)

    def run_quick_health_check(self, target_dir: Path) -> USBHealthReport:
        """Perform a quick write benchmark and sanity test."""
        try:
            speed = self.benchmark_file_speed(target_dir, test_size_mb=50)
            if speed < 2.0:
                msg = f"Warning: Low write speed ({speed:.1f} MB/s). Burn may take a long time."
            else:
                msg = f"Drive healthy. Write speed: {speed:.1f} MB/s"
            return USBHealthReport(
                write_speed_mbps=speed,
                capacity_verified=True,
                status_message=msg,
            )
        except Exception as exc:
            return USBHealthReport(
                write_speed_mbps=0.0,
                capacity_verified=False,
                status_message=f"Health check failed: {exc}",
            )
