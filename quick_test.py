#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing imports...")
try:
    from config import load_config
    print("✓ Config")
except Exception as e:
    print(f"✗ Config: {e}")

try:
    from models.database import Database
    print("✓ Database")
except Exception as e:
    print(f"✗ Database: {e}")

try:
    from api.esi import ESI
    print("✓ ESI")
except Exception as e:
    print(f"✗ ESI: {e}")

try:
    from version import __version__
    print(f"✓ Version: {__version__}")
except Exception as e:
    print(f"✗ Version: {e}")

try:
    from web.app import app
    print("✓ Web App")
except Exception as e:
    print(f"✗ Web App: {e}")

print("\nDone!")
