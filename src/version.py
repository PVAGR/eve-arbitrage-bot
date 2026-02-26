"""
Version information for EVE Personal Tracker & Arbitrage Bot.
"""

__version__ = "2.0.0"
__version_info__ = (2, 0, 0)
__title__ = "EVE Personal Tracker & Arbitrage Bot"
__description__ = "All-in-one EVE Online companion: character tracking, wormhole mapping, Twitch integration, and market arbitrage"
__author__ = "PVAGR"
__license__ = "MIT"

# Feature flags
FEATURES = {
    "character_tracking": True,
    "wormhole_mapping": True,
    "twitch_integration": True,
    "market_arbitrage": True,
    "auto_backup": True,
    "health_monitoring": True,
    "rate_limiting": True,
}

# Build info
BUILD_DATE = "2026-02-26"
PYTHON_REQUIRES = ">=3.10"

def get_version_string() -> str:
    """Get formatted version string."""
    return f"{__title__} v{__version__}"

def get_full_version_info() -> dict:
    """Get complete version information."""
    return {
        "version": __version__,
        "title": __title__,
        "description": __description__,
        "build_date": BUILD_DATE,
        "python_requires": PYTHON_REQUIRES,
        "features": FEATURES,
    }
