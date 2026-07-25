"""Compress WIM/ESD images with wimlib."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from winiso_toolkit.deps.installer import DependencyInstaller
from winiso_toolkit.utils.platform import is_windows, run_command
from winiso_toolkit.utils.progress import ProgressCallback, clamp_progress


class WIMCompressor:
    """Export selected WIM indices to LZMS-compressed ESD."""

    LZMS_RATIO = 0.45

    def __init__(self, deps: DependencyInstaller | None = None) -> None:
        self.deps = deps or DependencyInstaller()

    def estimate_size(self, source_size: int, num_indices: int = 1) -> int:
        return int(source_size * self.LZMS_RATIO * num_indices / max(num_indices, 1))

    def compress(
        self,
        source_wim: Path,
        dest_esd: Path,
        indices: list[int],
        *,
        progress: ProgressCallback | None = None,
    ) -> Path:
        wimlib = self.deps.check_wimlib()
        if not wimlib.installed:
            raise RuntimeError("wimlib is not installed.")

        dest_esd = Path(dest_esd)
        dest_esd.parent.mkdir(parents=True, exist_ok=True)
        work_dir = Path(tempfile.mkdtemp(prefix="winiso_compress_"))

        try:
            if len(indices) == 1:
                return self._export_single(source_wim, dest_esd, indices[0], progress=progress)

            partial: list[Path] = []
            for i, index in enumerate(indices):
                part = work_dir / f"part_{index}.esd"
                actual = self._export_single(
                    source_wim,
                    part,
                    index,
                    progress=lambda p, m: self._multi_progress(progress, i, len(indices), p, m),
                )
                partial.append(actual)

            return self._join_images(partial, dest_esd, progress=progress)
        except Exception:
            if dest_esd.exists():
                dest_esd.unlink(missing_ok=True)
            raise
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    def _multi_progress(
        self,
        callback: ProgressCallback | None,
        current: int,
        total: int,
        percent: float,
        message: str,
    ) -> None:
        if callback:
            overall = ((current + percent / 100.0) / total) * 100.0
            callback(clamp_progress(overall), message)

    def _wimexport_cmd(self) -> list[str]:
        cmd = self.deps.wimlib_cmd
        if Path(cmd).suffix.lower() == ".exe":
            return [cmd, "export"]
        if shutil.which("wimexport"):
            return ["wimexport"]
        return [cmd, "export"]

    def _export_single(
        self,
        source: Path,
        dest: Path,
        index: int,
        *,
        progress: ProgressCallback | None = None,
    ) -> Path:
        base = self._wimexport_cmd()
        args = [
            *base,
            str(source),
            str(index),
            str(dest),
            "--solid",
            "--compress=LZMS",
        ]

        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert proc.stdout is not None
        percent_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*%")

        for line in proc.stdout:
            match = percent_pattern.search(line)
            if match and progress:
                progress(clamp_progress(float(match.group(1))), line.strip())

        code = proc.wait()
        if code != 0:
            raise RuntimeError(f"wimexport failed (exit {code}) for index {index}")

        if dest.suffix.lower() != ".esd" and dest != Path(dest.with_suffix(".esd")):
            esd = dest.with_suffix(".esd")
            if esd != dest and not esd.exists():
                dest.rename(esd)
                dest = esd
        return dest

    def _join_images(
        self,
        parts: list[Path],
        dest_esd: Path,
        *,
        progress: ProgressCallback | None = None,
    ) -> Path:
        """Merge multiple single-index ESD files into one multi-index ESD.

        Uses ``wimexport <source> 1 <dest>`` to append each part's image
        (always index 1 in a single-index export) into the cumulative output.
        """
        if progress:
            progress(0, "Joining exported images…")

        base = self._wimexport_cmd()
        # Start by moving the first part as the base
        current = dest_esd.with_suffix(".merge.esd")
        shutil.copy2(str(parts[0]), str(current))

        for i, part in enumerate(parts[1:], 1):
            # Append image index 1 from 'part' into 'current'
            args = [*base, str(part), "1", str(current)]
            run_command(args)
            if progress:
                pct = (i / (len(parts) - 1)) * 100 if len(parts) > 1 else 100
                progress(clamp_progress(pct), f"Merged {i + 1}/{len(parts)} images")

        if current != dest_esd:
            shutil.move(str(current), str(dest_esd))
        if progress:
            progress(100, "Compression complete.")
        return dest_esd
