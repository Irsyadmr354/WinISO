"""Read and validate Windows installer ISOs using pycdlib."""

from __future__ import annotations

import logging
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import pycdlib
import pycdlib.pycdlibexception

from winiso_toolkit.deps.installer import DependencyInstaller
from winiso_toolkit.utils.platform import run_command, which

_log = logging.getLogger(__name__)


@dataclass
class WIMImageInfo:
    index: int
    name: str
    description: str
    size_bytes: int
    display_name: str = ""

    def __post_init__(self) -> None:
        if not self.display_name:
            self.display_name = self.name or self.description or f"Image {self.index}"


@dataclass
class ISOInfo:
    path: Path
    volume_label: str
    is_windows_installer: bool
    install_image_path: str | None = None
    install_image_size: int = 0
    wim_images: list[WIMImageInfo] = field(default_factory=list)
    total_iso_size: int = 0
    extracted_wim_path: Path | None = None
    wimlib_missing: bool = False  # True when wimlib is absent; editions cannot be listed

    @property
    def estimated_compressed_size(self) -> int:
        """Estimate LZMS ESD size (~45% of selected WIM data)."""
        if self.install_image_size:
            return int(self.install_image_size * 0.45)
        return int(self.total_iso_size * 0.45)


class ISOAnalyzer:
    """Analyze Windows ISO files without mounting."""

    WIM_PATHS = (
        "sources/install.wim",       # UDF (case-sensitive lowercase — Windows 11)
        "SOURCES/INSTALL.WIM",       # ISO9660 uppercase
        "/SOURCES/INSTALL.WIM;1",    # ISO9660 with version suffix
    )
    ESD_PATHS = (
        "sources/install.esd",       # UDF (case-sensitive lowercase)
        "SOURCES/INSTALL.ESD",       # ISO9660 uppercase
        "/SOURCES/INSTALL.ESD;1",    # ISO9660 with version suffix
    )

    def __init__(self, deps: DependencyInstaller | None = None) -> None:
        self.deps = deps or DependencyInstaller()

    def analyze(self, iso_path: Path, *, keep_wim: bool = False) -> ISOInfo:
        """Analyze ISO.

        Args:
            iso_path: Path to the ISO file.
            keep_wim: If True, keep the extracted install image on disk and
                store its path in ``info.extracted_wim_path`` so the caller
                can reuse it (avoids double-extraction in the pipeline).
        """
        iso_path = Path(iso_path).resolve()
        if not iso_path.is_file():
            raise FileNotFoundError(f"ISO file not found: {iso_path}")

        volume_label = self._read_volume_label(iso_path)
        install_path = self._find_install_image(iso_path)

        info = ISOInfo(
            path=iso_path,
            volume_label=volume_label,
            is_windows_installer=install_path is not None,
            install_image_path=install_path,
            total_iso_size=iso_path.stat().st_size,
        )

        if install_path:
            wim_local = self._extract_install_image(iso_path, install_path)
            try:
                info.install_image_size = wim_local.stat().st_size
                try:
                    info.wim_images = self._read_wim_metadata(wim_local)
                except _WimlibMissingError:
                    # wimlib not installed — ISO is still valid, editions unknown
                    info.wimlib_missing = True
                    _log.warning(
                        "wimlib is not installed; cannot enumerate editions. "
                        "Install wimlib (run --install-deps) to see edition list."
                    )
            except (OSError, RuntimeError, ValueError):
                if wim_local.parent.name.startswith("winiso_extract_"):
                    shutil.rmtree(wim_local.parent, ignore_errors=True)
                raise

            if keep_wim:
                info.extracted_wim_path = wim_local
            else:
                if wim_local.parent.name.startswith("winiso_extract_"):
                    shutil.rmtree(wim_local.parent, ignore_errors=True)

        return info

    def _read_volume_label(self, iso_path: Path) -> str:
        try:
            iso = pycdlib.PyCdlib()
            try:
                iso.open(str(iso_path))
                raw_label: bytes | None = iso.pvd.volume_identifier
                label = raw_label.decode("ascii", errors="replace").strip() if raw_label else ""
            finally:
                iso.close()
            if label:
                return label
        except (pycdlib.pycdlibexception.PyCdlibException, OSError, UnicodeDecodeError):
            pass

        xorriso = self.deps.check_xorriso()
        if xorriso.installed and xorriso.path:
            try:
                result = run_command(
                    [str(xorriso.path), "-indev", str(iso_path), "-pvd_info"],
                    check=False,
                )
                for line in (result.stdout + result.stderr).splitlines():
                    if "Volume id" in line or "Volume Id" in line:
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            return parts[1].strip().strip("'\"")
            except (OSError, ValueError):
                pass

        _log.warning(
            "No volume label found on ISO; falling back to generic label 'WINISO'."
        )
        return "WINISO"

    def _find_install_image(self, iso_path: Path) -> str | None:
        iso = pycdlib.PyCdlib()
        try:
            iso.open(str(iso_path))
            try:
                for candidate in (*self.WIM_PATHS, *self.ESD_PATHS):
                    norm = candidate.replace("\\", "/")
                    if self._iso_has_file(iso, norm):
                        return re.sub(r";\d+$", "", norm).lstrip("/")

                # Fallback: walk directory tree case-insensitively
                # Priority: UDF > Joliet > ISO9660
                try:
                    if iso.has_udf():
                        walk_iter = iso.walk(udf_path="/")
                    elif iso.has_joliet():
                        walk_iter = iso.walk(joliet_path="/")
                    else:
                        walk_iter = iso.walk(iso_path="/")
                    for current, _dirs, files in walk_iter:
                        for f in files:
                            clean_name = re.sub(r";\d+$", "", f).lower()
                            if clean_name in ("install.wim", "install.esd"):
                                full_path = f"{current}/{f}".replace("//", "/").lstrip("/")
                                return re.sub(r";\d+$", "", full_path)
                except (AttributeError, NotImplementedError, RuntimeError):
                    pass
            finally:
                iso.close()
        except (pycdlib.pycdlibexception.PyCdlibException, OSError, ValueError) as exc:
            raise ValueError(f"Unable to read ISO (corrupted or invalid): {exc}") from exc
        return None

    def _iso_has_file(self, iso: pycdlib.PyCdlib, iso_path: str) -> bool:
        """Check whether a file exists inside the ISO without extracting it.

        Tries UDF (preferred for modern Windows ISOs), then Joliet, then
        plain ISO9660 — including the ISO9660 version suffix variant (;1).
        """
        path = iso_path if iso_path.startswith("/") else f"/{iso_path}"
        path_lower = path.lower()

        # UDF: case-sensitive lowercase paths (modern Windows 11 ISOs are UDF-only)
        if iso.has_udf():
            try:
                iso.get_record(udf_path=path_lower)
                return True
            except (pycdlib.pycdlibexception.PyCdlibException, AttributeError):
                pass

        # Joliet: case-preserved mixed paths
        if iso.has_joliet():
            try:
                iso.get_record(joliet_path=path)
                return True
            except (pycdlib.pycdlibexception.PyCdlibException, AttributeError):
                pass

        # ISO9660: uppercase + optional version suffix
        for variant in (path.upper(), f"{path.upper()};1"):
            try:
                iso.get_record(iso_path=variant)
                return True
            except (pycdlib.pycdlibexception.PyCdlibException, AttributeError):
                pass

        return False

    def _extract_install_image(self, iso_path: Path, install_path: str) -> Path:
        tmp = Path(tempfile.mkdtemp(prefix="winiso_extract_"))
        out = tmp / Path(install_path).name
        iso = pycdlib.PyCdlib()
        try:
            iso.open(str(iso_path))
            extracted = False
            try:
                # UDF first — modern Windows 11 ISOs are UDF-only (no Joliet)
                if iso.has_udf():
                    try:
                        udf_p = f"/{install_path.lower()}"
                        iso.get_file_from_iso(local_path=str(out), udf_path=udf_p)
                        extracted = out.exists() and out.stat().st_size > 0
                    except (pycdlib.pycdlibexception.PyCdlibException, OSError):
                        pass

                # Joliet next
                if not extracted and iso.has_joliet():
                    try:
                        iso.get_file_from_iso(local_path=str(out), joliet_path=f"/{install_path}")
                        extracted = out.exists() and out.stat().st_size > 0
                    except (pycdlib.pycdlibexception.PyCdlibException, OSError):
                        pass

                # ISO9660 fallback (uppercase + optional ;1 suffix)
                if not extracted:
                    for variant in (
                        f"/{install_path.upper()}",
                        f"/{install_path.upper()};1",
                        f"/{install_path}",
                    ):
                        try:
                            iso.get_file_from_iso(local_path=str(out), iso_path=variant)
                            if out.exists() and out.stat().st_size > 0:
                                extracted = True
                                break
                        except (pycdlib.pycdlibexception.PyCdlibException, OSError):
                            pass
            finally:
                iso.close()

            if not extracted or not out.exists() or out.stat().st_size == 0:
                raise ValueError("Install image appears empty or unreadable.")
            return out
        except (pycdlib.pycdlibexception.PyCdlibException, OSError, ValueError):
            shutil.rmtree(tmp, ignore_errors=True)
            raise

    def _read_wim_metadata(self, wim_path: Path) -> list[WIMImageInfo]:
        wimlib = self.deps.check_wimlib()

        # --- Windows built-in DISM fallback ---
        # DISM is available on every Windows installation; try it before
        # requiring the user to install wimlib.
        if not wimlib.installed:
            dism_images = self._read_wim_metadata_dism(wim_path)
            if dism_images:
                return dism_images
            # DISM also unavailable (e.g. running on Linux without wimlib)
            raise _WimlibMissingError(
                "wimlib is not installed and DISM is unavailable. "
                "Run --install-deps or install wimlib manually."
            )

        cmd = self.deps.wimlib_cmd
        if Path(cmd).suffix.lower() == ".exe":
            info_args = [cmd, "info", str(wim_path)]
        else:
            info_args = ["wiminfo", str(wim_path)] if which("wiminfo") else [cmd, "info", str(wim_path)]

        result = run_command(info_args, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"wiminfo failed: {result.stderr or result.stdout}")

        return parse_wiminfo_output(result.stdout, wim_path.stat().st_size)

    def _read_wim_metadata_dism(self, wim_path: Path) -> list[WIMImageInfo]:
        """Try DISM /Get-WimInfo as a no-extra-install fallback (Windows only).

        On Linux, DISM does not exist — return immediately instead of
        wasting time searching PATH for a tool that will never be there.
        """
        from winiso_toolkit.utils.platform import is_windows
        if not is_windows():
            return []

        dism: str | Path | None = which("dism")
        if not dism:
            # dism.exe lives at a fixed path on every Windows installation
            dism_fixed = Path(r"C:\Windows\System32\dism.exe")
            if dism_fixed.exists():
                dism = dism_fixed

        if not dism:
            return []

        try:
            result = run_command(
                [str(dism), "/Get-WimInfo", f"/WimFile:{wim_path}"],
                check=False,
            )
        except OSError:
            return []

        if result.returncode != 0:
            return []

        return _parse_dism_wiminfo(result.stdout, wim_path.stat().st_size)


