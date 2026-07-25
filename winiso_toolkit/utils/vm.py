"""QEMU VM ISO Boot Tester.

Launches a lightweight QEMU virtual machine instance to verify ISO bootability
in a headless or windowed sandbox before burning to physical USB.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from winiso_toolkit.utils.platform import run_command, which


class QEMUTester:
    """Test built ISOs in QEMU VM."""

    def is_qemu_available(self) -> bool:
        return which("qemu-system-x86_64") is not None or which("qemu-system-x86_64.exe") is not None

    def launch_test_vm(
        self,
        iso_path: Path,
        ram_mb: int = 2048,
        uefi: bool = False,
    ) -> subprocess.Popen:
        """Launch QEMU with the target ISO as a virtual CD-ROM.

        Returns the running subprocess.
        """
        qemu_bin = which("qemu-system-x86_64") or which("qemu-system-x86_64.exe")
        if not qemu_bin:
            raise RuntimeError("QEMU is not installed. Install qemu-system-x86_64 to test ISOs.")

        iso_path = Path(iso_path).resolve()
        if not iso_path.is_file():
            raise FileNotFoundError(f"ISO not found: {iso_path}")

        cmd = [
            str(qemu_bin),
            "-m", str(ram_mb),
            "-cdrom", str(iso_path),
            "-boot", "d",
            "-vga", "std",
        ]

        if uefi:
            # Check for OVMF firmware file
            ovmf = which("OVMF.fd") or Path("/usr/share/ovmf/OVMF.fd")
            if ovmf and Path(ovmf).exists():
                cmd.extend(["-bios", str(ovmf)])

        proc = subprocess.Popen(cmd)
        return proc
