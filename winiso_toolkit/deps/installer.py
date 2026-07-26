"""Detect and install missing external tools."""

from __future__ import annotations

import io
import platform
import re
import shutil
import subprocess
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

from winiso_toolkit.utils.platform import is_linux, is_windows, run_command, which

# wimlib 1.14.5 direct download URLs from wimlib.net (Windows binaries only)
_WIMLIB_VERSION = "1.14.5"
_WIMLIB_WINDOWS_URLS: dict[str, str] = {
    "x86_64":  f"https://wimlib.net/downloads/wimlib-{_WIMLIB_VERSION}-windows-x86_64-bin.zip",
    "i686":    f"https://wimlib.net/downloads/wimlib-{_WIMLIB_VERSION}-windows-i686-bin.zip",
    "aarch64": f"https://wimlib.net/downloads/wimlib-{_WIMLIB_VERSION}-windows-aarch64-bin.zip",
}

# Portable xorriso for Windows (Cygwin build — exe plus required runtime DLLs)
_XORRISO_WINDOWS_BASE = "https://raw.githubusercontent.com/PeyTy/xorriso-exe-for-windows/master"
_XORRISO_WINDOWS_FILES = ("xorriso.exe", "cygwin1.dll", "cygiconv-2.dll")

# Linux package names per distro family: (package_manager, packages)
_LINUX_PKGS: dict[str, tuple[list[str], list[str]]] = {
    # distro-id → (pkg_manager_cmd, packages)
    "arch":       (["sudo", "pacman", "-S", "--needed", "--noconfirm"],
                   ["wimlib", "xorriso", "ntfs-3g", "parted", "usbutils"]),
    "manjaro":    (["sudo", "pacman", "-S", "--needed", "--noconfirm"],
                   ["wimlib", "xorriso", "ntfs-3g", "parted", "usbutils"]),
    "endeavouros":(["sudo", "pacman", "-S", "--needed", "--noconfirm"],
                   ["wimlib", "xorriso", "ntfs-3g", "parted", "usbutils"]),
    "garuda":     (["sudo", "pacman", "-S", "--needed", "--noconfirm"],
                   ["wimlib", "xorriso", "ntfs-3g", "parted", "usbutils"]),
    "debian":     (["sudo", "apt", "install", "-y"],
                   ["wimtools", "xorriso", "ntfs-3g", "parted", "usbutils"]),
    "ubuntu":     (["sudo", "apt", "install", "-y"],
                   ["wimtools", "xorriso", "ntfs-3g", "parted", "usbutils"]),
    "linuxmint":  (["sudo", "apt", "install", "-y"],
                   ["wimtools", "xorriso", "ntfs-3g", "parted", "usbutils"]),
    "pop":        (["sudo", "apt", "install", "-y"],
                   ["wimtools", "xorriso", "ntfs-3g", "parted", "usbutils"]),
    "kali":       (["sudo", "apt", "install", "-y"],
                   ["wimtools", "xorriso", "ntfs-3g", "parted", "usbutils"]),
    "raspbian":   (["sudo", "apt", "install", "-y"],
                   ["wimtools", "xorriso", "ntfs-3g", "parted", "usbutils"]),
    "fedora":     (["sudo", "dnf", "install", "-y"],
                   ["wimlib-utils", "xorriso", "ntfs-3g", "parted", "usbutils"]),
    "rhel":       (["sudo", "dnf", "install", "-y"],
                   ["wimlib-utils", "xorriso", "ntfs-3g", "parted", "usbutils"]),
    "centos":     (["sudo", "dnf", "install", "-y"],
                   ["wimlib-utils", "xorriso", "ntfs-3g", "parted", "usbutils"]),
    "rocky":      (["sudo", "dnf", "install", "-y"],
                   ["wimlib-utils", "xorriso", "ntfs-3g", "parted", "usbutils"]),
    "almalinux":  (["sudo", "dnf", "install", "-y"],
                   ["wimlib-utils", "xorriso", "ntfs-3g", "parted", "usbutils"]),
    "opensuse-leap":    (["sudo", "zypper", "install", "-y"],
                         ["wimlib", "xorriso", "ntfs-3g", "parted", "usbutils"]),
    "opensuse-tumbleweed": (["sudo", "zypper", "install", "-y"],
                             ["wimlib", "xorriso", "ntfs-3g", "parted", "usbutils"]),
    "sles":       (["sudo", "zypper", "install", "-y"],
                   ["wimlib", "xorriso", "ntfs-3g", "parted", "usbutils"]),
    "alpine":     (["sudo", "apk", "add"],
                   ["wimlib", "xorriso", "ntfs-3g", "parted", "usbutils"]),
    "void":       (["sudo", "xbps-install", "-Sy"],
                   ["wimlib", "xorriso", "ntfs-3g", "parted", "eudev"]),
    "gentoo":     (["sudo", "emerge", "--ask=n"],
                   ["app-backup/wimlib", "dev-libs/libisoburn",
                    "sys-fs/ntfs3g", "sys-block/parted"]),
}


