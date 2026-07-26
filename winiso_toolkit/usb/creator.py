"""Create bootable Windows USB installers."""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import tempfile
import threading
import time
from enum import Enum
from pathlib import Path

from winiso_toolkit.iso.drivers import DriverInjector
from winiso_toolkit.iso.extract import extract_iso
from winiso_toolkit.iso.unattended import BypassOptions, UnattendedGenerator
from winiso_toolkit.usb.partitioner import DualPartitioner
from winiso_toolkit.utils.platform import is_linux, is_windows, run_command
from winiso_toolkit.utils.progress import ProgressCallback, clamp_progress


class BootMode(str, Enum):
    UEFI = "uefi"
    LEGACY = "legacy"
    BOTH = "both"


_LINUX_DEVICE_RE = re.compile(r"^/dev/[A-Za-z0-9]+$")


def _validate_linux_device(device: str) -> str:
    """Validate that ``device`` is a safe, well-formed Linux block device path.

    Prevents shell injection via crafted device strings
    (e.g. ``/dev/sdb; rm -rf /``).
    """
    if not _LINUX_DEVICE_RE.match(device):
        raise ValueError(f"Invalid or unsafe device path: {device!r}")
    return device


def _validate_disk_num(disk_num: int) -> int:
    """Validate that ``disk_num`` is a non-negative integer disk index."""
    if not isinstance(disk_num, int) or isinstance(disk_num, bool) or disk_num < 0:
        raise ValueError(f"Invalid disk number: {disk_num!r}")
    return disk_num


