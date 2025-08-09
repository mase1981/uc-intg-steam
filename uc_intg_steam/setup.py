import logging
import aiohttp
from ucapi import (
    DriverSetupRequest,
    AbortDriverSetup,
    SetupComplete,
    SetupError,
    IntegrationSetupError,
    UserDataResponse,
    UserConfirmationResponse,
)

import uc_intg_steam.config as steam_config

_LOG = logging.getLogger("STEAM_SETUP")

class SteamSetup:
    """Steam integration setup handler."""
    
    def __init__(self, api, config: steam_config.SteamConfig, on_setup_complete):
        self.api = api
        self.config = config
        self.on_setup_complete = on_setup_complete

    async def handle_command(self, request):
        """Handle setup commands from the Remote Two."""
        _LOG.info(f"Handling setup command: {type(request)}")
        
        if isinstance(request, DriverSetupRequest):
            return await self._handle_driver_setup_request(request)
        
        if isinstance(request, UserDataResponse):
            return await self._handle_user_data_response(request)
            
        if isinstance(request, UserConfirmationResponse):
            return await self._handle_user_confirmation_response(request)
            
        if isinstance(request, AbortDriverSetup):
            return await self._handle_abort_setup(request)
        
        _LOG.warning(f"Unhandled setup request type: {type(request)}")
        return SetupError(IntegrationSetupError.OTHER)

    async def _handle_driver_setup_request(self, request: DriverSetupRequest):
        """Handle initial driver setup request."""
        _LOG.info("Processing driver setup request")
        
        steam_api_key = request.setup_data.get("steam_api_key", "").strip()
        steam_id = request.setup_data.get("steam_id", "").strip()
        
        if not steam_api_key:
            _LOG.error("Missing Steam API key")
            return SetupError(IntegrationSetupError.OTHER)
            
        if not steam_id:
            _LOG.error("Missing Steam ID")
            return SetupError(IntegrationSetupError.OTHER)
        
        try:
            steam_id_int = int(steam_id)
            if steam_id_int <= 0:
                raise ValueError("Invalid Steam ID")
        except ValueError:
            _LOG.error(f"Invalid Steam ID format: {steam_id}")
            return SetupError(IntegrationSetupError.OTHER)
        
        if not await self._test_steam_api_connection(steam_api_key, steam_id):
            _LOG.error("Failed to connect to Steam API with provided credentials")
            return SetupError(IntegrationSetupError.AUTHORIZATION_ERROR)
        
        self.config.steam_api_key = steam_api_key
        self.config.steam_id = steam_id
        
        try:
            await self.config.save(self.api)
            _LOG.info("Configuration saved successfully")
            await self.on_setup_complete()
            return SetupComplete()
        except Exception as e:
            _LOG.error(f"Failed to save configuration: {e}")
            return SetupError(IntegrationSetupError.OTHER)

    async def _handle_user_data_response(self, request: UserDataResponse):
        """Handle user data input during setup."""
        _LOG.info("Processing user data response")
        return SetupError(IntegrationSetupError.OTHER)

    async def _handle_user_confirmation_response(self, request: UserConfirmationResponse):
        """Handle user confirmation during setup."""
        _LOG.info("Processing user confirmation response")
        return SetupError(IntegrationSetupError.OTHER)

    async def _handle_abort_setup(self, request: AbortDriverSetup):
        """Handle setup abortion."""
        _LOG.info(f"Setup aborted: {request.error}")
        return

    async def _test_steam_api_connection(self, api_key: str, steam_id: str) -> bool:
        """Test if we can connect to Steam API with provided credentials."""
        try:
            url = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
            params = {
                "key": api_key,
                "steamids": steam_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        players = data.get("response", {}).get("players", [])
                        if players:
                            _LOG.info(f"Steam API test successful for user: {players[0].get('personaname', 'Unknown')}")
                            return True
                        else:
                            _LOG.error("Steam API returned no player data")
                            return False
                    else:
                        _LOG.error(f"Steam API test failed with status: {response.status}")
                        return False
                        
        except Exception as e:
            _LOG.error(f"Steam API test failed: {e}")
            return False