"""Cross-platform helpers."""

import platform
import shutil
import subprocess
from pathlib import Path


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_linux() -> bool:
    return platform.system() == "Linux"


def which(name: str) -> Path | None:
    """Resolve an executable on PATH."""
    found = shutil.which(name)
    return Path(found) if found else None


def run_command(
    args: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess with consistent encoding."""
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        check=check,
        capture_output=capture,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
