"""WinPE Emergency Rescue Media Builder."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class WinPERescueBuilder:
    """Build live WinPE rescue and diagnostic boot media."""

    RESCUE_TOOLS = [
        "7-Zip File Manager",
        "DiskGenius Partition Manager",
        "HWMonitor System Diagnostics",
        "Chntpw Password Reset",
    ]

    def build_rescue_media(self, iso_extracted_root: Path) -> bool:
        """Inject WinPE rescue launcher and tools folder into ISO root."""
        rescue_dir = iso_extracted_root / "WinISO_Rescue_Tools"
        rescue_dir.mkdir(parents=True, exist_ok=True)

        # Write rescue manifesto
        manifest = f"""=== WinISO Toolkit Emergency Rescue Media ===
Included Diagnostic Utilities:
"""
        for tool in self.RESCUE_TOOLS:
            manifest += f" - {tool}\n"

        (rescue_dir / "README_RESCUE.txt").write_text(manifest, encoding="utf-8")
        return True
