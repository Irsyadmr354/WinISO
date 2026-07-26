"""WinISO Toolkit — Windows ISO Compressor & Bootable USB Creator."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__: str = version("winiso-toolkit")
except PackageNotFoundError:
    # Package not installed (e.g. running directly from source tree)
    __version__ = "0.0.0.dev0"
