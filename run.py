#!/usr/bin/env python3
"""
EVE Online Personal Tracker & Arbitrage Bot
Entry point.

Double-click or run with no arguments → interactive menu (TUI).

CLI usage (for scripting):
  python run.py scan                          # Run a full market scan
  python run.py scan --regions Jita Amarr     # Scan specific region pair
  python run.py top 20                        # Show top 20 opportunities
  python run.py lookup "Tritanium"            # Price check an item
  python run.py inventory list                # Show your inventory
  python run.py inventory add "Tritanium" 10000 5.50
  python run.py inventory update ID QTY
  python run.py inventory remove ID
  python run.py web                           # Start web dashboard
  python run.py web --port 8080
  python run.py health                        # Check system health
  python run.py backup                        # Create manual backup
  python run.py version                       # Show version info
"""
import sys
import os

# Add src/ to path only when running as a script (PyInstaller handles it when frozen)
if not getattr(sys, "frozen", False):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

def validate_environment():
    """Validate environment and configuration before starting."""
    from utils.logging import setup_logging
    from utils.security import validate_config
    from config import load_config
    from version import __version__, get_version_string
    
    logger = setup_logging("eve-tracker")
    logger.info(get_version_string())
    
    # Validate config
    try:
        config = load_config()
        is_valid, errors = validate_config(config)
        if not is_valid:
            logger.warning("Configuration validation warnings:")
            for error in errors:
                logger.warning(f"  - {error}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        logger.info("Run 'python setup_wizard.py' to create a valid config")
        sys.exit(1)
    
    return logger

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments: launch the interactive TUI
        logger = validate_environment()
        logger.info("Starting interactive menu...")
        from tui.main import run_tui
        run_tui()
    else:
        # Arguments passed: use the CLI
        command = sys.argv[1].lower()
        
        # Special commands that don't need full validation
        if command == "version":
            from version import get_version_string, get_full_version_info
            print(get_version_string())
            info = get_full_version_info()
            print(f"\nBuild Date: {info['build_date']}")
            print(f"Python: {info['python_requires']}")
            print("\nEnabled Features:")
            for feature, enabled in info['features'].items():
                status = "✓" if enabled else "✗"
                print(f"  {status} {feature}")
            sys.exit(0)
        
        # Validate environment for other commands
        logger = validate_environment()
        
        # Handle special commands
        if command == "health":
            from utils.health import get_system_health, format_uptime
            health = get_system_health()
            print(f"\nSystem Health: {health.status.upper()}")
            print(f"Uptime: {format_uptime(health.uptime_seconds)}")
            print(f"\nResources:")
            print(f"  CPU: {health.cpu_percent:.1f}%")
            print(f"  Memory: {health.memory_percent:.1f}% ({health.memory_mb:.0f} MB)")
            print(f"  Disk: {health.disk_percent:.1f}%")
            print(f"\nComponents:")
            print(f"  {'✓' if health.database_ok else '✗'} Database")
            print(f"  {'✓' if health.esi_api_ok else '✗'} ESI API")
            print(f"  {'✓' if health.character_tracking_ok else '✗'} Character Tracking")
            print(f"  {'✓' if health.wormhole_tracking_ok else '✗'} Wormhole Tracking")
            print(f"  {'✓' if health.twitch_integration_ok else '✗'} Twitch Integration")
            if health.errors:
                print(f"\nErrors:")
                for error in health.errors:
                    print(f"  ✗ {error}")
            sys.exit(0 if health.status == "healthy" else 1)
        
        elif command == "backup":
            from utils.backup import get_backup_manager
            print("Creating backup...")
            manager = get_backup_manager()
            manager.backup_databases()
            manager.backup_config()
            print("✓ Backup created successfully")
            backups = manager.list_backups()
            print(f"\nTotal backups: {len(backups)}")
            if backups:
                latest = backups[0]
                print(f"Latest: {latest['name']} ({latest['created_str']})")
            sys.exit(0)
        
        # Use the CLI for regular commands
        from cli.main import cli
        cli()
