"""Tests for portable xorriso installation on Windows."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from winiso_toolkit.deps.installer import (
    _XORRISO_WINDOWS_FILES,
    DependencyInstaller,
)


@pytest.fixture
def installer() -> DependencyInstaller:
    return DependencyInstaller()


def test_xorriso_bundle_requires_all_runtime_files(installer: DependencyInstaller, tmp_path: Path) -> None:
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    (tools_dir / "xorriso.exe").write_bytes(b"fake")

    assert installer._xorriso_windows_bundle_complete(tools_dir) is False

    for name in _XORRISO_WINDOWS_FILES:
        (tools_dir / name).write_bytes(b"fake")

    assert installer._xorriso_windows_bundle_complete(tools_dir) is True


def test_check_xorriso_rejects_broken_windows_bundle(
    installer: DependencyInstaller,
    tmp_path: Path,
) -> None:
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    (tools_dir / "xorriso.exe").write_bytes(b"fake")

    with patch.object(installer, "_tools_dir", return_value=tools_dir), patch(
        "winiso_toolkit.deps.installer.is_windows",
        return_value=True,
    ), patch.object(installer, "_verify_xorriso_executable", return_value=False):
        status = installer.check_xorriso()

    assert status.installed is False
    assert "DLL" in status.message or "re-downloaded" in status.message


def test_install_xorriso_direct_downloads_all_files(
    installer: DependencyInstaller,
    tmp_path: Path,
) -> None:
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()

    def fake_urlopen(req, timeout=120):  # noqa: ARG001
        url = req.full_url
        filename = url.rsplit("/", 1)[-1]
        payload = MagicMock()
        payload.read.return_value = f"content-{filename}".encode()
        payload.__enter__ = lambda s: s
        payload.__exit__ = MagicMock(return_value=False)
        return payload

    with patch.object(installer, "_tools_dir", return_value=tools_dir), patch(
        "winiso_toolkit.deps.installer.is_windows",
        return_value=True,
    ), patch("urllib.request.urlopen", side_effect=fake_urlopen), patch.object(
        installer,
        "_verify_xorriso_executable",
        return_value=True,
    ):
        ok = installer.install_xorriso_direct()

    assert ok is True
    for name in _XORRISO_WINDOWS_FILES:
        assert (tools_dir / name).read_bytes() == f"content-{name}".encode()
