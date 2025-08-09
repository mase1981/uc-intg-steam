import asyncio
import logging
from pathlib import Path
from ucapi import IntegrationAPI, DeviceStates, Events

from uc_intg_steam.config import SteamConfig
from uc_intg_steam.setup import SteamSetup
from uc_intg_steam.client import SteamClient
from uc_intg_steam.media_player import SteamCurrentlyPlayingEntity, SteamFriendsEntity

_LOG = logging.getLogger(__name__)
UPDATE_INTERVAL_SECONDS = 30

try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

API = IntegrationAPI(loop)
CONFIG = SteamConfig()
STEAM_CLIENT: SteamClient | None = None
CURRENTLY_PLAYING_ENTITY: SteamCurrentlyPlayingEntity | None = None
FRIENDS_ENTITY: SteamFriendsEntity | None = None
UPDATE_TASK: asyncio.Task | None = None

async def on_setup_complete():
    """Called when setup is completed successfully."""
    _LOG.info("Setup complete, proceeding to connect.")
    await connect_and_start_client()

async def connect_and_start_client():
    """Initialize Steam client and entities."""
    global STEAM_CLIENT, CURRENTLY_PLAYING_ENTITY, FRIENDS_ENTITY
    
    if not CONFIG.steam_api_key or not CONFIG.steam_id:
        _LOG.error("Missing configuration, cannot connect")
        await API.set_device_state(DeviceStates.ERROR)
        return
    
    try:
        STEAM_CLIENT = SteamClient(
            api_key=CONFIG.steam_api_key,
            steam_id=CONFIG.steam_id
        )
        
        await STEAM_CLIENT.connect()
        
        user_data = await STEAM_CLIENT.get_player_summaries()
        if not user_data or "response" not in user_data:
            _LOG.error("Failed to get user info from Steam API")
            await API.set_device_state(DeviceStates.ERROR)
            return
            
        players = user_data["response"].get("players", [])
        if players:
            username = players[0].get("personaname", "Unknown")
            _LOG.info(f"Connected to Steam API for user: {username}")
        else:
            _LOG.warning("Connected to Steam API but no player data found")
        
        if not CURRENTLY_PLAYING_ENTITY:
            CURRENTLY_PLAYING_ENTITY = SteamCurrentlyPlayingEntity(api=API)
            API.available_entities.add(CURRENTLY_PLAYING_ENTITY)
            _LOG.info("Currently Playing entity created")
            
        if not FRIENDS_ENTITY:
            FRIENDS_ENTITY = SteamFriendsEntity(api=API)
            API.available_entities.add(FRIENDS_ENTITY)
            _LOG.info("Friends entity created")
        
        await API.set_device_state(DeviceStates.CONNECTED)
        _LOG.info("Device state set to CONNECTED")
        
    except Exception as e:
        _LOG.exception("Failed to connect to Steam API", exc_info=e)
        await API.set_device_state(DeviceStates.ERROR)

@API.listens_to(Events.CONNECT)
async def on_connect() -> None:
    """Called when remote connects via WebSocket."""
    _LOG.info("Remote connected via WebSocket")
    if STEAM_CLIENT and CURRENTLY_PLAYING_ENTITY and FRIENDS_ENTITY:
        await API.set_device_state(DeviceStates.CONNECTED)

@API.listens_to(Events.DISCONNECT)
async def on_disconnect() -> None:
    """Called when remote disconnects."""
    _LOG.info("Remote disconnected")

@API.listens_to(Events.SUBSCRIBE_ENTITIES)
async def on_subscribe_entities(entity_ids: list[str]) -> None:
    """Called when the remote UI subscribes to our entities."""
    _LOG.info(f"Received entity subscription for IDs: {entity_ids}")
    
    entities_subscribed = False
    
    if CURRENTLY_PLAYING_ENTITY and CURRENTLY_PLAYING_ENTITY.id in entity_ids:
        API.configured_entities.add(CURRENTLY_PLAYING_ENTITY)
        entities_subscribed = True
        _LOG.info("Currently Playing entity subscribed")
        
    if FRIENDS_ENTITY and FRIENDS_ENTITY.id in entity_ids:
        API.configured_entities.add(FRIENDS_ENTITY)
        entities_subscribed = True
        _LOG.info("Friends entity subscribed")
    
    if entities_subscribed:
        start_update_loop()

def start_update_loop():
    """Start the periodic update loop."""
    global UPDATE_TASK
    if UPDATE_TASK and not UPDATE_TASK.done():
        return
    
    _LOG.info("Starting Steam data update loop...")
    UPDATE_TASK = loop.create_task(update_loop())

async def update_loop():
    """Main update loop for Steam data."""
    while True:
        try:
            if STEAM_CLIENT and (CURRENTLY_PLAYING_ENTITY or FRIENDS_ENTITY):
                _LOG.debug("Fetching Steam data...")
                
                if CURRENTLY_PLAYING_ENTITY and CURRENTLY_PLAYING_ENTITY.id in [e.id for e in API.configured_entities._storage.values()]:
                    game_data, image_url = await STEAM_CLIENT.get_currently_playing()
                    
                    if game_data:
                        game_info = {
                            "name": game_data["name"],
                            "image_url": image_url,
                            "appid": game_data["appid"]
                        }
                    else:
                        game_info = {}
                        
                    await CURRENTLY_PLAYING_ENTITY.update_game_info(game_info)
                
                if FRIENDS_ENTITY and FRIENDS_ENTITY.id in [e.id for e in API.configured_entities._storage.values()]:
                    online_friends = await STEAM_CLIENT.get_online_friends()
                    
                    friends_info = {
                        "online_count": len(online_friends),
                        "total_count": len(online_friends),
                        "friends": online_friends
                    }
                    
                    await FRIENDS_ENTITY.update_friends_info(friends_info)
                    
            else:
                _LOG.warning("Update loop running but client/entities not ready")
                
        except Exception as e:
            _LOG.exception("Error during update loop", exc_info=e)
            
        await asyncio.sleep(UPDATE_INTERVAL_SECONDS)

SETUP_HANDLER = SteamSetup(API, CONFIG, on_setup_complete)

async def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    driver_path = str(Path(__file__).resolve().parent.parent / "driver.json")
    await API.init(driver_path, SETUP_HANDLER.handle_command)
    
    await CONFIG.load(API)
    _LOG.info("Steam Integration Driver is up and discoverable")
    
    if CONFIG.steam_api_key and CONFIG.steam_id:
        _LOG.info("Complete configuration found, attempting auto-connection...")
        await connect_and_start_client()
    else:
        _LOG.info("Incomplete configuration, requiring setup")
        await API.set_device_state(DeviceStates.DISCONNECTED)

if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
        loop.run_forever()
    except KeyboardInterrupt:
        _LOG.info("Driver stopped by user")
    finally:
        if STEAM_CLIENT:
            loop.run_until_complete(STEAM_CLIENT.disconnect())
        loop.close()