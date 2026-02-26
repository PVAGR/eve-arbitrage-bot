#!/usr/bin/env python3
"""
EVE Online Arbitrage Bot
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
"""
import sys
import os

# Add src/ to path only when running as a script (PyInstaller handles it when frozen)
if not getattr(sys, "frozen", False):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments: launch the interactive TUI
        from tui.main import run_tui
        run_tui()
    else:
        # Arguments passed: use the CLI
        from cli.main import cli
        cli()
