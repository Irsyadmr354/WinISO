"""High-level workflow orchestration."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from winiso_toolkit.deps.installer import DependencyInstaller
from winiso_toolkit.iso.analyzer import ISOAnalyzer
from winiso_toolkit.iso.builder import ISOBuilder
from winiso_toolkit.iso.compressor import WIMCompressor
from winiso_toolkit.iso.unattended import BypassOptions
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
    ) -> Path:
        iso_path = Path(iso_path)
        output_iso = Path(output_iso)
        work = Path(tempfile.mkdtemp(prefix="winiso_pipeline_"))
        wim_path: Path | None = None

        try:
            if progress:
                progress(0, "Analyzing ISO…")
            # Use keep_wim=True so the extracted install image is kept for
            # compression — avoids extracting the multi-GB WIM file twice.
            info = self.analyzer.analyze(iso_path, keep_wim=True)
            wim_path = getattr(info, "extracted_wim_path", None)
            if not info.is_windows_installer:
                raise ValueError("Not a valid Windows installer ISO (no install.wim/esd found).")
            if wim_path is None:
                raise ValueError("Failed to extract install image from ISO.")

            esd_path = work / "install.esd"
            if progress:
                progress(10, "Compressing selected editions…")
            self.compressor.compress(wim_path, esd_path, indices, progress=_scale_progress(progress, 10, 70))

            if progress:
                progress(75, "Rebuilding bootable ISO…")
            return self.builder.rebuild(
                iso_path,
                output_iso,
                new_install_image=esd_path,
                volume_label=info.volume_label,
                bypass_options=bypass_options,
                driver_dir=driver_dir,
                progress=_scale_progress(progress, 75, 100),
            )
        except Exception:
            output_iso.unlink(missing_ok=True)
            raise
        finally:
            # Clean up the extracted WIM kept from analysis
            if wim_path and wim_path.exists():
                parent = wim_path.parent
                if parent.name.startswith("winiso_extract_"):
                    shutil.rmtree(parent, ignore_errors=True)
            shutil.rmtree(work, ignore_errors=True)


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
