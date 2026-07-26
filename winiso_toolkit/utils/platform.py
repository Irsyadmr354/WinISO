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


_WIN_STATUS_DLL_NOT_FOUND = 0xC0000135


def describe_process_failure(returncode: int, stderr: str = "", stdout: str = "") -> str:
    """Turn a subprocess exit code into a readable error message."""
    if returncode == _WIN_STATUS_DLL_NOT_FOUND or returncode == -1073741515:
        return (
            "required DLL not found (Windows 0xC0000135). "
            "Re-run dependency install or install Windows ADK (oscdimg.exe)."
        )
    detail = (stderr or stdout).strip()
    if detail:
        return detail
    return f"process exited with code {returncode}"


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