class _WimlibMissingError(RuntimeError):
    """Raised when neither wimlib nor DISM can read WIM metadata."""


def _parse_dism_wiminfo(text: str, total_size: int) -> list[WIMImageInfo]:
    """Parse ``dism /Get-WimInfo`` output into WIMImageInfo list.

    DISM output looks like::

        Index : 1
        Name : Windows 11 Home
        Description : Windows 11 Home
        Size : 16,212,860,032 bytes
    """
    images: list[WIMImageInfo] = []
    current_index = 0
    name = ""
    description = ""
    size = 0

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("Index :"):
            if current_index:
                images.append(WIMImageInfo(
                    index=current_index,
                    name=name,
                    description=description,
                    size_bytes=size or (total_size // max(len(images) + 1, 1)),
                ))
            try:
                current_index = int(stripped.split(":", 1)[1].strip())
            except ValueError:
                pass
            name = ""
            description = ""
            size = 0
        elif stripped.startswith("Name :"):
            name = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Description :"):
            description = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Size :"):
            # "16,212,860,032 bytes"
            raw = stripped.split(":", 1)[1].strip().split()[0].replace(",", "")
            try:
                size = int(raw)
            except ValueError:
                pass

    if current_index:
        images.append(WIMImageInfo(
            index=current_index,
            name=name,
            description=description,
            size_bytes=size or (total_size // max(len(images) + 1, 1)),
        ))

    return images


def parse_wiminfo_output(text: str, total_size: int) -> list[WIMImageInfo]:
    """Parse wiminfo / wimlib-imagex info output."""
    images: list[WIMImageInfo] = []
    current_index = 0
    name = ""
    description = ""
    size = 0

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("Index:"):
            if current_index:
                images.append(
                    WIMImageInfo(
                        index=current_index,
                        name=name,
                        description=description,
                        size_bytes=size or (total_size // max(len(images) + 1, 1)),
                    )
                )
            current_index = int(stripped.split(":", 1)[1].strip())
            name = ""
            description = ""
            size = 0
        elif stripped.startswith("Name:"):
            name = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Description:"):
            description = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Total Bytes:"):
            try:
                size = int(stripped.split(":", 1)[1].strip().replace(",", ""))
            except ValueError:
                pass

    if current_index:
        images.append(
            WIMImageInfo(
                index=current_index,
                name=name,
                description=description,
                size_bytes=size or (total_size // max(len(images) + 1, 1)),
            )
        )

    if not images:
        images.append(WIMImageInfo(index=1, name="Windows", description="Default", size_bytes=total_size))

    return images
