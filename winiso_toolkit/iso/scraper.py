"""Official Microsoft Direct ISO Downloader & CDN Resolver."""

from __future__ import annotations

import logging
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from winiso_toolkit.utils.progress import ProgressCallback, clamp_progress

logger = logging.getLogger(__name__)


@dataclass
class MSISORelease:
    name: str
    product_id: str
    language: str
    url: str


class MicrosoftISOScraper:
    """Resolve and download official Microsoft Windows ISO images."""

    KNOWN_CDN_URLS = {
        "win11_23h2_en": "https://software.download.prss.microsoft.com/db/Win11_23H2_English_x64v2.iso",
        "win10_22h2_en": "https://software.download.prss.microsoft.com/db/Win10_22H2_English_x64.iso",
    }

    def list_available_releases(self) -> list[MSISORelease]:
        return [
            MSISORelease(
                name="Windows 11 23H2 (x64)",
                product_id="win11_23h2",
                language="English (en-US)",
                url=self.KNOWN_CDN_URLS["win11_23h2_en"],
            ),
            MSISORelease(
                name="Windows 10 22H2 (x64)",
                product_id="win10_22h2",
                language="English (en-US)",
                url=self.KNOWN_CDN_URLS["win10_22h2_en"],
            ),
        ]

    def download_iso(
        self,
        url: str,
        dest_path: Path,
        progress: ProgressCallback | None = None,
    ) -> Path:
        """Download ISO from URL with progress reporting."""
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            block_size = 1024 * 1024  # 1MB

            with open(dest_path, "wb") as f:
                while True:
                    chunk = resp.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress and total > 0:
                        pct = clamp_progress((downloaded / total) * 100)
                        msg = f"Downloading ISO: {downloaded / (1024**3):.2f} / {total / (1024**3):.2f} GB"
                        progress(pct, msg)

        return dest_path
