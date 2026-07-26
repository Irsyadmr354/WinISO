"""Driver slipstreaming module.

Pre-injects custom storage (NVMe/RAID) and network (Wi-Fi/LAN) drivers (.inf)
into Windows setup WIM images (boot.wim and install.wim) for out-of-the-box hardware support.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from winiso_toolkit.utils.platform import run_command, which


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
            res_add = run_command(add_cmd, check=False)
            if res_add.returncode != 0:
                import logging
                logging.getLogger(__name__).warning("Failed to add some drivers")

            # Unmount & commit
            unmount_cmd = [
                str(dism), "/Unmount-Image",
                f"/MountDir:{mount_dir}",
                "/Commit",
            ]
            res_unmount = run_command(unmount_cmd, check=False)
            if res_unmount.returncode != 0:
                raise RuntimeError(f"Failed to unmount DISM image: {res_unmount.stderr or res_unmount.stdout}")
            return True
        finally:
            run_command([str(dism), "/Unmount-Image", f"/MountDir:{mount_dir}", "/Discard"], check=False)
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

        copied_dirs = set()
        for inf in infs:
            driver_pkg_dir = inf.parent
            if driver_pkg_dir not in copied_dirs:
                dest = oem_dir / driver_pkg_dir.name
                shutil.copytree(str(driver_pkg_dir), str(dest), dirs_exist_ok=True)
                copied_dirs.add(driver_pkg_dir)

        return len(infs)
