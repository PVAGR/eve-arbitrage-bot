#!/usr/bin/env python3
"""
EVE Online Arbitrage Bot
Entry point for all commands.

Usage:
  python run.py scan                          # Run a full market scan
  python run.py scan --regions Jita Amarr     # Scan specific region pair
  python run.py top 20                        # Show top 20 opportunities
  python run.py lookup "Tritanium"            # Price check an item
  python run.py inventory list                # Show your inventory
  python run.py inventory add "Tritanium" 10000 5.50
  python run.py web                           # Start web dashboard
  python run.py web --port 8080
"""
import sys
import os

# Ensure src/ is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from cli.main import cli

if __name__ == "__main__":
    cli()
