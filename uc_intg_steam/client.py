"""
Steam API client with caching mechanism similar to Xbox Live integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any, Optional
import aiohttp
from asyncio_throttle import Throttler

_LOG = logging.getLogger(__name__)

# Global cache for game artwork - similar to Xbox Live's ARTWORK_CACHE
STEAM_ARTWORK_CACHE = {}
STEAM_DATA_CACHE = {
    "currently_playing": None,
    "friends_data": None,
    "last_update": 0
}


class SteamAPIError(Exception):
    """Steam API error."""
    pass


class SteamClient:
    """Steam API client with Xbox Live-style caching."""

    def __init__(self, api_key: str, steam_id: str):
        """Initialize Steam client."""
        self.api_key = api_key
        self.steam_id = steam_id
        self.base_url = "http://api.steampowered.com"
        self.session: Optional[aiohttp.ClientSession] = None
        self.throttler = Throttler(rate_limit=1, period=1)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self):
        """Create HTTP session."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
            _LOG.debug("Steam client session created")

    async def disconnect(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
            _LOG.debug("Steam client session closed")

    async def _make_request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """Make throttled API request with better error handling."""
        if not self.session:
            await self.connect()

        params.update({"key": self.api_key, "format": "json"})
        url = f"{self.base_url}/{endpoint}"

        async with self.throttler:
            try:
                _LOG.debug("Making Steam API request: %s", endpoint)
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 401:
                        raise SteamAPIError("Invalid API key")
                    elif response.status == 403:
                        raise SteamAPIError("Access denied - check Steam ID and privacy settings")
                    elif response.status in [502, 503, 504]:
                        # Steam server errors - use cached data if available
                        raise SteamAPIError(f"Steam servers temporarily unavailable (HTTP {response.status})")
                    else:
                        raise SteamAPIError(f"API request failed with status {response.status}")
            except aiohttp.ClientError as e:
                raise SteamAPIError(f"Network error: {e}")
            except Exception as e:
                raise SteamAPIError(f"Unexpected error: {e}")

    async def get_player_summaries(self, steam_ids: Optional[list[str]] = None) -> dict[str, Any]:
        """Get player summaries."""
        if steam_ids is None:
            steam_ids = [self.steam_id]
        
        params = {"steamids": ",".join(steam_ids)}
        return await self._make_request("ISteamUser/GetPlayerSummaries/v0002/", params)

    async def get_friend_list(self) -> dict[str, Any]:
        """Get friend list."""
        params = {
            "steamid": self.steam_id,
            "relationship": "friend"
        }
        
        try:
            return await self._make_request("ISteamUser/GetFriendList/v0001/", params)
        except SteamAPIError as e:
            if "403" in str(e) or "Forbidden" in str(e) or "Access denied" in str(e):
                _LOG.warning("Friends list not accessible - profile may be private")
                return {"friendslist": {"friends": []}}
            else:
                raise

    async def get_currently_playing(self) -> tuple[Optional[dict[str, Any]], Optional[str]]:
        """Get currently playing game with caching to prevent flickering."""
        try:
            data = await self.get_player_summaries()
            
            if "response" not in data or "players" not in data["response"]:
                # Return cached data if API fails
                if STEAM_DATA_CACHE["currently_playing"]:
                    _LOG.debug("Using cached currently playing data due to API issues")
                    return STEAM_DATA_CACHE["currently_playing"]
                return None, None
                
            players = data["response"]["players"]
            if not players:
                if STEAM_DATA_CACHE["currently_playing"]:
                    _LOG.debug("Using cached data - no players returned")
                    return STEAM_DATA_CACHE["currently_playing"]
                return None, None
                
            player = players[0]
            
            if "gameid" in player and "gameextrainfo" in player:
                game_name = player["gameextrainfo"]
                appid = player["gameid"]
                
                # Check cache for artwork URL first (like Xbox Live does)
                if game_name in STEAM_ARTWORK_CACHE:
                    image_url = STEAM_ARTWORK_CACHE[game_name]
                    _LOG.debug(f"Using cached artwork for '{game_name}'")
                else:
                    # Cache the Steam CDN URL for this game
                    image_url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/library_600x900.jpg"
                    STEAM_ARTWORK_CACHE[game_name] = image_url
                    _LOG.debug(f"Cached new artwork URL for '{game_name}': {image_url}")
                
                game_data = {
                    "appid": appid,
                    "name": game_name,
                    "personastate": player.get("personastate", 0)
                }
                
                result = (game_data, image_url)
                
                # Cache the successful result (like Xbox Live pattern)
                STEAM_DATA_CACHE["currently_playing"] = result
                return result
            else:
                # User not playing - cache this state too
                result = (None, None)
                STEAM_DATA_CACHE["currently_playing"] = result
                return result
                
        except SteamAPIError as e:
            if "temporarily unavailable" in str(e) or "502" in str(e) or "503" in str(e):
                # Use cache during temporary Steam server issues (like Xbox Live does)
                if STEAM_DATA_CACHE["currently_playing"]:
                    _LOG.debug(f"Using cached data due to Steam server issues: {e}")
                    return STEAM_DATA_CACHE["currently_playing"]
                else:
                    _LOG.warning("Steam servers temporarily unavailable and no cache available")
                    return None, None
            else:
                _LOG.error("Error getting currently playing game: %s", e)
                return None, None
        except Exception as e:
            _LOG.error("Unexpected error getting currently playing game: %s", e)
            return None, None

    async def get_online_friends(self) -> list[dict[str, Any]]:
        """Get list of online friends with caching."""
        try:
            friends_data = await self.get_friend_list()
            
            if "friendslist" not in friends_data or "friends" not in friends_data["friendslist"]:
                # Use cache if API fails (like Xbox Live pattern)
                if STEAM_DATA_CACHE["friends_data"]:
                    _LOG.debug("Using cached friends data due to API issues")
                    return STEAM_DATA_CACHE["friends_data"]
                _LOG.info("No friends list data available")
                return []
                
            friend_steam_ids = [friend["steamid"] for friend in friends_data["friendslist"]["friends"]]
            
            if not friend_steam_ids:
                result = []
                STEAM_DATA_CACHE["friends_data"] = result
                return result
                
            batch_size = 100
            all_online_friends = []
            
            for i in range(0, len(friend_steam_ids), batch_size):
                batch_ids = friend_steam_ids[i:i + batch_size]
                
                try:
                    summaries_data = await self.get_player_summaries(batch_ids)
                    
                    if "response" not in summaries_data or "players" not in summaries_data["response"]:
                        continue
                        
                    for player in summaries_data["response"]["players"]:
                        if player.get("personastate", 0) > 0:
                            friend_info = {
                                "steamid": player["steamid"],
                                "personaname": player.get("personaname", "Unknown"),
                                "personastate": player.get("personastate", 0),
                                "gameextrainfo": player.get("gameextrainfo", None),
                                "gameid": player.get("gameid", None)
                            }
                            all_online_friends.append(friend_info)
                            
                except Exception as e:
                    _LOG.error("Error processing friend batch: %s", e)
                    continue
            
            # Cache successful result (like Xbox Live)
            STEAM_DATA_CACHE["friends_data"] = all_online_friends
            return all_online_friends
            
        except SteamAPIError as e:
            if "temporarily unavailable" in str(e) or "502" in str(e) or "503" in str(e):
                if STEAM_DATA_CACHE["friends_data"]:
                    _LOG.debug("Using cached friends due to Steam server issues")
                    return STEAM_DATA_CACHE["friends_data"]
            _LOG.error("Error getting online friends: %s", e)
            return []
        except Exception as e:
            _LOG.error("Unexpected error getting online friends: %s", e)
            return []

    @staticmethod
    def get_game_image_url(appid: str) -> str:
        """Get game header image URL."""
        return f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg"

    @staticmethod
    def get_persona_state_text(state: int) -> str:
        """Convert persona state to readable text."""
        states = {
            0: "Offline", 1: "Online", 2: "Busy", 3: "Away",
            4: "Snooze", 5: "Looking to trade", 6: "Looking to play"
        }
        return states.get(state, "Unknown")

    @staticmethod
    def get_steam_logo_url() -> str:
        """Get high-resolution Steam logo URL (cached like Xbox Live artwork)."""
        # Using Steam's official high-res logo from their brand assets
        return "https://store.steampowered.com/public/shared/images/header/logo_steam.svg"
