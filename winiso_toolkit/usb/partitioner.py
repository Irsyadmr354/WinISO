"""Dual-partition layout helper for UEFI + Legacy bootability with >4GB file support.

Creates a 64MB FAT32 EFI boot partition plus an NTFS data partition, ensuring
strict UEFI firmware compatibility without needing to split large WIM files.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
import time
from pathlib import Path

from winiso_toolkit.utils.platform import is_linux

_LINUX_DEVICE_RE = re.compile(r"^/dev/[A-Za-z0-9]+$")


def _validate_linux_device(device: str) -> str:
    """Validate ``device`` is a safe ``/dev/<name>`` path to prevent shell injection."""
    if not _LINUX_DEVICE_RE.match(device):
        raise ValueError(f"Invalid or unsafe device path: {device!r}")
    return device


def _validate_disk_num(disk_num: int) -> int:
    """Validate ``disk_num`` is a non-negative integer disk index."""
    if not isinstance(disk_num, int) or isinstance(disk_num, bool) or disk_num < 0:
        raise ValueError(f"Invalid disk number: {disk_num!r}")
    return disk_num


class DualPartitioner:
    """Create dual-partition USB layout (FAT32 Boot + NTFS Data)."""

    def prepare_dual_partition_linux(self, device: str) -> tuple[Path, Path]:
        """Partition device on Linux into FAT32 (64MB) + NTFS (Rest).

        Returns:
            (boot_mount_point, data_mount_point)
        """
        if not is_linux():
            raise RuntimeError("prepare_dual_partition_linux requires Linux.")

        device = _validate_linux_device(device)
        boot_mount = Path(tempfile.mkdtemp(prefix="winiso_boot_"))
        data_mount = Path(tempfile.mkdtemp(prefix="winiso_data_"))

        steps: list[list[str]] = [
            ["parted", "-s", device, "mklabel", "gpt"],
            ["parted", "-s", device, "mkpart", "primary", "fat32", "1MiB", "65MiB"],
            ["parted", "-s", device, "set", "1", "boot", "on"],
            ["parted", "-s", device, "set", "1", "esp", "on"],
            ["parted", "-s", device, "mkpart", "primary", "ntfs", "65MiB", "100%"],
        ]
        for cmd in steps:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(
                    f"Dual partitioning failed ({' '.join(cmd)}): "
                    f"{result.stderr or result.stdout}"
                )

        time.sleep(2)

        p1 = Path(f"{device}1") if Path(f"{device}1").exists() else Path(f"{device}p1")
        p2 = Path(f"{device}2") if Path(f"{device}2").exists() else Path(f"{device}p2")
        if not p1.exists() or not p2.exists():
            raise RuntimeError(f"Partition device nodes not found for {device}")

        for cmd in (
            ["mkfs.vfat", "-F", "32", "-n", "UEFI_BOOT", str(p1)],
            ["mkfs.ntfs", "-f", "-L", "WINISO_DATA", str(p2)],
            ["mount", str(p1), str(boot_mount)],
            ["mount", str(p2), str(data_mount)],
        ):
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(
                    f"Dual partition setup failed ({' '.join(cmd)}): "
                    f"{result.stderr or result.stdout}"
                )

        return boot_mount, data_mount

    def prepare_dual_partition_windows(self, disk_num: int) -> tuple[str, str]:
        """Partition disk on Windows into FAT32 (64MB) + NTFS (Rest).

        Returns:
            (boot_drive_letter, data_drive_letter)
        """
        disk_num = _validate_disk_num(disk_num)
        script = f"""
select disk {disk_num}
clean
convert gpt
create partition primary size=64
format fs=fat32 quick label="UEFI_BOOT"
assign
create partition primary
format fs=ntfs quick label="WINISO_DATA"
assign
exit
"""
        fd, script_path = tempfile.mkstemp(prefix="winiso_dual_diskpart_", suffix=".txt")
        script_file = Path(script_path)
        try:
            with open(fd, "w", encoding="utf-8") as f:
                f.write(script)

            result = subprocess.run(
                ["diskpart", "/s", str(script_file)],
                capture_output=True,
                text=True,
            )
        finally:
            script_file.unlink(missing_ok=True)

        if result.returncode != 0:
            raise RuntimeError(f"diskpart dual-partition failed: {result.stderr or result.stdout}")

        # Fetch drive letters via PowerShell
        ps = f"""
$parts = Get-Partition -DiskNumber {disk_num} | Where-Object DriveLetter | Sort-Object PartitionNumber
$letters = $parts.DriveLetter
if ($letters.Count -ge 2) {{
    "$($letters[0]),$($letters[1])"
}} else {{
    ""
}}
"""
        letter_result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
        )
        out = letter_result.stdout.strip()
        if not out or "," not in out:
            raise RuntimeError("Could not determine USB drive letters after dual partitioning.")

        boot_let, data_let = out.split(",", 1)
        return boot_let.strip(), data_let.strip()
