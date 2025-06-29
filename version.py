"""
Version information for TXT to EPUB Converter
"""

__version__ = "0.1.0"
__version_info__ = tuple(map(int, __version__.split('.')))

# Release information
__author__ = "AI Development Team"
__email__ = ""
__license__ = "MIT"
__copyright__ = "Copyright (c) 2025 TXT to EPUB Converter"

# Project information
__title__ = "TXT to EPUB Converter"
__description__ = "An intelligent tool for converting TXT files to EPUB format with smart chapter detection"
__url__ = "https://github.com/your-username/txt-to-epub"

# Build information
__build_date__ = "2025-01-26"
__python_requires__ = ">=3.10"

def get_version():
    """Get the current version string."""
    return __version__

def get_version_info():
    """Get the current version info tuple."""
    return __version_info__ 