"""Driver slipstreaming module.

Pre-injects custom storage (NVMe/RAID) and network (Wi-Fi/LAN) drivers (.inf)
into Windows setup WIM images (boot.wim and install.wim) for out-of-the-box hardware support.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from winiso_toolkit.utils.platform import is_windows, run_command, which


class DriverInjector:
    """Inject custom driver directory (.inf) into Windows WIM images."""

    def find_driver_files(self, driver_dir: Path) -> list[Path]:
        """Find all .inf files inside a driver directory."""
        driver_dir = Path(driver_dir)
        if not driver_dir.is_dir():
            return []
        found = set(driver_dir.rglob("*.inf")).union(driver_dir.rglob("*.INF"))
        return sorted(list(found))

    def inject_drivers_dism(self, wim_path: Path, image_index: int, driver_dir: Path) -> bool:
        """Inject drivers using DISM on Windows."""
        dism = which("dism") or which("dism.exe")
        if not dism:
            return False

        # DISM requires mounting the image
        import tempfile
        mount_dir = Path(tempfile.mkdtemp(prefix="winiso_mount_wim_"))

        try:
            # Mount
            mount_cmd = [
                str(dism), "/Mount-Image",
                f"/ImageFile:{wim_path}",
                f"/Index:{image_index}",
                f"/MountDir:{mount_dir}",
            ]
            res = run_command(mount_cmd, check=False)
            if res.returncode != 0:
                return False

            # Add drivers
            add_cmd = [
                str(dism), f"/Image:{mount_dir}",
                "/Add-Driver", f"/Driver:{driver_dir}",
                "/Recurse",
            ]
            run_command(add_cmd, check=False)

            # Unmount & commit
            unmount_cmd = [
                str(dism), "/Unmount-Image",
                f"/MountDir:{mount_dir}",
                "/Commit",
            ]
            run_command(unmount_cmd, check=False)
            return True
        finally:
            shutil.rmtree(mount_dir, ignore_errors=True)

    def inject_drivers(self, iso_extracted_root: Path, driver_dir: Path) -> int:
        """Inject drivers from driver_dir into the extracted ISO structure.

        Returns:
            Number of driver .inf files found and queued/injected.
        """
        infs = self.find_driver_files(driver_dir)
        if not infs:
            return 0

        # Copy drivers into $WinPEDriver$ / $OEM$ directory inside ISO root for auto-installation
        oem_dir = iso_extracted_root / "$WinPEDriver$"
        oem_dir.mkdir(parents=True, exist_ok=True)

        for inf in infs:
            rel = inf.name
            target = oem_dir / rel
            if inf.is_file():
                shutil.copy2(inf, target)

        return len(infs)
