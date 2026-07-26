"""USB Health Diagnostic & Speed Benchmark Tool.

Measures actual write speed (MB/s) and verifies storage capacity to detect
fake or corrupted flash drives before burning.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

from winiso_toolkit.utils.platform import is_linux, is_windows


@dataclass
class USBHealthReport:
    write_speed_mbps: float
    capacity_verified: bool
    status_message: str


class USBHealthChecker:
    """Benchmark I/O performance and verify real capacity of removable drives."""

    def resolve_writable_directory(self, target: Path | str, mount_point: str = "") -> Path:
        """Map a block device path to a writable directory for file-based tests."""
        if mount_point:
            mounted = Path(mount_point)
            if mounted.is_dir():
                return mounted

        target_str = str(target)
        if is_windows() and "PHYSICALDRIVE" in target_str.upper():
            return self._resolve_windows_drive_letter(target_str)
        if is_linux() and target_str.startswith("/dev/"):
            return self._resolve_linux_mount(target_str)

        target_path = Path(target)
        if target_path.is_dir():
            return target_path

        raise FileNotFoundError(
            f"No writable mount point for {target_path}. "
            "Mount or format the USB drive before running a health check."
        )

    def _physical_drive_number(self, device_path: str) -> int:
        normalized = device_path.upper().replace("\\\\.\\", "")
        if not normalized.startswith("PHYSICALDRIVE"):
            raise ValueError(f"Invalid Windows device path: {device_path}")
        suffix = normalized.removeprefix("PHYSICALDRIVE")
        if not suffix.isdigit():
            raise ValueError(f"Invalid Windows device path: {device_path}")
        return int(suffix)

    def _resolve_windows_drive_letter(self, device_path: str) -> Path:
        import subprocess

        disk_num = self._physical_drive_number(device_path)
        ps = (
            f"$letter = (Get-Partition -DiskNumber {disk_num} | "
            "Where-Object { $_.DriveLetter } | "
            "Sort-Object -Property PartitionNumber | "
            "Select-Object -First 1).DriveLetter; "
            "if ($letter) { Write-Output ($letter + ':') }"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        letter = result.stdout.strip()
        if not letter:
            raise FileNotFoundError(
                f"No mounted drive letter for {device_path}. "
                "Assign a drive letter or format the USB before running a health check."
            )
        mount = Path(letter if letter.endswith(":") else f"{letter}:")
        if not mount.is_dir():
            raise FileNotFoundError(f"Drive letter path is not accessible: {mount}")
        return mount

    def _resolve_linux_mount(self, device_path: str) -> Path:
        import json
        import subprocess

        result = subprocess.run(
            ["lsblk", "-Jn", "-o", "NAME,MOUNTPOINT", device_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            raise FileNotFoundError(
                f"No mount point found for {device_path}. "
                "Mount the USB partition before running a health check."
            )

        data = json.loads(result.stdout)
        devices = data.get("blockdevices") or []
        if not devices:
            raise FileNotFoundError(f"No mount point found for {device_path}.")

        mount_candidates: list[str] = []
        for dev in devices:
            if dev.get("mountpoint"):
                mount_candidates.append(dev["mountpoint"])
            for child in dev.get("children") or []:
                if child.get("mountpoint"):
                    mount_candidates.append(child["mountpoint"])

        for mount in mount_candidates:
            mount_path = Path(mount)
            if mount_path.is_dir():
                return mount_path

        raise FileNotFoundError(
            f"No mount point found for {device_path}. "
            "Mount the USB partition before running a health check."
        )

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
        data = b"\x00" * chunk_size
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

    def verify_capacity(self, target_dir: Path, test_size_mb: int = 5) -> bool:
        """Write a known pattern and read it back to detect fake/corrupt flash."""
        target_dir = Path(target_dir)
        if not target_dir.is_dir():
            raise FileNotFoundError(f"Directory not found: {target_dir}")

        test_file = target_dir / "winiso_captest.tmp"
        chunk_size = 1024 * 1024
        pattern = bytes(i % 256 for i in range(chunk_size))

        try:
            with open(test_file, "wb") as f:
                for _ in range(test_size_mb):
                    f.write(pattern)
                f.flush()
                os.fsync(f.fileno())

            with open(test_file, "rb") as f:
                for _ in range(test_size_mb):
                    block = f.read(chunk_size)
                    if block != pattern:
                        return False
            return True
        finally:
            if test_file.exists():
                test_file.unlink(missing_ok=True)

    def run_quick_health_check(
        self,
        target: Path | str,
        *,
        mount_point: str = "",
    ) -> USBHealthReport:
        """Perform a quick write benchmark and sanity test."""
        try:
            test_dir = self.resolve_writable_directory(target, mount_point)
            capacity_ok = self.verify_capacity(test_dir, test_size_mb=5)
            speed = self.benchmark_file_speed(test_dir, test_size_mb=50)
            if not capacity_ok:
                msg = "Warning: Write/read verification failed — drive may be fake or failing."
            elif speed < 2.0:
                msg = f"Warning: Low write speed ({speed:.1f} MB/s). Burn may take a long time."
            else:
                msg = f"Drive healthy. Write speed: {speed:.1f} MB/s"
            return USBHealthReport(
                write_speed_mbps=speed,
                capacity_verified=capacity_ok,
                status_message=msg,
            )
        except Exception as exc:
            return USBHealthReport(
                write_speed_mbps=0.0,
                capacity_verified=False,
                status_message=f"Health check failed: {exc}",
            )
