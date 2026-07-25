"""Progress reporting types."""

from collections.abc import Callable


ProgressCallback = Callable[[float, str], None]
"""Callback receiving (percent 0-100, status message)."""


def clamp_progress(value: float) -> float:
    """Clamp progress to [0, 100] to prevent UI overflow."""
    return max(0.0, min(100.0, value))
