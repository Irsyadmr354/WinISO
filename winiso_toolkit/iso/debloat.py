"""Offline Windows WIM Debloater & Bloatware Stripper."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

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

    def generate_debloat_script(self, target_dir: Path, mounted_image_dir: str = "C:\\WinISO_Mount") -> Path:
        """Generate a PowerShell debloating script that targets an *offline*
        mounted WIM image (via DISM) rather than the running online system.

        Args:
            target_dir: Directory to write the script into.
            mounted_image_dir: Path where the offline WIM/image is mounted
                (e.g. via ``DISM /Mount-Image``) before this script runs.
        """
        script_content = "# WinISO Toolkit - Automated Windows Debloater (offline image)\n"
        for pkg in self.options.packages_to_remove:
            script_content += (
                f'Get-AppxProvisionedPackage -Path "{mounted_image_dir}" '
                f'| Where-Object DisplayName -like "*{pkg}*" '
                f'| Remove-AppxProvisionedPackage -Path "{mounted_image_dir}" -ErrorAction SilentlyContinue\n'
            )

        if self.options.disable_onedrive:
            script_content += 'stop-process -name "OneDrive" -ErrorAction SilentlyContinue\n'
            script_content += 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\OneDrive" /v "DisableFileSyncNGSC" /t REG_DWORD /d 1 /f\n'

        if self.options.disable_telemetry:
            script_content += 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v "AllowTelemetry" /t REG_DWORD /d 0 /f\n'
            script_content += 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v "MaxTelemetryAllowed" /t REG_DWORD /d 0 /f\n'

        target_dir.mkdir(parents=True, exist_ok=True)
        script_file = target_dir / "winiso_debloat.ps1"
        script_file.write_text(script_content, encoding="utf-8")
        return script_file
