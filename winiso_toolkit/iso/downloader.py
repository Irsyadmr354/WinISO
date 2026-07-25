"""Official Microsoft Windows ISO Downloader Helper.

Provides direct links and download utilities for official Windows 11 and 10 ISOs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OfficialISOLink:
    version: str
    edition: str
    url: str
    description: str


class ISODownloader:
    """Helper for fetching official Microsoft Windows ISO download URLs."""

    OFFICIAL_DOWNLOAD_PAGES = {
        "Windows 11 (64-bit)": "https://www.microsoft.com/software-download/windows11",
        "Windows 10 (64-bit)": "https://www.microsoft.com/software-download/windows10",
    }

    def get_official_links(self) -> list[OfficialISOLink]:
        return [
            OfficialISOLink(
                version="Windows 11 23H2/24H2",
                edition="Multi-edition ISO (x64)",
                url="https://www.microsoft.com/software-download/windows11",
                description="Official Microsoft Windows 11 Multi-edition ISO",
            ),
            OfficialISOLink(
                version="Windows 10 22H2",
                edition="Multi-edition ISO (x64)",
                url="https://www.microsoft.com/software-download/windows10",
                description="Official Microsoft Windows 10 Multi-edition ISO",
            ),
        ]
