"""WinPE Emergency Rescue Media Builder."""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from winiso_toolkit.utils.platform import which

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RescueToolSpec:
    """Definition of a rescue tool slot in the WinPE media."""

    name: str
    folder: str
    launcher: str
    description: str
    portable_exe: str
    system_candidates: tuple[str, ...] = ()


class WinPERescueBuilder:
    """Build live WinPE rescue and diagnostic boot media."""

    RESCUE_TOOLS: tuple[RescueToolSpec, ...] = (
        RescueToolSpec(
            name="7-Zip File Manager",
            folder="7-Zip",
            launcher="Launch_7-Zip.cmd",
            description="Archive manager for extracting drivers and logs.",
            portable_exe="7zFM.exe",
            system_candidates=("7zFM.exe", "7zG.exe"),
        ),
        RescueToolSpec(
            name="DiskGenius Partition Manager",
            folder="DiskGenius",
            launcher="Launch_DiskGenius.cmd",
            description="Partition editor and disk recovery utility.",
            portable_exe="DiskGenius.exe",
        ),
        RescueToolSpec(
            name="HWMonitor System Diagnostics",
            folder="HWMonitor",
            launcher="Launch_HWMonitor.cmd",
            description="Hardware temperature and sensor monitor.",
            portable_exe="HWMonitor.exe",
        ),
        RescueToolSpec(
            name="Chntpw Password Reset",
            folder="Chntpw",
            launcher="Launch_Chntpw.cmd",
            description="Offline Windows password reset helper.",
            portable_exe="chntpw.exe",
        ),
    )

    def build_rescue_media(self, iso_extracted_root: Path) -> bool:
        """Inject WinPE rescue launcher, tool slots, and startup menu into ISO root."""
        rescue_dir = iso_extracted_root / "WinISO_Rescue_Tools"
        tools_dir = rescue_dir / "Tools"
        rescue_dir.mkdir(parents=True, exist_ok=True)
        tools_dir.mkdir(parents=True, exist_ok=True)

        manifest_tools: list[dict[str, str | bool]] = []
        for spec in self.RESCUE_TOOLS:
            tool_dir = tools_dir / spec.folder
            tool_dir.mkdir(parents=True, exist_ok=True)
            bundled = self._bundle_system_tool(spec, tool_dir)
            self._write_tool_launcher(tool_dir, spec, bundled)
            manifest_tools.append(
                {
                    "name": spec.name,
                    "folder": spec.folder,
                    "launcher": spec.launcher,
                    "description": spec.description,
                    "bundled_from_system": bundled,
                }
            )

        self._write_readme(rescue_dir, manifest_tools)
        self._write_start_menu(rescue_dir, manifest_tools)
        self._write_manifest(rescue_dir, manifest_tools)
        self._write_autorun_hook(iso_extracted_root, rescue_dir)
        return True

    def _bundle_system_tool(self, spec: RescueToolSpec, tool_dir: Path) -> bool:
        """Copy a matching system binary into the tool folder when available."""
        for candidate in spec.system_candidates:
            path = which(candidate)
            if path:
                dest = tool_dir / spec.portable_exe
                try:
                    shutil.copy2(path, dest)
                    logger.info("Bundled %s from system PATH for rescue media.", candidate)
                    return True
                except OSError as exc:
                    logger.warning("Could not copy %s: %s", candidate, exc)
        return False

    def _write_tool_launcher(self, tool_dir: Path, spec: RescueToolSpec, bundled: bool) -> None:
        portable_path = tool_dir / spec.portable_exe
        if bundled and portable_path.is_file():
            body = f"""@echo off
title {spec.name}
cd /d "%~dp0"
start "" "{spec.portable_exe}"
"""
        else:
            body = f"""@echo off
title {spec.name}
echo.
echo  {spec.name}
echo  {spec.description}
echo.
echo  Place the portable executable here:
echo    %~dp0{spec.portable_exe}
echo.
echo  Download a portable build, copy it into this folder, then re-run the launcher.
echo.
pause
"""
        (tool_dir / spec.launcher).write_text(body, encoding="utf-8")

    def _write_readme(self, rescue_dir: Path, tools: list[dict[str, str | bool]]) -> None:
        lines = [
            "=== WinISO Toolkit Emergency Rescue Media ===",
            "",
            "This rescue suite provides launcher scripts and tool folders inside the ISO.",
            "Drop portable executables into each Tools subfolder, then boot the media.",
            "",
            "Included tool slots:",
        ]
        for tool in tools:
            status = "bundled from system" if tool["bundled_from_system"] else "awaiting portable EXE"
            lines.append(f" - {tool['name']} ({status})")
            lines.append(f"     {tool['description']}")
        lines.extend(
            [
                "",
                "Quick start:",
                "  1. Boot this ISO/USB in WinPE or Windows Setup (Shift+F10 for CMD).",
                "  2. Run WinISO_Rescue_Tools\\START_RESCUE.cmd",
                "  3. Pick a diagnostic tool from the menu.",
            ]
        )
        (rescue_dir / "README_RESCUE.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _write_start_menu(self, rescue_dir: Path, tools: list[dict[str, str | bool]]) -> None:
        menu_lines = [
            "@echo off",
            "title WinISO Rescue Toolkit",
            ":menu",
            "cls",
            "echo ========================================================",
            "echo        WinISO Toolkit - Emergency Rescue Menu",
            "echo ========================================================",
            "echo.",
        ]
        for idx, tool in enumerate(tools, start=1):
            menu_lines.append(f"echo  [{idx}] {tool['name']}")
        menu_lines.extend(
            [
                "echo  [0] Exit",
                "echo.",
                "set /p choice=Select tool: ",
            ]
        )
        for idx, tool in enumerate(tools, start=1):
            launcher = Path("Tools") / str(tool["folder"]) / str(tool["launcher"])
            menu_lines.append(f'if "%choice%"=="{idx}" call "%~dp0{launcher}" & goto menu')
        menu_lines.extend(["if \"%choice%\"==\"0\" exit /b 0", "goto menu", ""])
        (rescue_dir / "START_RESCUE.cmd").write_text("\n".join(menu_lines), encoding="utf-8")

    def _write_manifest(self, rescue_dir: Path, tools: list[dict[str, str | bool]]) -> None:
        (rescue_dir / "tools_manifest.json").write_text(
            json.dumps({"tools": tools}, indent=2),
            encoding="utf-8",
        )

    def _write_autorun_hook(self, iso_root: Path, rescue_dir: Path) -> None:
        """Add a Setup helper script users can run from WinPE/recovery CMD."""
        sources_dir = iso_root / "sources"
        sources_dir.mkdir(parents=True, exist_ok=True)
        hook = sources_dir / "winiso_rescue_launcher.cmd"
        hook.write_text(
            "@echo off\n"
            f'call "{rescue_dir.name}\\START_RESCUE.cmd"\n',
            encoding="utf-8",
        )
