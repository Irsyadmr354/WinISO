"""Official Microsoft Direct ISO Downloader & CDN Resolver."""

from __future__ import annotations

import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from winiso_toolkit.utils.progress import ProgressCallback, clamp_progress

logger = logging.getLogger(__name__)

DOWNLOAD_TIMEOUT_SEC = 60
MAX_RETRIES = 3


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
        """Download ISO from URL with progress reporting, retries, and resume."""
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                return self._download_once(url, dest_path, progress)
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = exc
                if attempt < MAX_RETRIES - 1:
                    wait = 2 ** attempt
                    logger.warning(
                        "Download attempt %d failed (%s); retrying in %ds…",
                        attempt + 1,
                        exc,
                        wait,
                    )
                    time.sleep(wait)
                else:
                    break

        raise RuntimeError(
            f"Failed to download ISO after {MAX_RETRIES} attempts: {last_error}"
        ) from last_error

    def _download_once(
        self,
        url: str,
        dest_path: Path,
        progress: ProgressCallback | None,
    ) -> Path:
        downloaded = dest_path.stat().st_size if dest_path.exists() else 0
        headers = {"User-Agent": "Mozilla/5.0"}
        if downloaded > 0:
            headers["Range"] = f"bytes={downloaded}-"

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT_SEC) as resp:
            status = getattr(resp, "status", 200)
            if downloaded > 0 and status not in (206, 200):
                dest_path.unlink(missing_ok=True)
                downloaded = 0

            content_range = resp.headers.get("Content-Range", "")
            if content_range and "/" in content_range:
                total = int(content_range.rsplit("/", 1)[1])
            else:
                content_length = resp.headers.get("Content-Length")
                total = int(content_length) + downloaded if content_length else 0

            mode = "ab" if downloaded > 0 and status == 206 else "wb"
            if mode == "wb":
                downloaded = 0

            block_size = 1024 * 1024  # 1MB
            with open(dest_path, mode) as f:
                while True:
                    chunk = resp.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress and total > 0:
                        pct = clamp_progress((downloaded / total) * 100)
                        msg = (
                            f"Downloading ISO: {downloaded / (1024**3):.2f} / "
                            f"{total / (1024**3):.2f} GB"
                        )
                        progress(pct, msg)

        return dest_path
