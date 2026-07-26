"""Unified logging system with file rotation and diagnostic dump export."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path.home() / ".winiso_toolkit"
LOG_FILE = LOG_DIR / "winiso_toolkit.log"


def setup_logger(debug: bool = False) -> logging.Logger:
    """Configure logger with rotating file handler and console handler."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("winiso_toolkit")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    if not logger.handlers:
        # File handler (rotating max 5MB, 3 backups)
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
        logger.addHandler(console_handler)

    return logger


def export_diagnostic_report(error_message: str, dest_file: Path = Path("diagnostic_report.txt")) -> Path:
    """Export structured diagnostic dump for troubleshooting."""
    import platform

    report = f"""=== WinISO Toolkit Diagnostic Report ===
Date: {logging.Formatter().formatTime(logging.LogRecord("", 0, "", 0, "", (), None))}
OS Platform: {platform.platform()}
Python Version: {platform.python_version()}

--- Error Details ---
{error_message}

--- System Log Tail ---
"""
    if LOG_FILE.exists():
        lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        report += "\n".join(lines[-50:])
    else:
        report += "No log file found."

    dest_file.write_text(report, encoding="utf-8")
    return dest_file
