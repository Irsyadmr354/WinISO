"""Dependency auto-installer (Module 3)."""

from winiso_toolkit.deps.installer import (
    DependencyInstaller,
    DependencyStatus,
    ensure_dependencies,
)

__all__ = ["DependencyInstaller", "DependencyStatus", "ensure_dependencies"]
