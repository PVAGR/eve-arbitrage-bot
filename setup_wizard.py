#!/usr/bin/env python3
"""
Setup wizard for EVE Personal Tracker & Arbitrage Bot.
Helps configure ESI, Twitch, and other settings interactively.
"""
import os
import sys
import yaml

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def get_input(prompt, default=None):
    """Get user input with optional default."""
    if default:
        result = input(f"{prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"{prompt}: ").strip()

def get_yes_no(prompt, default=True):
    """Get yes/no input."""
    default_str = "Y/n" if default else "y/N"
    result = input(f"{prompt} [{default_str}]: ").strip().lower()
    if not result:
        return default
    return result in ('y', 'yes')

def setup_character():
    """Setup EVE character tracking."""
    print_header("EVE Character Tracking Setup")
    
    print("To track your character, you need an ESI Client ID:")
    print("  1. Go to: https://developers.eveonline.com/")
    print("  2. Click 'Manage Applications' → 'Create New Application'")
    print("  3. Set callback URL to: http://localhost:8888/callback")
    print("  4. Copy your Client ID\n")
    
    enable = get_yes_no("Enable character tracking?", True)
    if not enable:
        return {"character": {"esi_client_id": "YOUR_ESI_CLIENT_ID", "auto_track": False}}
    
    client_id = get_input("Enter your ESI Client ID")
    if not client_id:
        print("⚠️  Skipping character setup")
        return {"character": {"esi_client_id": "YOUR_ESI_CLIENT_ID", "auto_track": False}}
    
    auto_track = get_yes_no("Automatically track your location?", True)
    interval = int(get_input("Tracking interval (seconds)", "60"))
    
    return {
        "character": {
            "esi_client_id": client_id,
            "auto_track": auto_track,
            "track_interval_seconds": interval,
        }
    }

def setup_twitch():
    """Setup Twitch integration."""
    print_header("Twitch Integration Setup")
    
    print("To integrate with Twitch, you need:")
    print("  1. Client ID and Secret from: https://dev.twitch.tv/console/apps")
    print("  2. Your Twitch User ID (Broadcaster ID)")
    print("     Find it at: https://www.streamweasels.com/tools/convert-twitch-username-to-user-id/\n")
    
    enable = get_yes_no("Enable Twitch integration?", False)
    if not enable:
        return {"twitch": {"enabled": False}}
    
    client_id = get_input("Twitch Client ID")
    client_secret = get_input("Twitch Client Secret")
    broadcaster_id = get_input("Your Twitch User ID (Broadcaster ID)")
    
    if not client_id or not client_secret or not broadcaster_id:
        print("⚠️  Incomplete credentials, disabling Twitch")
        return {"twitch": {"enabled": False}}
    
    auto_update = get_yes_no("Auto-update stream title with your activity?", True)
    
    return {
        "twitch": {
            "enabled": True,
            "client_id": client_id,
            "client_secret": client_secret,
            "broadcaster_id": broadcaster_id,
            "auto_update_title": auto_update,
            "update_title_template": "EVE Online - {character_name} {activity} in {location}",
        }
    }

def setup_wormholes():
    """Setup wormhole tracking."""
    print_header("Wormhole Tracking Setup")
    
    enable = get_yes_no("Enable wormhole connection tracking?", True)
    if not enable:
        return {"wormholes": {"enabled": False}}
    
    auto_track = get_yes_no("Auto-track jumps into wormhole systems?", True)
    
    return {
        "wormholes": {
            "enabled": True,
            "auto_track_jumps": auto_track,
            "home_systems": [],
        }
    }

def setup_fees():
    """Setup market fees."""
    print_header("Market Fee Configuration")
    
    print("Configure based on your in-game skills:\n")
    
    broker_buy = float(get_input("Broker fee % when buying (e.g., 3.0 for 3%)", "3.0")) / 100
    broker_sell = float(get_input("Broker fee % when selling", "3.0")) / 100
    sales_tax = float(get_input("Sales tax % (Accounting skill)", "8.0")) / 100
    hauling = float(get_input("Hauling cost per m³ (ISK)", "800"))
    
    return {
        "fees": {
            "broker_fee_buy": broker_buy,
            "broker_fee_sell": broker_sell,
            "sales_tax": sales_tax,
            "hauling_isk_per_m3": hauling,
        }
    }

def setup_filters():
    """Setup profit filters."""
    print_header("Arbitrage Filter Configuration")
    
    min_margin = float(get_input("Minimum profit margin % (e.g., 10 for 10%)", "10"))
    min_profit = float(get_input("Minimum ISK profit per unit (e.g., 1000000 for 1M ISK)", "1000000"))
    max_invest = float(get_input("Max investment per item (0 = unlimited)", "0"))
    min_volume = int(get_input("Minimum volume available", "1"))
    
    return {
        "filters": {
            "min_profit_margin_pct": min_margin,
            "min_net_isk_profit": min_profit,
            "max_investment_per_item": max_invest,
            "min_volume_available": min_volume,
        }
    }

def main():
    print("\n" + "=" * 60)
    print("  EVE Personal Tracker & Arbitrage Bot — Setup Wizard")
    print("=" * 60)
    print("\nThis wizard will help you configure the application.\n")
    
    # Build config
    config = {}
    
    # Character tracking
    config.update(setup_character())
    
    # Twitch
    config.update(setup_twitch())
    
    # Wormholes
    config.update(setup_wormholes())
    
    # Fees
    config.update(setup_fees())
    
    # Filters
    config.update(setup_filters())
    
    # Add default regions and scan settings
    config["regions"] = [
        {"name": "Jita", "id": 10000002},
        {"name": "Amarr", "id": 10000043},
        {"name": "Dodixie", "id": 10000032},
        {"name": "Rens", "id": 10000030},
        {"name": "Hek", "id": 10000042},
    ]
    
    config["scan"] = {
        "cache_ttl_minutes": 5,
        "pairs": [
            ["Jita", "Amarr"],
            ["Jita", "Dodixie"],
            ["Jita", "Rens"],
            ["Jita", "Hek"],
            ["Amarr", "Dodixie"],
            ["Amarr", "Rens"],
        ],
    }
    
    config["web"] = {
        "host": "127.0.0.1",
        "port": 5000,
        "auto_refresh_seconds": 60,
    }
    
    # Save config
    print_header("Saving Configuration")
    
    config_path = "config.yaml"
    backup_path = "config.yaml.backup"
    
    # Backup existing config
    if os.path.exists(config_path):
        print(f"⚠️  Backing up existing config to {backup_path}")
        with open(config_path, 'r') as f:
            old_config = f.read()
        with open(backup_path, 'w') as f:
            f.write(old_config)
    
    # Write new config
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"✅ Configuration saved to {config_path}")
    print("\nYou can now run the application:")
    print("  - Windows: Double-click EVEArbitrageBot.exe")
    print("  - Python:  python run.py")
    print("\nWeb dashboard will be at: http://localhost:5000")
    print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
        sys.exit(1)
