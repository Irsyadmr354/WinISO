"""Windows Update (.msu / .cab) Slipstreamer."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class UpdateSlipstreamer:
    """Slipstream Windows cumulative updates into WIM images."""

    def find_update_packages(self, updates_dir: Path) -> list[Path]:
        """Find all .msu and .cab update packages in a directory."""
        updates_dir = Path(updates_dir)
        if not updates_dir.is_dir():
            return []
        msus = list(updates_dir.rglob("*.msu")) + list(updates_dir.rglob("*.MSU"))
        cabs = list(updates_dir.rglob("*.cab")) + list(updates_dir.rglob("*.CAB"))
        found = set(msus).union(cabs)
        return sorted(list(found))

    def copy_updates_to_iso(self, iso_extracted_root: Path, updates_dir: Path) -> int:
        """Copy update packages into ISO $OEM$ setup directory for auto-installation."""
        pkgs = self.find_update_packages(updates_dir)
        if not pkgs:
            return 0

        target_dir = iso_extracted_root / "sources" / "$OEM$" / "$1" / "Updates"
        target_dir.mkdir(parents=True, exist_ok=True)

        for pkg in pkgs:
            shutil.copy2(pkg, target_dir / pkg.name)

        return len(pkgs)
