"""Tests for USB health check path resolution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from winiso_toolkit.usb.health import USBHealthChecker


@pytest.fixture
def checker() -> USBHealthChecker:
    return USBHealthChecker()


def test_resolve_uses_mount_point_when_provided(checker: USBHealthChecker, tmp_path: Path) -> None:
    resolved = checker.resolve_writable_directory(r"\\.\PHYSICALDRIVE1", mount_point=str(tmp_path))
    assert resolved == tmp_path


def test_resolve_windows_physical_drive_via_powershell(checker: USBHealthChecker) -> None:
    with patch("winiso_toolkit.usb.health.is_windows", return_value=True), patch(
        "subprocess.run",
        return_value=type("Result", (), {"stdout": "E:", "returncode": 0})(),
    ), patch.object(Path, "is_dir", return_value=True):
        resolved = checker.resolve_writable_directory(r"\\.\PHYSICALDRIVE1")

    assert str(resolved).startswith("E")


def test_resolve_linux_device_via_lsblk(checker: USBHealthChecker) -> None:
    lsblk_json = (
        '{"blockdevices":[{"name":"sdb","children":['
        '{"name":"sdb1","mountpoint":"/media/usb"}]}]}'
    )
    with patch("winiso_toolkit.usb.health.is_linux", return_value=True), patch(
        "subprocess.run",
        return_value=type("Result", (), {"stdout": lsblk_json, "returncode": 0})(),
    ), patch.object(Path, "is_dir", return_value=True):
        resolved = checker.resolve_writable_directory("/dev/sdb")

    assert resolved.as_posix() == "/media/usb"


def test_run_quick_health_check_uses_resolved_mount(
    checker: USBHealthChecker,
    tmp_path: Path,
) -> None:
    with patch.object(checker, "resolve_writable_directory", return_value=tmp_path), patch.object(
        checker,
        "verify_capacity",
        return_value=True,
    ), patch.object(checker, "benchmark_file_speed", return_value=25.5):
        report = checker.run_quick_health_check(
            r"\\.\PHYSICALDRIVE1",
            mount_point=str(tmp_path),
        )

    assert report.capacity_verified is True
    assert report.write_speed_mbps == 25.5
    assert "healthy" in report.status_message.lower()