class USBCreator:
    """Format USB and copy Windows installer files."""

    def __init__(self) -> None:
        self._cancel_event = threading.Event()

    def cancel(self) -> None:
        self._cancel_event.set()

    def validate_capacity(self, usb_size: int, iso_size: int) -> tuple[bool, str]:
        if usb_size >= iso_size:
            return True, ""
        usb_gb = usb_size / (1024**3)
        iso_gb = iso_size / (1024**3)
        return False, (
            f"Your USB is {usb_gb:.1f} GB, this ISO requires {iso_gb:.1f} GB. "
            "Choose: (a) compress the ISO further by removing editions/languages, "
            "(b) use a larger USB drive."
        )

    def create(
        self,
        iso_path: Path,
        device: str,
        *,
        boot_mode: BootMode = BootMode.BOTH,
        bypass_options: BypassOptions | None = None,
        driver_dir: Path | None = None,
        use_dual_partition: bool = False,
        progress: ProgressCallback | None = None,
        verify: bool = True,
    ) -> None:
        iso_path = Path(iso_path)

        if progress:
            progress(0, "Extracting ISO contents…")

        work_dir = Path(tempfile.mkdtemp(prefix="winiso_usb_"))
        self._cancel_event.clear()

        boot_mount_point: Path | None = None
        mount_point: Path | None = None
        try:
            self._extract_iso(iso_path, work_dir)

            if bypass_options:
                if progress:
                    progress(3, "Injecting autounattend.xml bypasses…")
                gen = UnattendedGenerator(bypass_options)
                gen.save(work_dir / "autounattend.xml")

            if driver_dir and Path(driver_dir).is_dir():
                if progress:
                    progress(4, "Injecting custom drivers…")
                injector = DriverInjector()
                injector.inject_drivers(work_dir, Path(driver_dir))

            files_with_sizes = [(f, f.stat().st_size) for f in work_dir.rglob("*") if f.is_file()]
            total_bytes = sum(size for _, size in files_with_sizes)

            if use_dual_partition:
                if progress:
                    progress(5, "Creating dual UEFI FAT32+NTFS partition layout…")
                partitioner = DualPartitioner()
                if is_linux():
                    boot_mnt, data_mnt = partitioner.prepare_dual_partition_linux(device)
                    boot_mount_point = boot_mnt
                    mount_point = data_mnt
                    self._copy_files(work_dir, data_mnt, files_with_sizes, progress)
                    # Copy EFI boot folder to FAT32 boot partition
                    efi_src = work_dir / "efi"
                    if efi_src.exists():
                        shutil.copytree(efi_src, boot_mnt / "efi", dirs_exist_ok=True)
                elif is_windows():
                    disk_num = _validate_disk_num(self._physical_drive_number(device))
                    boot_let, data_let = partitioner.prepare_dual_partition_windows(disk_num)
                    mount_point = Path(f"{data_let}:\\")
                    self._copy_files(work_dir, mount_point, files_with_sizes, progress)
                    efi_src = work_dir / "efi"
                    if efi_src.exists():
                        shutil.copytree(efi_src, Path(f"{boot_let}:\\efi"), dirs_exist_ok=True)
                    self._write_bootsector_windows(data_let, work_dir)
            else:
                if is_linux():
                    device = _validate_linux_device(device)
                    mount_point = self._prepare_linux_usb(device, boot_mode, progress)
                    self._copy_files(work_dir, mount_point, files_with_sizes, progress)
                elif is_windows():
                    drive_letter = self._prepare_windows_usb(device, boot_mode, progress)
                    mount_point = Path(f"{drive_letter}:\\")
                    self._copy_files(work_dir, mount_point, files_with_sizes, progress)
                    self._write_bootsector_windows(drive_letter, work_dir)
                else:
                    raise RuntimeError("Unsupported platform for USB creation.")

            if verify and mount_point:
                if progress:
                    progress(95, "Verifying written files…")
                self._verify_copy(work_dir, mount_point)

            if progress:
                progress(100, "USB creation complete.")
        finally:
            if boot_mount_point and is_linux():
                subprocess.run(["umount", str(boot_mount_point)], capture_output=True, check=False)
                try:
                    boot_mount_point.rmdir()
                except OSError:
                    pass
            if mount_point and is_linux():
                subprocess.run(["umount", str(mount_point)], capture_output=True, check=False)
                try:
                    mount_point.rmdir()
                except OSError:
                    pass
            shutil.rmtree(work_dir, ignore_errors=True)

    def _extract_iso(self, iso_path: Path, dest: Path) -> None:
        extract_iso(iso_path, dest)

    def _prepare_linux_usb(
        self,
        device: str,
        boot_mode: BootMode,
        progress: ProgressCallback | None,
    ) -> Path:
        if not is_linux():
            raise RuntimeError("_prepare_linux_usb requires Linux.")

        device = _validate_linux_device(device)

        if progress:
            progress(5, f"Partitioning {device}…")

        mount_point = Path(tempfile.mkdtemp(prefix="winiso_mount_"))
        part_type = "gpt" if boot_mode in (BootMode.UEFI, BootMode.BOTH) else "msdos"

        # UEFI firmware requires FAT32. For BOTH mode, use NTFS (most modern UEFI can boot NTFS via CSM, and NTFS handles >4GB files).
        fs_type = "vfat" if boot_mode == BootMode.UEFI else "ntfs"

        steps: list[list[str]] = [
            ["parted", "-s", device, "mklabel", part_type],
            ["parted", "-s", device, "mkpart", "primary", fs_type, "1MiB", "100%"],
        ]
        if boot_mode in (BootMode.LEGACY, BootMode.BOTH):
            steps.append(["parted", "-s", device, "set", "1", "boot", "on"])

        for cmd in steps:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(
                    f"USB partitioning failed ({' '.join(cmd)}): "
                    f"{result.stderr or result.stdout}"
                )

        time.sleep(2)

        part = Path(f"{device}1")
        if not part.exists():
            part = Path(f"{device}p1")
        if not part.exists():
            raise RuntimeError(f"Partition device node not found for {device}")

        mkfs_cmd = (
            ["mkfs.ntfs", "-f", "-L", "WINISO", str(part)]
            if fs_type == "ntfs"
            else ["mkfs.vfat", "-n", "WINISO", str(part)]
        )
        result = subprocess.run(mkfs_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Filesystem creation failed: {result.stderr or result.stdout}")

        result = subprocess.run(
            ["mount", str(part), str(mount_point)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Mount failed: {result.stderr or result.stdout}")
        return mount_point

    def _prepare_windows_usb(
        self,
        device_path: str,
        boot_mode: BootMode,
        progress: ProgressCallback | None,
    ) -> str:
        if progress:
            progress(5, "Preparing USB via diskpart…")

        disk_num = _validate_disk_num(self._physical_drive_number(device_path))
        part_type = "gpt" if boot_mode in (BootMode.UEFI, BootMode.BOTH) else "mbr"
        # UEFI firmware requires FAT32. For BOTH mode, use NTFS (most modern UEFI can boot NTFS via CSM, and NTFS handles >4GB files).
        fs = "fat32" if boot_mode == BootMode.UEFI else "ntfs"

        script = f"""
select disk {disk_num}
clean
convert {part_type}
create partition primary
{"active" if part_type == "mbr" else ""}
format fs={fs} quick label=WINISO
assign
exit
"""
        fd, script_path = tempfile.mkstemp(prefix="winiso_diskpart_", suffix=".txt")
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
            raise RuntimeError(f"diskpart failed: {result.stderr or result.stdout}")

        # Find assigned drive letter
        ps = f"(Get-Partition -DiskNumber {disk_num} | Where-Object DriveLetter).DriveLetter"
        letter_result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
        )
        letter = letter_result.stdout.strip()
        if not letter:
            raise RuntimeError("Could not determine USB drive letter after formatting.")
        return letter

    def _physical_drive_number(self, device_path: str) -> int:
        match = device_path.upper().replace("\\\\.\\", "")
        if match.startswith("PHYSICALDRIVE"):
            suffix = match.replace("PHYSICALDRIVE", "")
            if not suffix.isdigit():
                raise ValueError(f"Invalid Windows device path: {device_path}")
            return int(suffix)
        raise ValueError(f"Invalid Windows device path: {device_path}")

    def _copy_files(
        self,
        source: Path,
        dest: Path,
        files_with_sizes: list[tuple[Path, int]],
        progress: ProgressCallback | None,
    ) -> None:
        copied = 0
        total_bytes = sum(size for _, size in files_with_sizes)
        start_time = time.time()

        for src_file, size in files_with_sizes:
            if self._cancel_event.is_set():
                raise InterruptedError("USB creation cancelled by user.")

            rel = src_file.relative_to(source)
            dst_file = dest / rel
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
            copied += size

            if progress and total_bytes > 0:
                elapsed = time.time() - start_time
                speed_mbps = (copied / (1024 * 1024)) / max(elapsed, 0.001)
                remaining_bytes = total_bytes - copied
                eta_sec = remaining_bytes / max(copied / max(elapsed, 0.001), 1)

                pct = clamp_progress((copied / total_bytes) * 80 + 10)
                msg = f"Copying {rel.name} ({speed_mbps:.1f} MB/s — ETA {int(eta_sec)}s)"
                progress(pct, msg)

    def _write_bootsector_windows(self, drive_letter: str, iso_root: Path) -> None:
        bootsect = iso_root / "boot" / "bootsect.exe"
        if bootsect.exists():
            result = run_command([str(bootsect), "/nt60", f"{drive_letter}:", "/force"], check=False)
            if result.returncode != 0:
                raise RuntimeError(
                    f"bootsect.exe failed (exit {result.returncode}): "
                    f"{result.stderr or result.stdout}"
                )

    def _verify_copy(self, source: Path, dest: Path) -> None:
        critical = [
            "boot/bootsect.exe",
            "boot/etfsboot.com",
            "efi/microsoft/boot/efisys.bin",
            "sources/boot.wim",
            "sources/install.wim",
            "sources/install.esd",
        ]
        for rel in critical:
            src = source / rel
            dst = dest / rel
            if not src.exists():
                continue
            if not dst.exists():
                raise RuntimeError(f"Verification failed: missing {rel} on USB.")
            if self._file_hash(src) != self._file_hash(dst):
                raise RuntimeError(f"Verification failed: checksum mismatch for {rel}.")

    @staticmethod
    def _file_hash(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
