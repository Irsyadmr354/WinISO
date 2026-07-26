"""Windows To Go (WTG) Live Portable USB Creator."""

from __future__ import annotations

import logging
from pathlib import Path
from winiso_toolkit.utils.platform import run_command, which
from winiso_toolkit.utils.progress import ProgressCallback

logger = logging.getLogger(__name__)


class WindowsToGoDeployer:
    """Deploy Windows directly onto a USB drive as a live portable OS."""

    def deploy_wtg_windows(
        self,
        wim_path: Path,
        wim_index: int,
        target_drive_letter: str,
        progress: ProgressCallback | None = None,
    ) -> bool:
        """Apply WIM image directly to USB drive and configure BCD boot sector."""
        target_drive_letter = target_drive_letter.rstrip(":\\")
        wim_path = Path(wim_path)
        dism = which("dism") or which("dism.exe")
        if not dism:
            raise RuntimeError("DISM is required for Windows To Go deployment.")

        if progress:
            progress(10, f"Applying Windows To Go image to {target_drive_letter}:\\…")

        # Apply image using DISM
        apply_cmd = [
            str(dism), "/Apply-Image",
            f"/ImageFile:{wim_path}",
            f"/Index:{wim_index}",
            f"/ApplyDir:{target_drive_letter}:\\",
        ]
        res = run_command(apply_cmd, check=False)
        if res.returncode != 0:
            raise RuntimeError(f"DISM Apply-Image failed: {res.stderr or res.stdout}")

        if progress:
            progress(85, "Configuring Windows To Go bootloader (bcdboot)…")

        # Configure BCD boot sector for portable USB boot
        bcdboot = which("bcdboot") or which("bcdboot.exe")
        if not bcdboot:
            raise RuntimeError("bcdboot is required for Windows To Go bootloader configuration.")
        bcd_cmd = [
            str(bcdboot), f"{target_drive_letter}:\\Windows",
            "/s", f"{target_drive_letter}:",
            "/f", "ALL",
        ]
        res_bcd = run_command(bcd_cmd, check=False)
        if res_bcd.returncode != 0:
            raise RuntimeError(f"bcdboot failed: {res_bcd.stderr or res_bcd.stdout}")

        if progress:
            progress(100, "Windows To Go deployment complete.")

        return True
