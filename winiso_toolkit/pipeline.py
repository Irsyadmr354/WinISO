"""High-level workflow orchestration."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from winiso_toolkit.deps.installer import DependencyInstaller
from winiso_toolkit.iso.analyzer import ISOAnalyzer
from winiso_toolkit.iso.builder import ISOBuilder
from winiso_toolkit.iso.compressor import WIMCompressor
from winiso_toolkit.iso.debloat import DebloatOptions, WIMDebloater
from winiso_toolkit.iso.extract import extract_iso
from winiso_toolkit.iso.pebuilder import WinPERescueBuilder
from winiso_toolkit.iso.unattended import BypassOptions, UnattendedGenerator
from winiso_toolkit.iso.updates import UpdateSlipstreamer
from winiso_toolkit.iso.winpe import WinPEInjector
from winiso_toolkit.utils.progress import ProgressCallback


class WinISOPipeline:
    """End-to-end compress-and-rebuild workflow."""

    def __init__(self, deps: DependencyInstaller | None = None) -> None:
        self.deps = deps or DependencyInstaller()
        self.analyzer = ISOAnalyzer(self.deps)
        self.compressor = WIMCompressor(self.deps)
        self.builder = ISOBuilder(self.deps)

    def compress_iso(
        self,
        iso_path: Path,
        output_iso: Path,
        indices: list[int],
        *,
        bypass_options: BypassOptions | None = None,
        driver_dir: Path | None = None,
        progress: ProgressCallback | None = None,
        debloat: bool = False,
        debloat_options: DebloatOptions | None = None,
        updates_dir: Path | None = None,
        inject_winpe_tools: bool = False,
        build_pe_rescue: bool = False,
    ) -> Path:
        iso_path = Path(iso_path)
        output_iso = Path(output_iso)
        work = Path(tempfile.mkdtemp(prefix="winiso_pipeline_"))
        extract_dir = work / "iso_root"
        wim_path: Path | None = None

        try:
            if progress:
                progress(0, "Analyzing ISO…")
            # Extract only install.wim/esd once for compression metadata.
            info = self.analyzer.analyze(iso_path, keep_wim=True)
            wim_path = info.extracted_wim_path
            if not info.is_windows_installer:
                raise ValueError("Not a valid Windows installer ISO (no install.wim/esd found).")
            if wim_path is None:
                raise ValueError("Failed to extract install image from ISO.")

            esd_path = work / "install.esd"
            if progress:
                progress(10, "Compressing selected editions…")

            # indices=[0] means "keep all editions" (set when wimlib is missing)
            keep_all = indices == [0]
            if keep_all:
                # No wimlib — copy the original WIM as-is, skip ESD compression
                if progress:
                    progress(10, "wimlib not available — copying install image as-is…")
                esd_path = work / wim_path.name  # keep original extension
                shutil.copy2(wim_path, esd_path)
                if progress:
                    progress(55, "Install image copied.")
            else:
                self.compressor.compress(
                    wim_path,
                    esd_path,
                    indices,
                    progress=_scale_progress(progress, 10, 55),
                )

            if progress:
                progress(58, "Extracting source ISO (single pass)…")
            extract_iso(iso_path, extract_dir)

            if progress:
                progress(65, "Replacing install image…")
            self.builder._replace_install_image(extract_dir, esd_path)

            if bypass_options:
                if progress:
                    progress(68, "Injecting autounattend.xml bypasses…")
                UnattendedGenerator(bypass_options).save(extract_dir / "autounattend.xml")

            if driver_dir and Path(driver_dir).is_dir():
                if progress:
                    progress(70, "Injecting custom drivers…")
                from winiso_toolkit.iso.drivers import DriverInjector

                DriverInjector().inject_drivers(extract_dir, Path(driver_dir))

            if debloat or updates_dir or inject_winpe_tools or build_pe_rescue:
                self._apply_extras_to_dir(
                    extract_dir,
                    debloat=debloat,
                    debloat_options=debloat_options,
                    updates_dir=updates_dir,
                    inject_winpe_tools=inject_winpe_tools,
                    build_pe_rescue=build_pe_rescue,
                )

            if progress:
                progress(80, "Building bootable ISO…")
            final_iso = self.builder.build_from_dir(
                extract_dir,
                output_iso,
                info.volume_label,
                progress=_scale_progress(progress, 80, 95),
            )

            if progress:
                progress(100, "Done.")
            return final_iso
        except Exception:
            if output_iso.resolve() != iso_path.resolve():
                output_iso.unlink(missing_ok=True)
            raise
        finally:
            if wim_path and wim_path.exists():
                parent = wim_path.parent
                if parent.name.startswith("winiso_extract_"):
                    shutil.rmtree(parent, ignore_errors=True)
            shutil.rmtree(work, ignore_errors=True)

    def _apply_extras_to_dir(
        self,
        extract_dir: Path,
        *,
        debloat: bool,
        debloat_options: DebloatOptions | None,
        updates_dir: Path | None,
        inject_winpe_tools: bool,
        build_pe_rescue: bool,
    ) -> None:
        """Apply optional post-processing directly to an extracted ISO tree."""
        if debloat:
            debloater = WIMDebloater(debloat_options)
            debloat_target = extract_dir / "sources" / "$OEM$" / "$1" / "WinISO"
            debloater.generate_debloat_script(debloat_target)

        if updates_dir:
            UpdateSlipstreamer().copy_updates_to_iso(extract_dir, Path(updates_dir))

        if inject_winpe_tools:
            WinPEInjector().inject_winpe_cmd_shortcut(extract_dir)

        if build_pe_rescue:
            WinPERescueBuilder().build_rescue_media(extract_dir)


def _scale_progress(
    callback: ProgressCallback | None,
    start: float,
    end: float,
) -> ProgressCallback | None:
    if not callback:
        return None

    def scaled(percent: float, message: str) -> None:
        overall = start + (percent / 100.0) * (end - start)
        callback(overall, message)

    return scaled
