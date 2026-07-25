"""Rebuild bootable Windows ISO from extracted contents."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pycdlib

from winiso_toolkit.deps.installer import DependencyInstaller
from winiso_toolkit.iso.drivers import DriverInjector
from winiso_toolkit.iso.extract import extract_iso
from winiso_toolkit.iso.unattended import BypassOptions, UnattendedGenerator
from winiso_toolkit.utils.platform import is_linux, is_windows, run_command
from winiso_toolkit.utils.progress import ProgressCallback, clamp_progress


BOOT_WARNING = "No proposals available for boot related commands"


class ISOBuilder:
    """Extract source ISO, replace install image, rebuild with boot records."""

    def __init__(self, deps: DependencyInstaller | None = None) -> None:
        self.deps = deps or DependencyInstaller()

    def rebuild(
        self,
        source_iso: Path,
        output_iso: Path,
        *,
        new_install_image: Path | None = None,
        volume_label: str | None = None,
        bypass_options: BypassOptions | None = None,
        driver_dir: Path | None = None,
        progress: ProgressCallback | None = None,
    ) -> Path:
        source_iso = Path(source_iso)
        output_iso = Path(output_iso)
        work_dir = Path(tempfile.mkdtemp(prefix="winiso_build_"))

        try:
            if progress:
                progress(5, "Extracting source ISO…")
            self._extract_iso(source_iso, work_dir)

            if new_install_image:
                if progress:
                    progress(20, "Replacing install image…")
                self._replace_install_image(work_dir, new_install_image)

            if bypass_options:
                if progress:
                    progress(25, "Injecting autounattend.xml bypasses…")
                gen = UnattendedGenerator(bypass_options)
                gen.save(work_dir / "autounattend.xml")

            if driver_dir and Path(driver_dir).is_dir():
                if progress:
                    progress(30, "Injecting custom drivers…")
                injector = DriverInjector()
                injector.inject_drivers(work_dir, Path(driver_dir))

            label = volume_label or self._read_label(source_iso)
            if progress:
                progress(40, "Building bootable ISO…")

            if is_linux():
                self._build_xorriso(work_dir, output_iso, label, progress=progress)
            elif is_windows():
                self._build_oscdimg(work_dir, output_iso, label, progress=progress)
            else:
                raise RuntimeError("Unsupported platform for ISO building.")

            if progress:
                progress(90, "Validating boot record…")
            self._validate_boot_record(output_iso)

            if progress:
                progress(100, "ISO build complete.")
            return output_iso
        except Exception:
            output_iso.unlink(missing_ok=True)
            raise
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    def _extract_iso(self, iso_path: Path, dest: Path) -> None:
        extract_iso(iso_path, dest)

    def _replace_install_image(self, root: Path, new_image: Path) -> None:
        for sub in ("sources", "SOURCES"):
            target_dir = root / sub
            if not target_dir.is_dir():
                continue
            for old in ("install.wim", "install.esd", "INSTALL.WIM", "INSTALL.ESD"):
                old_path = target_dir / old
                if old_path.exists():
                    old_path.unlink()
            ext = new_image.suffix.lower()
            name = "install.esd" if ext == ".esd" else "install.wim"
            shutil.copy2(new_image, target_dir / name)
            return
        raise RuntimeError("sources/ directory not found in extracted ISO.")

    def _read_label(self, iso_path: Path) -> str:
        iso = pycdlib.PyCdlib()
        iso.open(str(iso_path))
        label = iso.volume_identifier().strip() if iso.volume_identifier() else ""
        iso.close()
        return label or "CCCOMA_X64FRE_EN-US_DV9"

    def _build_xorriso(
        self,
        source_dir: Path,
        output_iso: Path,
        volume_label: str,
        *,
        progress: ProgressCallback | None = None,
    ) -> None:
        xorriso = self.deps.check_xorriso()
        if not xorriso.installed or not xorriso.path:
            raise RuntimeError("xorriso is required on Linux.")

        args = [
            str(xorriso.path),
            "-as", "mkisofs",
            "-iso-level", "3",
            "-full-iso9660-filenames",
            "-J",
            "-joliet-long",
            "-r",
            "-V", volume_label,
            "-o", str(output_iso.resolve()),
            "-c", "boot/boot.cat",
            "-b", "boot/etfsboot.com",
            "-no-emul-boot",
            "-boot-load-size", "8",
            "-boot-info-table",
            "-eltorito-alt-boot",
            "-e", "efi/microsoft/boot/efisys.bin",
            "-no-emul-boot",
            "-isohybrid-gpt-basdat",
            ".",
        ]

        proc = subprocess.Popen(
            args,
            cwd=str(source_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        stdout, stderr = proc.communicate()
        combined = stdout + stderr

        if BOOT_WARNING in combined:
            raise RuntimeError(
                f"ISO build failed: boot record not created ({BOOT_WARNING}). "
                "Check that boot/etfsboot.com and efi/microsoft/boot/efisys.bin exist."
            )
        if proc.returncode != 0:
            raise RuntimeError(f"xorriso failed (exit {proc.returncode}): {stderr or stdout}")

        if progress:
            progress(85, "xorriso build finished.")

    def _build_oscdimg(
        self,
        source_dir: Path,
        output_iso: Path,
        volume_label: str,
        *,
        progress: ProgressCallback | None = None,
    ) -> None:
        oscdimg = self.deps.check_oscdimg()
        if not oscdimg.installed or not oscdimg.path:
            raise RuntimeError(
                "oscdimg.exe not found. Install Windows ADK Deployment Tools."
            )

        args = [
            str(oscdimg.path),
            "-m",
            "-o",
            "-u2",
            "-udfver102",
            "-bootdata:2#p0,e,b{}#pEF,e,b{}".format(
                "boot\\etfsboot.com",
                "efi\\microsoft\\boot\\efisys.bin",
            ),
            "-l", volume_label,
            ".",
            str(output_iso.resolve()),
        ]

        # Use cwd=source_dir so oscdimg resolves boot file paths correctly
        result = run_command(args, cwd=source_dir, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"oscdimg failed: {result.stderr or result.stdout}")

        if progress:
            progress(85, "oscdimg build finished.")

    def _validate_boot_record(self, iso_path: Path) -> None:
        xorriso = self.deps.check_xorriso()
        if xorriso.installed and xorriso.path and is_linux():
            result = run_command(
                [str(xorriso.path), "-indev", str(iso_path), "-report_el_torito", "plain"],
                check=False,
            )
            output = result.stdout + result.stderr
            if "El Torito" not in output and "boot" not in output.lower():
                raise RuntimeError("Built ISO has no valid El Torito boot record.")
            return

        # Windows fallback: check file size and basic readability
        iso = pycdlib.PyCdlib()
        try:
            iso.open(str(iso_path))
            iso.close()
        except Exception as exc:
            raise RuntimeError(f"Built ISO failed validation: {exc}") from exc
