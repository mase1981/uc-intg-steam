"""
Configuration management for Steam integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import json
import logging
import os
from typing import Any

_LOG = logging.getLogger(__name__)


class SteamConfig:
    """Configuration manager for Steam integration - matching Xbox Live pattern."""

    def __init__(self):
        """Initialize configuration manager."""
        self.steam_api_key: str = ""
        self.steam_id: str = ""
        self.update_interval: int = 60

    async def load(self, api) -> None:
        """Load configuration from API config directory."""
        try:
            config_file = os.path.join(api.config_dir_path, "config.json")
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    self.steam_api_key = data.get("steam_api_key", "")
                    self.steam_id = data.get("steam_id", "")
                    self.update_interval = data.get("update_interval", 60)
                    _LOG.info("✅ Configuration loaded from %s", config_file)
            else:
                _LOG.info("No existing configuration file found")
        except Exception as e:
            _LOG.error("Error loading configuration: %s", e)

    async def save(self, api) -> None:
        """Save configuration to API config directory."""
        try:
            os.makedirs(api.config_dir_path, exist_ok=True)
            config_file = os.path.join(api.config_dir_path, "config.json")
            
            data = {
                "steam_api_key": self.steam_api_key,
                "steam_id": self.steam_id,
                "update_interval": self.update_interval
            }
            
            with open(config_file, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)
                _LOG.info("✅ Configuration saved to %s", config_file)
        except Exception as e:
            _LOG.error("Error saving configuration: %s", e)
            raise

    def is_configured(self) -> bool:
        """Check if required configuration is present."""
        return bool(self.steam_api_key and self.steam_id)