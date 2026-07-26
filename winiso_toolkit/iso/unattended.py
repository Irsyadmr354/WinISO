"""Automated autounattend.xml generator for Windows 10/11 setup.

Supports bypassing TPM 2.0, Secure Boot, RAM, CPU, Storage, and mandatory
Microsoft Account (MSA) requirements, plus automated local account creation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape


@dataclass
class BypassOptions:
    bypass_tpm: bool = True
    bypass_secure_boot: bool = True
    bypass_ram: bool = True
    bypass_cpu: bool = True
    bypass_msa: bool = True
    disable_telemetry: bool = True
    username: str = "User"
    computer_name: str = "WinISO-PC"
    language: str = "en-US"


class UnattendedGenerator:
    """Generate autounattend.xml for unattended Windows installation."""

    def __init__(self, options: BypassOptions | None = None) -> None:
        self.options = options or BypassOptions()

    def generate_xml(self) -> str:
        opts = self.options

        # Registry commands for Win11 requirement bypasses during Setup (OOBE/specialize)
        reg_bypasses = []
        if opts.bypass_tpm:
            reg_bypasses.append(
                'reg add "HKLM\\SYSTEM\\Setup\\LabConfig" /v "BypassTPMCheck" /t REG_DWORD /d 1 /f'
            )
        if opts.bypass_secure_boot:
            reg_bypasses.append(
                'reg add "HKLM\\SYSTEM\\Setup\\LabConfig" /v "BypassSecureBootCheck" /t REG_DWORD /d 1 /f'
            )
        if opts.bypass_ram:
            reg_bypasses.append(
                'reg add "HKLM\\SYSTEM\\Setup\\LabConfig" /v "BypassRAMCheck" /t REG_DWORD /d 1 /f'
            )
        if opts.bypass_cpu:
            reg_bypasses.append(
                'reg add "HKLM\\SYSTEM\\Setup\\LabConfig" /v "BypassCPUCheck" /t REG_DWORD /d 1 /f'
            )
            reg_bypasses.append(
                'reg add "HKLM\\SYSTEM\\Setup\\LabConfig" /v "BypassStorageCheck" /t REG_DWORD /d 1 /f'
            )

        specialize_bypasses = []
        if opts.bypass_msa:
            # BypassNRO registry entry to allow offline account setup in Win 11 OOBE
            specialize_bypasses.append(
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\OOBE" /v "BypassNRO" /t REG_DWORD /d 1 /f'
            )

        if opts.disable_telemetry:
            specialize_bypasses.append(
                'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v "AllowTelemetry" /t REG_DWORD /d 0 /f'
            )

        run_synchronous_cmds = ""
        for idx, cmd in enumerate(reg_bypasses, start=1):
            run_synchronous_cmds += f"""
                <RunSynchronousCommand wcm:action="add">
                    <Order>{idx}</Order>
                    <Path>cmd.exe /c {escape(cmd, {'"': '&quot;'})}</Path>
                    <Description>Bypass Setup Requirement {idx}</Description>
                </RunSynchronousCommand>"""

        specialize_cmds = ""
        for idx, cmd in enumerate(specialize_bypasses, start=1):
            specialize_cmds += f"""
                <RunSynchronousCommand wcm:action="add">
                    <Order>{idx}</Order>
                    <Path>cmd.exe /c {escape(cmd, {'"': '&quot;'})}</Path>
                    <Description>Specialize Setup Command {idx}</Description>
                </RunSynchronousCommand>"""

        xml = f"""<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
  <settings pass="windowsPE">
    <component name="Microsoft-Windows-International-Core-WinPE" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <SetupUILanguage>
        <UILanguage>{opts.language}</UILanguage>
      </SetupUILanguage>
      <InputLocale>{opts.language}</InputLocale>
      <SystemLocale>{opts.language}</SystemLocale>
      <UserLocale>{opts.language}</UserLocale>
      <UILanguage>{opts.language}</UILanguage>
    </component>
    <component name="Microsoft-Windows-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <UserData>
        <AcceptEula>true</AcceptEula>
      </UserData>
      <RunSynchronous>{run_synchronous_cmds}
      </RunSynchronous>
    </component>
  </settings>
  <settings pass="specialize">
    <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <ComputerName>{opts.computer_name}</ComputerName>
    </component>
    <component name="Microsoft-Windows-Deployment" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <RunSynchronous>{specialize_cmds}
      </RunSynchronous>
    </component>
  </settings>
  <settings pass="oobeSystem">
    <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <OOBE>
        <HideEULAPage>true</HideEULAPage>
        <HideOEMRegistrationScreen>true</HideOEMRegistrationScreen>
        <HideOnlineAccountScreens>true</HideOnlineAccountScreens>
        <HideWirelessSetupInOOBE>true</HideWirelessSetupInOOBE>
        <NetworkLocation>Work</NetworkLocation>
        <ProtectYourPC>3</ProtectYourPC>
      </OOBE>
      <UserAccounts>
        <LocalAccounts>
          <LocalAccount wcm:action="add">
            <Name>{opts.username}</Name>
            <Group>Administrators</Group>
            <DisplayName>{opts.username}</DisplayName>
            <Description>Local Administrator Account</Description>
          </LocalAccount>
        </LocalAccounts>
      </UserAccounts>
    </component>
  </settings>
</unattend>
"""
        return xml

    def save(self, dest_path: Path) -> Path:
        dest_path = Path(dest_path)
        dest_path.write_text(self.generate_xml(), encoding="utf-8")
        return dest_path
