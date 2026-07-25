"""Offline Windows WIM Debloater & Bloatware Stripper."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from winiso_toolkit.utils.platform import run_command, which

logger = logging.getLogger(__name__)

# List of default provisioned AppX bloatware packages to remove
DEFAULT_BLOATWARE_PACKAGES = [
    "Microsoft.BingNews",
    "Microsoft.BingWeather",
    "Microsoft.GamingApp",
    "Microsoft.GetHelp",
    "Microsoft.Getstarted",
    "Microsoft.MicrosoftOfficeHub",
    "Microsoft.MicrosoftSolitaireCollection",
    "Microsoft.People",
    "Microsoft.PowerAutomateDesktop",
    "Microsoft.SkypeApp",
    "Microsoft.Todos",
    "Microsoft.Xbox.TCUI",
    "Microsoft.XboxApp",
    "Microsoft.XboxGameOverlay",
    "Microsoft.XboxGamingOverlay",
    "Microsoft.XboxIdentityProvider",
    "Microsoft.XboxSpeechToTextOverlay",
    "Microsoft.YourPhone",
    "Microsoft.ZuneMusic",
    "Microsoft.ZuneVideo",
]


@dataclass
class DebloatOptions:
    remove_appx: bool = True
    packages_to_remove: list[str] = field(default_factory=lambda: list(DEFAULT_BLOATWARE_PACKAGES))
    disable_onedrive: bool = True
    disable_telemetry: bool = True


class WIMDebloater:
    """Remove AppX bloatware packages and telemetry from WIM images."""

    def __init__(self, options: DebloatOptions | None = None) -> None:
        self.options = options or DebloatOptions()

    def generate_debloat_script(self, target_dir: Path) -> Path:
        """Generate a PowerShell debloating script for offline setup."""
        script_content = "# WinISO Toolkit - Automated Windows Debloater\n"
        for pkg in self.options.packages_to_remove:
            script_content += f'Get-AppxProvisionedPackage -Online | Where-Object DisplayName -like "*{pkg}*" | Remove-AppxProvisionedPackage -Online -ErrorAction SilentlyContinue\n'

        if self.options.disable_onedrive:
            script_content += 'stop-process -name "OneDrive" -ErrorAction SilentlyContinue\n'
            script_content += 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\OneDrive" /v "DisableFileSyncNGSC" /t REG_DWORD /d 1 /f\n'

        script_file = target_dir / "winiso_debloat.ps1"
        script_file.write_text(script_content, encoding="utf-8")
        return script_file
