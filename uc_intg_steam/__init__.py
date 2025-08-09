"""
Steam Integration for Unfolded Circle Remote Two.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

__version__ = "0.1.0"

# Make key classes available at package level for easier importing
from .config import SteamConfig
from .client import SteamClient
from .media_player import SteamCurrentlyPlayingEntity, SteamFriendsEntity
from .setup import SteamSetup

__all__ = [
    "SteamConfig",
    "SteamClient", 
    "SteamCurrentlyPlayingEntity",
    "SteamFriendsEntity",
    "SteamSetup"
]