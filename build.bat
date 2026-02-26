@echo off
:: ============================================================
::  EVE Arbitrage Bot — Windows .exe builder
::  Run this once to produce dist\EVEArbitrageBot.exe
:: ============================================================

echo [1/3] Installing build dependencies...
pip install -r requirements.txt pyinstaller --quiet
if errorlevel 1 (
    echo ERROR: pip install failed. Make sure Python and pip are on your PATH.
    pause & exit /b 1
)

echo [2/3] Building exe with PyInstaller...
pyinstaller ^
  --onefile ^
  --name EVEArbitrageBot ^
  --icon NONE ^
  --paths src ^
  --add-data "src\web\templates;templates" ^
  --add-data "src\web\static;static" ^
  --collect-all flask ^
  --collect-all werkzeug ^
  --collect-all jinja2 ^
  --collect-all click ^
  --collect-all rich ^
  --collect-all psutil ^
  --hidden-import yaml ^
  --hidden-import requests ^
  --hidden-import urllib3 ^
  --hidden-import certifi ^
  --hidden-import charset_normalizer ^
  --hidden-import idna ^
  --hidden-import itsdangerous ^
  --hidden-import blinker ^
  --hidden-import markupsafe ^
  --hidden-import pygments ^
  --hidden-import sqlite3 ^
  --hidden-import psutil ^
  --hidden-import psutil._pswindows ^
  --hidden-import threading ^
  --hidden-import dataclasses ^
  --hidden-import json ^
  --hidden-import datetime ^
  --hidden-import hashlib ^
  --hidden-import secrets ^
  --hidden-import webbrowser ^
  run.py

if errorlevel 1 (
    echo ERROR: PyInstaller build failed. See output above.
    pause & exit /b 1
)

echo [3/3] Preparing distribution package...
copy /Y config.yaml dist\config.yaml >nul
copy /Y README.md dist\README.md >nul
copy /Y SETUP_GUIDE.md dist\SETUP_GUIDE.md >nul
copy /Y CHANGELOG.md dist\CHANGELOG.md >nul
copy /Y RELEASE_NOTES.md dist\RELEASE_NOTES.md >nul
copy /Y setup.bat dist\setup.bat >nul
copy /Y quick_start.bat dist\quick_start.bat >nul

:: Create data directories
mkdir dist\data 2>nul
mkdir dist\data\logs 2>nul
mkdir dist\data\backups 2>nul
mkdir dist\data\backups\config 2>nul
mkdir dist\data\backups\databases 2>nul

echo.
echo ============================================================
echo  Build complete!
echo.
echo.
echo ============================================================
echo  Build complete!
echo  Your exe:      dist\EVEArbitrageBot.exe
echo  
echo  Documentation:
echo    - dist\README.md         (overview)
echo    - dist\SETUP_GUIDE.md    (detailed setup)
echo    - dist\CHANGELOG.md      (version history)
echo    - dist\RELEASE_NOTES.md  (release info)
echo.
echo  Configuration:
echo    - dist\config.yaml       (edit before first run)
echo    - dist\setup.bat         (run setup wizard)
echo.
echo  Quick Start:
echo    1. Run dist\quick_start.bat (auto-setup + launch)
echo    2. Or double-click dist\EVEArbitrageBot.exe
echo    3. Or run 'dist\EVEArbitrageBot.exe web' for dashboard
echo.
echo  The app creates a data\ folder for:
echo    - Databases (eve_arbitrage.db, wormholes.db)
echo    - Logs (data\logs\)
echo    - Backups (data\backups\)
echo ============================================================
pause
