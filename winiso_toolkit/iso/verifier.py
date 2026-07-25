"""ISO SHA-256 Checksum Verifier & Official Microsoft Hash Matcher."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class HashVerificationResult:
    calculated_hash: str
    is_official_match: bool
    official_name: str = ""


# Official Microsoft Published SHA-256 Hashes for English (en-US) ISOs
KNOWN_OFFICIAL_HASHES = {
    # Windows 11 23H2 (x64)
    "9c788600183141b7d14d8ed1702e5a60e060014b2d35eb18080f589886a11e03": "Windows 11 23H2 (x64) English",
    # Windows 11 22H2 (x64)
    "a06d88f615f5d02345511b0e360980c6f554e26e2e5058091724d1a49f57912a": "Windows 11 22H2 (x64) English",
    # Windows 10 22H2 (x64)
    "2967e81404c084050f24522d4f26b52a7812f689f24e908db618e77c5d9e5b87": "Windows 10 22H2 (x64) English",
}


class ISOVerifier:
    """Verify ISO file integrity against SHA-256 checksums."""

    def calculate_sha256(self, iso_path: Path, progress_callback=None) -> str:
        """Calculate SHA-256 hash of an ISO file."""
        iso_path = Path(iso_path)
        if not iso_path.is_file():
            raise FileNotFoundError(f"ISO file not found: {iso_path}")

        total_bytes = iso_path.stat().st_size
        h = hashlib.sha256()
        read_bytes = 0

        with iso_path.open("rb") as f:
            for chunk in iter(lambda: f.read(2 * 1024 * 1024), b""):
                h.update(chunk)
                read_bytes += len(chunk)
                if progress_callback and total_bytes > 0:
                    pct = (read_bytes / total_bytes) * 100
                    progress_callback(pct, f"Calculating SHA-256... ({read_bytes / (1024**3):.1f} GB)")

        return h.hexdigest().lower()

    def verify_iso(self, iso_path: Path, progress_callback=None) -> HashVerificationResult:
        """Calculate SHA-256 and check if it matches official Microsoft releases."""
        digest = self.calculate_sha256(iso_path, progress_callback)
        match_name = KNOWN_OFFICIAL_HASHES.get(digest, "")
        return HashVerificationResult(
            calculated_hash=digest,
            is_official_match=bool(match_name),
            official_name=match_name or "Custom / Unrecognized ISO",
        )
