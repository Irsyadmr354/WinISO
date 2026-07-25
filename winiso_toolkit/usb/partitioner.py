"""Dual-partition layout helper for UEFI + Legacy bootability with >4GB file support.

Creates a 64MB FAT32 EFI boot partition plus an NTFS data partition, ensuring
strict UEFI firmware compatibility without needing to split large WIM files.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from winiso_toolkit.utils.platform import is_linux, is_windows, run_command


class DualPartitioner:
    """Create dual-partition USB layout (FAT32 Boot + NTFS Data)."""

    def prepare_dual_partition_linux(self, device: str) -> tuple[Path, Path]:
        """Partition device on Linux into FAT32 (64MB) + NTFS (Rest).

        Returns:
            (boot_mount_point, data_mount_point)
        """
        boot_mount = Path(tempfile.mkdtemp(prefix="winiso_boot_"))
        data_mount = Path(tempfile.mkdtemp(prefix="winiso_data_"))

        script = f"""
set -e
parted -s {device} mklabel gpt
parted -s {device} mkpart primary fat32 1MiB 65MiB
parted -s {device} set 1 boot on
parted -s {device} set 1 esp on
parted -s {device} mkpart primary ntfs 65MiB 100%
sleep 2

P1={device}1
if [ ! -b "$P1" ]; then P1={device}p1; fi

P2={device}2
if [ ! -b "$P2" ]; then P2={device}p2; fi

mkfs.vfat -F 32 -n "UEFI_BOOT" "$P1"
mkfs.ntfs -f -L "WINISO_DATA" "$P2"

mount "$P1" {boot_mount}
mount "$P2" {data_mount}
"""
        result = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Dual partitioning failed: {result.stderr or result.stdout}")

        return boot_mount, data_mount

    def prepare_dual_partition_windows(self, disk_num: int) -> tuple[str, str]:
        """Partition disk on Windows into FAT32 (64MB) + NTFS (Rest).

        Returns:
            (boot_drive_letter, data_drive_letter)
        """
        script = f"""
select disk {disk_num}
clean
convert gpt
create partition primary size=64
format fs=fat32 quick label="UEFI_BOOT"
set id="c12a7328-f81f-11d2-ba4b-00a0c93ec93b"
assign
create partition primary
format fs=ntfs quick label="WINISO_DATA"
assign
exit
"""
        script_file = Path(tempfile.gettempdir()) / "winiso_dual_diskpart.txt"
        script_file.write_text(script, encoding="utf-8")

        result = subprocess.run(
            ["diskpart", "/s", str(script_file)],
            capture_output=True,
            text=True,
        )
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
