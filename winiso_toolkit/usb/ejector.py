"""USB Safe Ejection & Buffer Flushing Helper."""

from __future__ import annotations

import subprocess

from winiso_toolkit.utils.platform import is_linux, is_windows, run_command


class USBEjector:
    """Flush write buffers and safely unmount USB storage devices."""

    def safe_eject(self, device_path: str) -> tuple[bool, str]:
        """Flush buffers and safely eject USB drive.

        Returns:
            (success, message)
        """
        if is_linux():
            return self._eject_linux(device_path)
        if is_windows():
            return self._eject_windows(device_path)
        return False, "Unsupported platform for safe eject."

    def _eject_linux(self, device_path: str) -> tuple[bool, str]:
        # Flush buffers
        subprocess.run(["sync"], check=False)
        res = subprocess.run(["eject", device_path], capture_output=True, text=True)
        if res.returncode == 0:
            return True, "Safe to remove USB drive."
        return False, f"Could not eject drive: {res.stderr or res.stdout}"

    def _eject_windows(self, device_path: str) -> tuple[bool, str]:
        # Parse PHYSICALDRIVE number from path (e.g. \\.\PHYSICALDRIVE1)
        normalized = device_path.upper().replace("\\\\.\\", "")
        if normalized.startswith("PHYSICALDRIVE"):
            suffix = normalized.replace("PHYSICALDRIVE", "")
            if not suffix.isdigit():
                return False, f"Invalid device path: {device_path}"
            disk_num = int(suffix)
            if disk_num < 0:
                return False, f"Invalid disk number in device path: {device_path}"
            # Pass disk_num as a validated integer — no string interpolation of
            # untrusted input; the value came from a digit-only suffix above.
            ps = (
                f"Get-Disk -Number {disk_num} | Set-Disk -IsOffline $true; "
                f"Get-Disk -Number {disk_num} | Set-Disk -IsOffline $false"
            )
            res = run_command(["powershell", "-NoProfile", "-Command", ps], check=False)
            if res.returncode == 0:
                return True, "Safe to remove USB drive (buffers flushed)."
        return False, "Failed to offline/eject drive."