@dataclass
class DependencyStatus:
    name: str
    installed: bool
    path: Path | None = None
    message: str = ""


class DependencyInstaller:
    """Check and optionally install required external tools."""

    def __init__(self) -> None:
        self.wimlib_cmd: str = "wimlib-imagex"
        self.xorriso_cmd: str = "xorriso"
        self.oscdimg_cmd: str = "oscdimg"
        self.log: list[str] = []

    def _log(self, message: str) -> None:
        self.log.append(message)

    def _tools_dir(self) -> Path:
        return Path(__file__).resolve().parents[1] / "tools"

    def _verify_xorriso_executable(self, exe: Path) -> bool:
        """Return True when xorriso starts and responds to --version."""
        try:
            result = subprocess.run(
                [str(exe), "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                check=False,
            )
            return result.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False

    def _xorriso_windows_bundle_complete(self, tools_dir: Path) -> bool:
        return all((tools_dir / name).is_file() for name in _XORRISO_WINDOWS_FILES)

    def detect_linux_distro(self) -> str:
        """Return the distro ID from /etc/os-release, lower-cased."""
        os_release = Path("/etc/os-release")
        if not os_release.exists():
            return "unknown"
        content = os_release.read_text(encoding="utf-8", errors="replace")
        # Prefer ID_LIKE for derived distros (e.g. Pop!_OS → ubuntu)
        for key in ("ID", "ID_LIKE"):
            match = re.search(rf"^{key}=(.+)$", content, re.MULTILINE)
            if match:
                # ID_LIKE may be space-separated; take first value
                val = match.group(1).strip().strip('"').lower().split()[0]
                if val in _LINUX_PKGS:
                    return val
        # Return raw ID even if not in our table — caller handles unknown
        match = re.search(r"^ID=(.+)$", content, re.MULTILINE)
        return match.group(1).strip().strip('"').lower() if match else "unknown"

    # ------------------------------------------------------------------
    # Dependency checkers
    # ------------------------------------------------------------------

    def check_wimlib(self) -> DependencyStatus:
        """Find wimlib on PATH or in the bundled tools/ dir (Windows)."""
        for name in ("wimlib-imagex", "wimexport", "wiminfo"):
            path = which(name)
            if path:
                # Prefer invoking via the canonical multi-command binary name
                self.wimlib_cmd = "wimlib-imagex" if name == "wimexport" else name
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
        """Find xorriso on PATH or in the bundled tools/ dir (Windows)."""
        for name in ("xorriso", "xorriso.exe"):
            path = which(name)
            if path:
                self.xorriso_cmd = name
                return DependencyStatus(name="xorriso", installed=True, path=Path(path))
        if is_windows():
            bundled = self._tools_dir() / "xorriso.exe"
            if bundled.is_file() and self._verify_xorriso_executable(bundled):
                self.xorriso_cmd = str(bundled)
                return DependencyStatus(
                    name="xorriso",
                    installed=True,
                    path=bundled,
                    message="Using bundled xorriso.exe",
                )
            if bundled.is_file():
                return DependencyStatus(
                    name="xorriso",
                    installed=False,
                    path=bundled,
                    message=(
                        "Bundled xorriso.exe is incomplete or missing Cygwin DLLs. "
                        "It will be re-downloaded automatically."
                    ),
                )
        return DependencyStatus(
            name="xorriso",
            installed=False,
            message="xorriso not found. Install xorriso for ISO creation.",
        )

    def check_oscdimg(self) -> DependencyStatus:
        """Find oscdimg.exe — Windows ADK tool, Windows-only."""
        for candidate in (
            which("oscdimg"),
            Path(r"C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit"
                 r"\Deployment Tools\amd64\Oscdimg\oscdimg.exe"),
            Path(r"C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit"
                 r"\Deployment Tools\x86\Oscdimg\oscdimg.exe"),
        ):
            if candidate and Path(candidate).exists():
                self.oscdimg_cmd = str(candidate)
                return DependencyStatus(name="oscdimg", installed=True, path=Path(candidate))
        return DependencyStatus(
            name="oscdimg",
            installed=False,
            message="oscdimg not found. Install Windows ADK or install xorriso instead.",
        )

    def check_all(self) -> list[DependencyStatus]:
        """Return status of all required tools for the current platform."""
        statuses: list[DependencyStatus] = [self.check_wimlib()]
        if is_linux():
            # On Linux, xorriso is the ISO builder; oscdimg is not needed
            statuses.append(self.check_xorriso())
        elif is_windows():
            # On Windows, prefer oscdimg (ADK); xorriso is optional but accepted
            statuses.append(self.check_oscdimg())
            # If oscdimg is missing but xorriso is installed, that's still OK
            xorriso = self.check_xorriso()
            if not statuses[-1].installed and xorriso.installed:
                statuses[-1] = xorriso  # replace missing oscdimg with present xorriso
        else:
            # Other platforms (macOS etc.) — report xorriso only
            statuses.append(self.check_xorriso())
        return statuses

    def missing(self) -> list[DependencyStatus]:
        return [s for s in self.check_all() if not s.installed]

    # ------------------------------------------------------------------
    # Installation helpers
    # ------------------------------------------------------------------

    def install_linux(
        self,
        *,
        confirm: bool = True,
        progress_callback: object = None,
    ) -> bool:
        """Install all required deps using the distro's package manager."""

        def _progress(msg: str) -> None:
            self._log(msg)
            if callable(progress_callback):
                progress_callback(msg)  # type: ignore[call-arg]

        if not confirm:
            _progress("Skipped Linux dependency installation (no confirmation).")
            return False

        distro = self.detect_linux_distro()
        _progress(f"Detected Linux distro: {distro}")

        entry = _LINUX_PKGS.get(distro)
        if entry is None:
            _progress(
                f"Unsupported distro '{distro}'. "
                "Install manually: wimlib (or wimtools), xorriso, ntfs-3g, parted."
            )
            return False

        mgr_prefix, packages = entry
        cmd = mgr_prefix + packages
        _progress(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, check=False)
            if result.returncode == 0:
                _progress("Dependencies installed successfully.")
                return True
            _progress(f"Package manager exited with code {result.returncode}.")
            return False
        except FileNotFoundError as exc:
            _progress(f"Package manager not found: {exc}")
            return False

    def install_windows(
        self,
        *,
        confirm: bool = True,
        progress_callback: object = None,
    ) -> bool:
        """Install wimlib on Windows.

        Strategy (in order):
        1. winget install — fast, no UAC required
        2. Direct download from wimlib.net into tools/ — no admin rights needed
        """
        def _progress(msg: str) -> None:
            self._log(msg)
            if callable(progress_callback):
                progress_callback(msg)  # type: ignore[call-arg]

        if not confirm:
            _progress("Skipped Windows dependency installation (no confirmation).")
            return False

        if not self.missing():
            _progress("All required dependencies are already available.")
            return True

        # --- Strategy 1: winget ---
        winget = which("winget")
        if winget:
            _progress("Trying winget install Wimlib.Wimlib…")
            try:
                result = subprocess.run(
                    [winget, "install", "--id=Wimlib.Wimlib", "-e",
                     "--accept-source-agreements", "--accept-package-agreements"],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=120,
                )
                if result.returncode == 0:
                    _progress("wimlib installed via winget.")
                    if not self.missing():
                        return True
                else:
                    _progress(
                        f"winget returned exit {result.returncode}. "
                        "Falling back to direct download…"
                    )
            except (OSError, subprocess.TimeoutExpired) as exc:
                _progress(f"winget failed: {exc}. Falling back to direct download…")

        # --- Strategy 2: direct download ---
        ok_wim = self.check_wimlib().installed or self.install_wimlib_direct(progress_callback=progress_callback)
        ok_xor = (self.check_xorriso().installed or self.check_oscdimg().installed) or self.install_xorriso_direct(progress_callback=progress_callback)
        return self.check_wimlib().installed and (self.check_xorriso().installed or self.check_oscdimg().installed)

    def install_wimlib_direct(
        self,
        *,
        progress_callback: object = None,
    ) -> bool:
        """Download wimlib-imagex.exe from wimlib.net into tools/ (Windows only)."""
        def _progress(msg: str) -> None:
            self._log(msg)
            if callable(progress_callback):
                progress_callback(msg)  # type: ignore[call-arg]

        if is_linux():
            _progress(
                "Direct download is only for Windows. "
                "On Linux, use your package manager:\n"
                "  Debian/Ubuntu:  sudo apt install wimtools xorriso ntfs-3g parted\n"
                "  Arch/Manjaro:   sudo pacman -S wimlib xorriso ntfs-3g parted\n"
                "  Fedora/RHEL:    sudo dnf install wimlib-utils xorriso ntfs-3g parted\n"
                "  openSUSE:       sudo zypper install wimlib xorriso ntfs-3g parted\n"
                "  Alpine:         sudo apk add wimlib xorriso ntfs-3g parted\n"
                "Or run: winiso-toolkit --install-deps"
            )
            return False

        if not is_windows():
            _progress("Direct download is not supported on this platform.")
            return False

        # Detect Windows CPU architecture
        machine = platform.machine().lower()
        if machine in ("amd64", "x86_64"):
            arch = "x86_64"
        elif machine in ("arm64", "aarch64"):
            arch = "aarch64"
        else:
            arch = "i686"

        url = _WIMLIB_WINDOWS_URLS[arch]
        tools_dir = Path(__file__).resolve().parents[1] / "tools"
        tools_dir.mkdir(parents=True, exist_ok=True)
        dest_exe = tools_dir / "wimlib-imagex.exe"

        _progress(f"Downloading wimlib {_WIMLIB_VERSION} ({arch}) from wimlib.net…")

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "WinISO-Toolkit/1.0"})
            with urllib.request.urlopen(req, timeout=60) as response:
                data = response.read()

            _progress(f"Downloaded {len(data) // 1024} KB — extracting…")

            # Two-pass: first extract exe, then DLLs (ZipFile can't rewind)
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                exe_names = [n for n in zf.namelist()
                             if n.lower().endswith("wimlib-imagex.exe")]
                if not exe_names:
                    _progress("ERROR: wimlib-imagex.exe not found inside zip.")
                    return False
                with zf.open(exe_names[0]) as src, open(dest_exe, "wb") as dst:
                    dst.write(src.read())

                dll_names = [n for n in zf.namelist() if n.lower().endswith(".dll")]
                for dll in dll_names:
                    dll_dest = tools_dir / Path(dll).name
                    with zf.open(dll) as src, open(dll_dest, "wb") as dst:
                        dst.write(src.read())

            _progress(f"Extracted {1 + len(dll_names)} files to {tools_dir}")
            self.wimlib_cmd = str(dest_exe)
            _progress("wimlib-imagex.exe installed successfully.")
            return True

        except urllib.error.URLError as exc:
            _progress(f"Download failed: {exc}. Check internet connection.")
        except (zipfile.BadZipFile, OSError, KeyError) as exc:
            _progress(f"Extraction failed: {exc}")
            dest_exe.unlink(missing_ok=True)

        return False

    def install_xorriso_direct(
        self,
        *,
        progress_callback: object = None,
    ) -> bool:
        """Download portable xorriso (exe + Cygwin DLLs) into tools/ (Windows only)."""
        def _progress(msg: str) -> None:
            self._log(msg)
            if callable(progress_callback):
                progress_callback(msg)  # type: ignore[call-arg]

        if not is_windows():
            return False

        tools_dir = self._tools_dir()
        tools_dir.mkdir(parents=True, exist_ok=True)
        dest_exe = tools_dir / "xorriso.exe"

        if self._xorriso_windows_bundle_complete(tools_dir) and self._verify_xorriso_executable(dest_exe):
            self.xorriso_cmd = str(dest_exe)
            return True

        total = len(_XORRISO_WINDOWS_FILES)
        _progress("Downloading portable xorriso for Windows (exe + runtime DLLs)…")

        try:
            for index, filename in enumerate(_XORRISO_WINDOWS_FILES, start=1):
                url = f"{_XORRISO_WINDOWS_BASE}/{filename}"
                _progress(f"Downloading {filename} ({index}/{total})…")
                req = urllib.request.Request(url, headers={"User-Agent": "WinISO-Toolkit/1.0"})
                with urllib.request.urlopen(req, timeout=120) as response:
                    data = response.read()
                with open(tools_dir / filename, "wb") as dst:
                    dst.write(data)

            if not self._verify_xorriso_executable(dest_exe):
                _progress(
                    "xorriso verification failed after download. "
                    "Install Windows ADK (oscdimg.exe) or a full xorriso build manually."
                )
                for filename in _XORRISO_WINDOWS_FILES:
                    (tools_dir / filename).unlink(missing_ok=True)
                return False

            self.xorriso_cmd = str(dest_exe)
            _progress("Portable xorriso installed successfully.")
            return True
        except Exception as exc:
            _progress(f"xorriso download failed: {exc}")
            for filename in _XORRISO_WINDOWS_FILES:
                (tools_dir / filename).unlink(missing_ok=True)
            return False

    def install_missing(
        self,
        *,
        confirm: bool = True,
        progress_callback: object = None,
    ) -> bool:
        """Install all missing dependencies for the current platform."""
        if not self.missing():
            return True
        if is_linux():
            return self.install_linux(confirm=confirm, progress_callback=progress_callback)
        if is_windows():
            return self.install_windows(confirm=confirm, progress_callback=progress_callback)
        # Other platforms (macOS, BSD…) — guide the user
        if callable(progress_callback):
            progress_callback(  # type: ignore[call-arg]
                "Automatic installation is not supported on this platform.\n"
                "Install manually:\n"
                "  macOS (Homebrew): brew install wimlib xorriso\n"
                "  FreeBSD (pkg):    pkg install wimlib xorriso ntfs-3g"
            )
        return False


def ensure_dependencies(*, auto_install: bool = False, confirm: bool = True) -> DependencyInstaller:
    """Return installer after optional auto-install of missing deps."""
    installer = DependencyInstaller()
    if auto_install and installer.missing():
        installer.install_missing(confirm=confirm)
    return installer
