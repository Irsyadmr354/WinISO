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
        path_kw = _resolve_path_type(iso)
        walk_kwargs = {path_kw: "/"}
        for current, _dirs, files in iso.walk(**walk_kwargs):
            rel = _iso_rel_path(current)
            out_dir = dest / rel
            out_dir.mkdir(parents=True, exist_ok=True)
            for name in files:
                _extract_file(
                    iso,
                    f"{current}/{name}".replace("//", "/"),
                    dest,
                    path_kw=path_kw,
                )
    finally:
        iso.close()


def _resolve_path_type(iso: pycdlib.PyCdlib) -> str:
    """Pick the best filesystem path type for walking/extracting this ISO."""
    if iso.has_udf():
        return "udf_path"
    if iso.has_joliet():
        return "joliet_path"
    return "iso_path"


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
    path_kw: str,
) -> None:
    rel = _iso_rel_path(iso_path)
    out = dest_root / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    iso.get_file_from_iso(local_path=str(out), **{path_kw: iso_path})
