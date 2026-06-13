"""
Version and application metadata for AcoustiCAD.

Version single-source-of-truth is the `VERSION` file at the project root
(read once at import). Bumping is a one-place edit: update `VERSION`, add a
`CHANGELOG.md` entry, optionally `git tag vX.Y.Z`.
"""

import re
import sys
from pathlib import Path


def _version_file_path() -> Path:
    """Locate the VERSION file in both source and PyInstaller-frozen runs."""
    # In a PyInstaller bundle, data files live under sys._MEIPASS.
    # The .spec must list VERSION in `datas` for this to resolve when frozen.
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "VERSION"
    return Path(__file__).resolve().parent / "VERSION"


def _read_version() -> str:
    try:
        return _version_file_path().read_text(encoding="utf-8").strip()
    except (FileNotFoundError, OSError):
        # Fail-soft: unknown is loud enough to notice but doesn't crash the app
        return "0.0.0-unknown"


def _parse_version(v: str):
    """Parse `MAJOR.MINOR.PATCH[-prerelease]` into a tuple, prerelease may be None."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$", v)
    if not match:
        return (0, 0, 0, "unknown")
    major, minor, patch, prerelease = match.groups()
    return (int(major), int(minor), int(patch), prerelease)


__version__ = _read_version()
__version_info__ = _parse_version(__version__)

__author__ = "Free Forge Labs"
__email__ = "support@freeforgelabs.com"
__license__ = "MIT"
__copyright__ = "Copyright 2026 Free Forge Labs"
__description__ = "Professional audio system design tool for commercial audio systems"
__url__ = "https://github.com/FreeForgeLabs/AcoustiCAD"

# Build information (populated by CI if/when wired up)
__build_date__ = None
__build_number__ = None
__git_hash__ = None

# Minimum requirements
__python_requires__ = ">=3.8"
__qt_version__ = "5.15.0"

# Application metadata for installers and about dialogs
APP_NAME = "AcoustiCAD"
APP_DISPLAY_NAME = "AcoustiCAD"
APP_ORGANIZATION = "Free Forge Labs"
APP_DOMAIN = "freeforgelabs.com"
APP_ID = "com.freeforgelabs.acousticad"  # Used for installers / macOS bundle identifier

# Previous app identity — kept for one-shot settings-dir migration in utils/storage.py
LEGACY_APP_NAME = "AudioSystemDesigner"

# Feature flags for different builds
FEATURES = {
    "pdf_support": True,        # Enable PDF background loading
    "advanced_reports": True,   # Enable detailed reporting
    "cloud_sync": False,        # Future feature
    "plugin_system": False,     # Future feature
    "dev_tools": False,         # Set to True for development builds
}


def get_version_string() -> str:
    """Formatted version string for display — derives from __version_info__."""
    major, minor, patch, prerelease = __version_info__
    base = f"{major}.{minor}.{patch}"
    return f"{base}-{prerelease}" if prerelease else base


def get_build_info() -> dict:
    """Build information if available."""
    info = {
        "version": __version__,
        "build_date": __build_date__,
        "build_number": __build_number__,
        "git_hash": __git_hash__,
        "python_version": __python_requires__,
    }
    return {k: v for k, v in info.items() if v is not None}


def is_development_build() -> bool:
    return "dev" in __version__.lower() or "alpha" in __version__.lower()


def is_beta_build() -> bool:
    return "beta" in __version__.lower() or "rc" in __version__.lower()


def is_stable_release() -> bool:
    return not (is_development_build() or is_beta_build())
