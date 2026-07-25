"""Build script to compile WinISO Toolkit into a single standalone executable."""

import subprocess
import sys
from pathlib import Path


def build_executable() -> None:
    print("Building WinISO Toolkit standalone executable...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "winiso_toolkit.spec",
        "--clean",
        "--noconfirm",
    ]
    result = subprocess.run(cmd)
    if result.returncode == 0:
        print("\nSuccess! Binary created in dist/WinISO-Toolkit")
    else:
        print(f"\nBuild failed with exit code {result.returncode}")


if __name__ == "__main__":
    build_executable()
