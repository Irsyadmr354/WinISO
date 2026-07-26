"""WinPE Emergency Recovery & Setup Tool Slipstreamer.

Injects custom recovery scripts, registry overrides, and WinPE shortcuts into
Windows installer boot media for offline rescue and system recovery.
"""

from __future__ import annotations

from pathlib import Path


class WinPEInjector:
    """Inject emergency tools and recovery scripts into WinPE media."""

    def inject_winpe_cmd_shortcut(self, iso_extracted_root: Path) -> bool:
        """Create a WinPE startup script that displays a recovery command prompt helper."""
        sources_dir = iso_extracted_root / "sources"
        if not sources_dir.is_dir():
            return False

        # Create WinPE helper script
        cmd_script = """@echo off
echo ========================================================
echo        WinISO Toolkit - Emergency Recovery Shell
echo ========================================================
echo Press Shift + F10 anytime during setup to open CMD.
echo Available diagnostic tools: diskpart, bootrec, regedit
echo ========================================================
"""
        script_path = sources_dir / "winiso_recovery.bat"
        script_path.write_text(cmd_script, encoding="utf-8")

        # Create winpeshl.ini to auto-launch the recovery script during WinPE
        winpeshl = sources_dir / "winpeshl.ini"
        winpeshl.write_text(
            "[LaunchApps]\n"
            "%SYSTEMDRIVE%\\sources\\winiso_recovery.bat\n",
            encoding="utf-8",
        )
        return True
