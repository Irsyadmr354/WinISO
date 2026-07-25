"""Extract ISO contents using pycdlib (no mount required)."""

from __future__ import annotations

from pathlib import Path
import re

import pycdlib


def extract_iso(iso_path: Path, dest: Path) -> None:
    """Extract all files from an ISO into dest."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)

    iso = pycdlib.PyCdlib()
    iso.open(str(iso_path))

    try:
        walk_path = "/"
        if iso.has_joliet():
            for current, _dirs, files in iso.walk(joliet_path="/"):
                rel = _iso_rel_path(current)
                out_dir = dest / rel
                out_dir.mkdir(parents=True, exist_ok=True)
                for name in files:
                    _extract_file(iso, f"{current}/{name}".replace("//", "/"), dest, joliet=True)
        else:
            for current, _dirs, files in iso.walk(iso_path="/"):
                rel = _iso_rel_path(current)
                out_dir = dest / rel
                out_dir.mkdir(parents=True, exist_ok=True)
                for name in files:
                    _extract_file(iso, f"{current}/{name}".replace("//", "/"), dest, joliet=False)
    finally:
        iso.close()


def _iso_rel_path(iso_path: str) -> Path:
    """Convert ISO internal path to a local relative path.

    Strips the ISO9660 version suffix (;N) from each path component
    rather than replacing ';' with '/', which would corrupt filenames.
    """
    cleaned = iso_path.strip("/")
    if not cleaned:
        return Path(".")
    parts = cleaned.split("/")
    parts = [re.sub(r";\d+$", "", p) for p in parts]
    return Path("/".join(parts))


def _extract_file(
    iso: pycdlib.PyCdlib,
    iso_path: str,
    dest_root: Path,
    *,
    joliet: bool,
) -> None:
    rel = _iso_rel_path(iso_path)
    out = dest_root / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    if joliet:
        iso.get_file_from_iso(local_path=str(out), joliet_path=iso_path)
    else:
        iso.get_file_from_iso(local_path=str(out), iso_path=iso_path)
