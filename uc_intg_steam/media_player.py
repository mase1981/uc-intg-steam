"""
Steam media player entities.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import (
    MediaPlayer,
    StatusCodes,
    media_player
)

_LOG = logging.getLogger(__name__)


async def steam_command_handler(entity, command: str, params: dict[str, Any] | None = None) -> StatusCodes:
    """Command handler for Steam entities."""
    _LOG.info(f"Steam command received: {command}")

    if command == media_player.Commands.ON:
        _LOG.info("Refreshing Steam data on user command.")
        if hasattr(entity, 'trigger_update'):
            await entity.trigger_update()
        return StatusCodes.OK
    elif command in [media_player.Commands.OFF, media_player.Commands.PLAY_PAUSE]:
        return StatusCodes.OK
    else:
        return StatusCodes.NOT_IMPLEMENTED


class SteamCurrentlyPlayingEntity(MediaPlayer):
    """Steam currently playing game entity."""

    def __init__(self, api=None):
        """Initialize currently playing entity."""
        features = [media_player.Features.ON_OFF]
        
        initial_attributes = {
            media_player.Attributes.STATE: media_player.States.ON,
            media_player.Attributes.MEDIA_TITLE: "Steam - Now Playing",
            media_player.Attributes.MEDIA_ARTIST: "No game detected",
            media_player.Attributes.MEDIA_ALBUM: "Steam",
            media_player.Attributes.MEDIA_IMAGE_URL: "",
        }
        
        super().__init__(
            identifier="steam_currently_playing",
            name="Steam - Now Playing",
            features=features,
            attributes=initial_attributes,
            cmd_handler=steam_command_handler,
            device_class=media_player.DeviceClasses.RECEIVER
        )
        
        self._api = api

    async def trigger_update(self):
        """Trigger an immediate update when user presses ON button."""
        _LOG.info("User triggered Steam currently playing update")

    async def update_game_info(self, game_info: dict[str, Any]) -> None:
        """Update entity with current game information."""
        new_attributes = self.attributes.copy()
        
        try:
            if game_info and "name" in game_info:
                new_attributes.update({
                    media_player.Attributes.STATE: media_player.States.PLAYING,
                    media_player.Attributes.MEDIA_TITLE: "Steam - Now Playing",
                    media_player.Attributes.MEDIA_ARTIST: game_info["name"],
                    media_player.Attributes.MEDIA_ALBUM: "Playing on Steam",
                    media_player.Attributes.MEDIA_IMAGE_URL: game_info.get("image_url", ""),
                })
                _LOG.info("Now playing: %s", game_info["name"])
            else:
                new_attributes.update({
                    media_player.Attributes.STATE: media_player.States.OFF,
                    media_player.Attributes.MEDIA_TITLE: "Steam - Now Playing",
                    media_player.Attributes.MEDIA_ARTIST: "No game detected", 
                    media_player.Attributes.MEDIA_ALBUM: "Steam",
                    media_player.Attributes.MEDIA_IMAGE_URL: "",
                })
                _LOG.debug("No game currently playing")
                    
        except Exception as e:
            _LOG.error("Error updating currently playing entity: %s", e)
            new_attributes.update({
                media_player.Attributes.STATE: media_player.States.UNKNOWN,
                media_player.Attributes.MEDIA_TITLE: "Steam - Now Playing",
                media_player.Attributes.MEDIA_ARTIST: "Steam API Error",
                media_player.Attributes.MEDIA_ALBUM: "Check connection",
                media_player.Attributes.MEDIA_IMAGE_URL: "",
            })

        self.attributes.update(new_attributes)
        
        if self._api and self._api.configured_entities.contains(self.id):
            self._api.configured_entities.update_attributes(self.id, self.attributes)


class SteamFriendsEntity(MediaPlayer):
    """Steam friends list entity."""

    def __init__(self, api=None):
        """Initialize friends entity."""
        features = [media_player.Features.ON_OFF]
        
        # Steam logo for friends entity
        steam_logo_url = "https://store.steampowered.com/favicon.ico"
        
        initial_attributes = {
            media_player.Attributes.STATE: media_player.States.ON,
            media_player.Attributes.MEDIA_TITLE: "Steam - Friends",
            media_player.Attributes.MEDIA_ARTIST: "Loading...",
            media_player.Attributes.MEDIA_ALBUM: "Fetching friends...",
            media_player.Attributes.MEDIA_IMAGE_URL: steam_logo_url,
        }
        
        super().__init__(
            identifier="steam_friends",
            name="Steam - Friends",
            features=features,
            attributes=initial_attributes,
            cmd_handler=steam_command_handler,
            device_class=media_player.DeviceClasses.RECEIVER
        )
        
        self._api = api

    async def trigger_update(self):
        """Trigger an immediate update when user presses ON button."""
        _LOG.info("User triggered Steam friends update")

    async def update_friends_info(self, friends_info: dict[str, Any]) -> None:
        """Update entity with friends information."""
        new_attributes = self.attributes.copy()
        steam_logo_url = "https://store.steampowered.com/favicon.ico"
        
        try:
            if friends_info and "online_count" in friends_info:
                online_count = friends_info["online_count"]
                total_count = friends_info.get("total_count", online_count)
                
                new_attributes.update({
                    media_player.Attributes.STATE: media_player.States.PLAYING,
                    media_player.Attributes.MEDIA_TITLE: "Steam - Friends",
                    media_player.Attributes.MEDIA_ARTIST: f"{online_count} friends online",
                    media_player.Attributes.MEDIA_ALBUM: f"Total: {total_count}",
                    media_player.Attributes.MEDIA_IMAGE_URL: steam_logo_url,
                })
                
                _LOG.info("Friends online: %d/%d", online_count, total_count)
            else:
                new_attributes.update({
                    media_player.Attributes.STATE: media_player.States.OFF,
                    media_player.Attributes.MEDIA_TITLE: "Steam - Friends",
                    media_player.Attributes.MEDIA_ARTIST: "No friends data",
                    media_player.Attributes.MEDIA_ALBUM: "Steam",
                    media_player.Attributes.MEDIA_IMAGE_URL: steam_logo_url,
                })
                _LOG.debug("No friends data available")
            
        except Exception as e:
            _LOG.error("Error updating friends entity: %s", e)
            new_attributes.update({
                media_player.Attributes.STATE: media_player.States.UNKNOWN,
                media_player.Attributes.MEDIA_TITLE: "Steam - Friends",
                media_player.Attributes.MEDIA_ARTIST: "Connection Error",
                media_player.Attributes.MEDIA_ALBUM: "Steam",
                media_player.Attributes.MEDIA_IMAGE_URL: steam_logo_url,
            })

        self.attributes.update(new_attributes)
        
        if self._api and self._api.configured_entities.contains(self.id):
            self._api.configured_entities.update_attributes(self.id, self.attributes)