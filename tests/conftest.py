"""pytest configuration and shared fixtures for WinISO Toolkit tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_dir() -> Path:
    """Return a temporary directory that is cleaned up after each test."""
    with tempfile.TemporaryDirectory(prefix="winiso_test_") as d:
        yield Path(d)


@pytest.fixture
def sample_iso_dir(tmp_dir: Path) -> Path:
    """Populate a temp dir with a minimal Windows ISO file-tree skeleton."""
    (tmp_dir / "sources").mkdir()
    (tmp_dir / "sources" / "install.wim").write_bytes(b"\x00" * 64)
    (tmp_dir / "boot").mkdir()
    (tmp_dir / "boot" / "etfsboot.com").write_bytes(b"\x00" * 8)
    (tmp_dir / "efi" / "microsoft" / "boot").mkdir(parents=True)
    (tmp_dir / "efi" / "microsoft" / "boot" / "efisys.bin").write_bytes(b"\x00" * 8)
    return tmp_dir
