"""Detect and install missing external tools."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from winiso_toolkit.utils.platform import is_linux, is_windows, run_command, which


@dataclass
class DependencyStatus:
    name: str
    installed: bool
    path: Path | None = None
    message: str = ""


@dataclass
class DependencyInstaller:
    """Check and optionally install required external tools."""

    wimlib_cmd: str = "wimlib-imagex"
    xorriso_cmd: str = "xorriso"
    oscdimg_cmd: str = "oscdimg"
    log: list[str] = field(default_factory=list)

    def _log(self, message: str) -> None:
        self.log.append(message)

    def detect_linux_distro(self) -> str:
        os_release = Path("/etc/os-release")
        if not os_release.exists():
            return "unknown"
        content = os_release.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"^ID=(.+)$", content, re.MULTILINE)
        if not match:
            return "unknown"
        return match.group(1).strip().strip('"').lower()

    def check_wimlib(self) -> DependencyStatus:
        for name in ("wimlib-imagex", "wimexport", "wiminfo"):
            path = which(name)
            if path:
                self.wimlib_cmd = name if name != "wimexport" else "wimlib-imagex"
                return DependencyStatus(name="wimlib", installed=True, path=path)
        if is_windows():
            bundled = Path(__file__).resolve().parents[1] / "tools" / "wimlib-imagex.exe"
            if bundled.exists():
                self.wimlib_cmd = str(bundled)
                return DependencyStatus(
                    name="wimlib",
                    installed=True,
                    path=bundled,
                    message="Using bundled wimlib-imagex.exe",
                )
        return DependencyStatus(
            name="wimlib",
            installed=False,
            message="wimlib not found. Required for WIM/ESD compression.",
        )

    def check_xorriso(self) -> DependencyStatus:
        path = which("xorriso")
        if path:
            self.xorriso_cmd = "xorriso"
            return DependencyStatus(name="xorriso", installed=True, path=path)
        return DependencyStatus(
            name="xorriso",
            installed=False,
            message="xorriso not found. Required for bootable ISO creation on Linux.",
        )

    def check_oscdimg(self) -> DependencyStatus:
        for candidate in (
            which("oscdimg"),
            Path(r"C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\amd64\Oscdimg\oscdimg.exe"),
            Path(r"C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\x86\Oscdimg\oscdimg.exe"),
        ):
            if candidate and Path(candidate).exists():
                self.oscdimg_cmd = str(candidate)
                return DependencyStatus(name="oscdimg", installed=True, path=Path(candidate))
        return DependencyStatus(
            name="oscdimg",
            installed=False,
            message="oscdimg not found. Install Windows ADK or use xorriso on Linux.",
        )

    def check_all(self) -> list[DependencyStatus]:
        statuses = [self.check_wimlib()]
        if is_linux():
            statuses.append(self.check_xorriso())
        elif is_windows():
            statuses.append(self.check_oscdimg())
        return statuses

    def missing(self) -> list[DependencyStatus]:
        return [s for s in self.check_all() if not s.installed]

    def install_linux(self, *, confirm: bool = True) -> bool:
        if not confirm:
            self._log("Skipped Linux dependency installation (no confirmation).")
            return False

        distro = self.detect_linux_distro()
        self._log(f"Detected Linux distro: {distro}")

        if distro in ("arch", "manjaro"):
            cmd = ["sudo", "pacman", "-S", "--needed", "--noconfirm",
                   "wimlib", "xorriso", "ntfs-3g", "parted", "usbutils"]
        elif distro in ("debian", "ubuntu", "linuxmint", "pop"):
            cmd = ["sudo", "apt", "install", "-y",
                   "wimtools", "xorriso", "ntfs-3g", "parted", "usbutils"]
        elif distro in ("fedora", "rhel", "centos"):
            cmd = ["sudo", "dnf", "install", "-y",
                   "wimlib-utils", "xorriso", "ntfs-3g", "parted", "usbutils"]
        else:
            self._log(
                f"Unsupported distro '{distro}'. Install manually: wimlib, xorriso, ntfs-3g, parted."
            )
            return False

        self._log(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, check=False)
            return result.returncode == 0
        except FileNotFoundError as exc:
            self._log(f"Package manager not found: {exc}")
            return False

    def install_windows(self, *, confirm: bool = True) -> bool:
        if not confirm:
            self._log("Skipped Windows dependency installation (no confirmation).")
            return False

        adk_url = (
            "https://go.microsoft.com/fwlink/?linkid=2249370"
        )
        self._log(
            "Windows ADK is recommended for oscdimg.exe and DISM.\n"
            f"Download from Microsoft: {adk_url}\n"
            "Alternatively, place wimlib-imagex.exe in winiso_toolkit/tools/."
        )
        return False

    def install_missing(self, *, confirm: bool = True) -> bool:
        if not self.missing():
            return True
        if is_linux():
            return self.install_linux(confirm=confirm)
        if is_windows():
            return self.install_windows(confirm=confirm)
        return False


def ensure_dependencies(*, auto_install: bool = False, confirm: bool = True) -> DependencyInstaller:
    """Return installer after optional auto-install of missing deps."""
    installer = DependencyInstaller()
    if auto_install and installer.missing():
        installer.install_missing(confirm=confirm)
    return installer
