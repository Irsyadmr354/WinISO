"""Read and validate Windows installer ISOs using pycdlib."""

from __future__ import annotations

import re
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import pycdlib

from winiso_toolkit.deps.installer import DependencyInstaller
from winiso_toolkit.utils.platform import run_command


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

    @property
    def estimated_compressed_size(self) -> int:
        """Estimate LZMS ESD size (~45% of selected WIM data)."""
        if self.install_image_size:
            return int(self.install_image_size * 0.45)
        return int(self.total_iso_size * 0.45)


class ISOAnalyzer:
    """Analyze Windows ISO files without mounting."""

    WIM_PATHS = (
        "sources/install.wim",
        "SOURCES/INSTALL.WIM",
        "/SOURCES/INSTALL.WIM;1",
    )
    ESD_PATHS = (
        "sources/install.esd",
        "SOURCES/INSTALL.ESD",
        "/SOURCES/INSTALL.ESD;1",
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
                info.wim_images = self._read_wim_metadata(wim_local)
            except Exception:
                if wim_local.parent.name.startswith("winiso_extract_"):
                    shutil.rmtree(wim_local.parent, ignore_errors=True)
                raise

            if keep_wim:
                # Caller is responsible for cleanup
                info.extracted_wim_path = wim_local  # type: ignore[attr-defined]
            else:
                if wim_local.parent.name.startswith("winiso_extract_"):
                    shutil.rmtree(wim_local.parent, ignore_errors=True)

        return info

    def _read_volume_label(self, iso_path: Path) -> str:
        try:
            iso = pycdlib.PyCdlib()
            iso.open(str(iso_path))
            label = iso.volume_identifier().strip() if iso.volume_identifier() else ""
            iso.close()
            if label:
                return label
        except Exception:
            pass

        xorriso = self.deps.check_xorriso()
        if xorriso.installed and xorriso.path:
            try:
                result = run_command(
                    [str(xorriso.path), "-indev", str(iso_path), "-report_system_area", "plain"],
                    check=False,
                )
                for line in (result.stdout + result.stderr).splitlines():
                    if "Volume id" in line or "Volume Id" in line:
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            return parts[1].strip().strip("'\"")
            except Exception:
                pass

        return "CCCOMA_X64FRE_EN-US_DV9"

    def _find_install_image(self, iso_path: Path) -> str | None:
        iso = pycdlib.PyCdlib()
        try:
            iso.open(str(iso_path))
            for candidate in (*self.WIM_PATHS, *self.ESD_PATHS):
                norm = candidate.replace("\\", "/")
                if self._iso_has_file(iso, norm):
                    clean = re.sub(r";\d+$", "", norm).lstrip("/")
                    iso.close()
                    return clean

            # Fallback: walk directory tree case-insensitively
            try:
                walk_iter = iso.walk(joliet_path="/") if iso.has_joliet() else iso.walk(iso_path="/")
                for current, _dirs, files in walk_iter:
                    for f in files:
                        clean_name = re.sub(r";\d+$", "", f).lower()
                        if clean_name in ("install.wim", "install.esd"):
                            full_path = f"{current}/{f}".replace("//", "/").lstrip("/")
                            clean_full_path = re.sub(r";\d+$", "", full_path)
                            iso.close()
                            return clean_full_path
            except Exception:
                pass

            iso.close()
        except Exception as exc:
            raise ValueError(f"Unable to read ISO (corrupted or invalid): {exc}") from exc
        return None

    def _iso_has_file(self, iso: pycdlib.PyCdlib, iso_path: str) -> bool:
        """Check whether a file exists inside the ISO without extracting it."""
        path = iso_path if iso_path.startswith("/") else f"/{iso_path}"

        for variant in (path, path.upper(), f"{path.upper()};1"):
            try:
                iso.get_record(iso_path=variant)
                return True
            except Exception:
                pass

        if iso.has_joliet():
            try:
                iso.get_record(joliet_path=path)
                return True
            except Exception:
                pass

        return False

    def _extract_install_image(self, iso_path: Path, install_path: str) -> Path:
        tmp = Path(tempfile.mkdtemp(prefix="winiso_extract_"))
        out = tmp / Path(install_path).name
        iso = pycdlib.PyCdlib()
        iso.open(str(iso_path))

        extracted = False
        if iso.has_joliet():
            try:
                iso.get_file_from_iso(local_path=str(out), joliet_path=f"/{install_path}")
                extracted = out.exists() and out.stat().st_size > 0
            except Exception:
                pass

        if not extracted:
            for variant in (f"/{install_path}", f"/{install_path.upper()}", f"/{install_path.upper()};1"):
                try:
                    iso.get_file_from_iso(local_path=str(out), iso_path=variant)
                    if out.exists() and out.stat().st_size > 0:
                        extracted = True
                        break
                except Exception:
                    pass

        iso.close()
        if not extracted or out.stat().st_size == 0:
            raise ValueError("Install image appears empty or unreadable.")
        return out

    def _read_wim_metadata(self, wim_path: Path) -> list[WIMImageInfo]:
        wimlib = self.deps.check_wimlib()
        if not wimlib.installed:
            raise RuntimeError(
                "wimlib is required to read WIM metadata. "
                "Run with --install-deps or install wimlib manually."
            )

        cmd = self.deps.wimlib_cmd
        if Path(cmd).suffix.lower() == ".exe":
            info_args = [cmd, "info", str(wim_path)]
        else:
            info_args = ["wiminfo", str(wim_path)] if which_simple("wiminfo") else [cmd, "info", str(wim_path)]

        result = run_command(info_args, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"wiminfo failed: {result.stderr or result.stdout}")

        return parse_wiminfo_output(result.stdout, wim_path.stat().st_size)


def which_simple(name: str) -> bool:
    import shutil
    return shutil.which(name) is not None


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
                size_bytes=size or (total_size // max(len(images), 1)),
            )
        )

    if not images:
        images.append(WIMImageInfo(index=1, name="Windows", description="Default", size_bytes=total_size))

    return images
