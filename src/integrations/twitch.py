"""
Twitch Integration for EVE Online streaming.

Updates your Twitch stream title/game with current EVE activity.
Shows chat notifications for major events (rare loot, big trades, etc.).
Optional: chat bot commands for viewers to see your stats.
"""
from __future__ import annotations

import requests
import time
import json
import os
from typing import Optional
from dataclasses import dataclass

TWITCH_AUTH_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_API_URL = "https://api.twitch.tv/helix"

CONFIG_FILE = "data/twitch_config.json"


@dataclass
class TwitchConfig:
    client_id: str
    client_secret: str
    broadcaster_id: str
    access_token: str = ""
    token_expires_at: float = 0.0


class TwitchIntegration:
    """Handles Twitch API interactions."""
    
    def __init__(self, config: TwitchConfig):
        self.config = config
        self.session = requests.Session()
        self._ensure_valid_token()
    
    def _ensure_valid_token(self):
        """Ensure we have a valid access token."""
        if time.time() < self.config.token_expires_at - 300:  # 5 min buffer
            return
        
        # Get app access token (for updating channel info)
        data = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "grant_type": "client_credentials",
        }
        
        try:
            resp = requests.post(TWITCH_AUTH_URL, data=data, timeout=10)
            resp.raise_for_status()
            token_data = resp.json()
            
            self.config.access_token = token_data["access_token"]
            self.config.token_expires_at = time.time() + token_data["expires_in"]
            self._save_config()
            
            # Update session headers
            self.session.headers.update({
                "Client-ID": self.config.client_id,
                "Authorization": f"Bearer {self.config.access_token}",
            })
        except Exception as e:
            print(f"Failed to get Twitch token: {e}")
    
    def _save_config(self):
        """Save config to disk."""
        os.makedirs("data", exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump({
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "broadcaster_id": self.config.broadcaster_id,
                "access_token": self.config.access_token,
                "token_expires_at": self.config.token_expires_at,
            }, f, indent=2)
    
    def update_stream_title(self, title: str) -> bool:
        """
        Update your Twitch stream title.
        Returns True if successful.
        """
        self._ensure_valid_token()
        
        url = f"{TWITCH_API_URL}/channels"
        params = {"broadcaster_id": self.config.broadcaster_id}
        data = {"title": title}
        
        try:
            resp = self.session.patch(url, params=params, json=data, timeout=10)
            resp.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to update stream title: {e}")
            return False
    
    def update_game(self, game_id: str = "20746") -> bool:
        """
        Update the game/category for your stream.
        Default is EVE Online (game_id=20746).
        Returns True if successful.
        """
        self._ensure_valid_token()
        
        url = f"{TWITCH_API_URL}/channels"
        params = {"broadcaster_id": self.config.broadcaster_id}
        data = {"game_id": game_id}
        
        try:
            resp = self.session.patch(url, params=params, json=data, timeout=10)
            resp.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to update game: {e}")
            return False
    
    def get_stream_status(self) -> Optional[dict]:
        """
        Get current stream status.
        Returns dict with stream info if live, None if offline.
        """
        self._ensure_valid_token()
        
        url = f"{TWITCH_API_URL}/streams"
        params = {"user_id": self.config.broadcaster_id}
        
        try:
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("data"):
                return data["data"][0]
            return None
        except Exception as e:
            print(f"Failed to get stream status: {e}")
            return None
    
    def is_live(self) -> bool:
        """Check if stream is currently live."""
        return self.get_stream_status() is not None
    
    def create_marker(self, description: str = "") -> bool:
        """
        Create a stream marker (for VODs).
        Useful for marking important events.
        Returns True if successful.
        """
        self._ensure_valid_token()
        
        url = f"{TWITCH_API_URL}/streams/markers"
        data = {"user_id": self.config.broadcaster_id}
        if description:
            data["description"] = description[:140]  # Twitch limit
        
        try:
            resp = self.session.post(url, json=data, timeout=10)
            resp.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to create marker: {e}")
            return False
    
    def auto_update_title(self, character_name: str, activity: str, location: str):
        """
        Auto-generate and update stream title based on current activity.
        
        Example:
          character_name: "PVAGR"
          activity: "Mining"
          location: "J123456 (Wormhole)"
          Result: "EVE Online - PVAGR Mining in J123456 (Wormhole)"
        """
        title = f"EVE Online - {character_name} {activity} in {location}"
        self.update_stream_title(title)


def load_twitch_config() -> Optional[TwitchConfig]:
    """Load Twitch config from file."""
    if not os.path.exists(CONFIG_FILE):
        return None
    
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
        return TwitchConfig(
            client_id=data["client_id"],
            client_secret=data["client_secret"],
            broadcaster_id=data["broadcaster_id"],
            access_token=data.get("access_token", ""),
            token_expires_at=data.get("token_expires_at", 0.0),
        )
    except Exception:
        return None


def setup_twitch_config(client_id: str, client_secret: str, broadcaster_id: str):
    """Create and save Twitch config."""
    config = TwitchConfig(
        client_id=client_id,
        client_secret=client_secret,
        broadcaster_id=broadcaster_id,
    )
    
    os.makedirs("data", exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump({
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "broadcaster_id": config.broadcaster_id,
        }, f, indent=2)
    
    return config


def get_twitch_integration() -> Optional[TwitchIntegration]:
    """Get TwitchIntegration instance if configured."""
    config = load_twitch_config()
    if not config:
        return None
    
    return TwitchIntegration(config)
