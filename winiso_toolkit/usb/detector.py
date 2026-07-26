"""Detect removable USB storage devices."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass

from winiso_toolkit.utils.platform import is_linux, is_windows


@dataclass
class USBDevice:
    path: str
    name: str
    size_bytes: int
    filesystem: str
    removable: bool = True
    model: str = ""
    mount_point: str = ""

    @property
    def size_gb(self) -> float:
        return self.size_bytes / (1024**3)

    def has_capacity_for(self, required_bytes: int) -> bool:
        return self.size_bytes >= required_bytes


class USBDetector:
    """List connected removable USB drives."""

    def list_devices(self) -> list[USBDevice]:
        if is_linux():
            return self._list_linux()
        if is_windows():
            return self._list_windows()
        return []

    def _list_linux(self) -> list[USBDevice]:
        try:
            result = subprocess.run(
                ["lsblk", "-Jb", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,RM,MODEL,LABEL"],
                capture_output=True,
                text=True,
                check=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            return []

        data = json.loads(result.stdout)
        devices: list[USBDevice] = []

        for dev in data.get("blockdevices", []):
            if dev.get("type") != "disk":
                continue
            if str(dev.get("rm", "")).lower() not in ("1", "true"):
                continue
            try:
                size = int(dev.get("size", 0))
            except (TypeError, ValueError):
                size = parse_size(str(dev.get("size", "0")))
            fs = ""
            label = dev.get("label") or ""
            mount = ""
            for child in dev.get("children") or []:
                if child.get("fstype"):
                    fs = child["fstype"]
                    if child.get("label"):
                        label = child["label"]
                if child.get("mountpoint"):
                    mount = child["mountpoint"]
            devices.append(
                USBDevice(
                    path=f"/dev/{dev['name']}",
                    name=label or dev.get("model") or dev["name"],
                    size_bytes=size,
                    filesystem=fs,
                    model=dev.get("model") or "",
                    mount_point=mount,
                )
            )
        return devices

    def _list_windows(self) -> list[USBDevice]:
        ps_script = """
Get-Disk | Where-Object { $_.BusType -eq 'USB' -and $_.Size -gt 0 } | ForEach-Object {
    $part = Get-Partition -DiskNumber $_.Number -ErrorAction SilentlyContinue |
        Where-Object { $_.DriveLetter } | Select-Object -First 1
    $vol = $null
    if ($part) { $vol = Get-Volume -Partition $part -ErrorAction SilentlyContinue }
    [PSCustomObject]@{
        Number = $_.Number
        Path = '\\\\.\\PHYSICALDRIVE' + $_.Number
        Size = $_.Size
        Model = $_.FriendlyName
        FileSystem = if ($vol) { $vol.FileSystemType } else { '' }
        Label = if ($vol) { $vol.FileSystemLabel } else { $_.FriendlyName }
        DriveLetter = if ($part) { $part.DriveLetter } else { $null }
    }
} | ConvertTo-Json -Compress
"""
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            return []

        if result.returncode != 0 or not result.stdout.strip():
            return self._list_windows_wmic()

        raw = result.stdout.strip()
        if raw.startswith("["):
            items = json.loads(raw)
        elif raw:
            items = [json.loads(raw)]
        else:
            return []

        devices: list[USBDevice] = []
        for item in items:
            drive_letter = item.get("DriveLetter")
            mount_point = f"{drive_letter}:\\" if drive_letter else ""
            devices.append(
                USBDevice(
                    path=item.get("Path", ""),
                    name=item.get("Label") or item.get("Model") or f"Disk {item.get('Number')}",
                    size_bytes=int(item.get("Size") or 0),
                    filesystem=item.get("FileSystem") or "",
                    model=item.get("Model") or "",
                    mount_point=mount_point,
                )
            )
        return devices

    def _list_windows_wmic(self) -> list[USBDevice]:
        try:
            result = subprocess.run(
                ["wmic", "diskdrive", "where", "InterfaceType='USB'", "get",
                 "DeviceID,Size,Model", "/format:csv"],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            return []

        devices: list[USBDevice] = []
        for line in result.stdout.splitlines():
            if not line.strip() or line.startswith("Node"):
                continue
            parts = line.split(",")
            if len(parts) < 4:
                continue
            device_id = parts[1].strip()
            model = parts[2].strip()
            try:
                size = int(parts[3].strip())
            except ValueError:
                size = 0
            if device_id:
                devices.append(
                    USBDevice(
                        path=device_id,
                        name=model or device_id,
                        size_bytes=size,
                        filesystem="",
                        model=model,
                    )
                )
        return devices


def parse_size(size_str: str) -> int:
    """Parse lsblk size strings like 14.9G, 512M."""
    size_str = size_str.strip().upper()
    match = re.match(r"([\d.]+)([KMGT]?)", size_str)
    if not match:
        return 0
    value = float(match.group(1))
    unit = match.group(2) or ""
    multipliers = {"": 1, "K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}
    return int(value * multipliers.get(unit, 1))
