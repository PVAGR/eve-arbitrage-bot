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
  --paths src ^
  --add-data "src\web\templates;templates" ^
  --add-data "src\web\static;static" ^
  --collect-all flask ^
  --collect-all werkzeug ^
  --collect-all jinja2 ^
  --collect-all click ^
  --collect-all rich ^
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
  run.py

if errorlevel 1 (
    echo ERROR: PyInstaller build failed. See output above.
    pause & exit /b 1
)

echo [3/3] Copying config.yaml to dist\...
copy /Y config.yaml dist\config.yaml >nul

echo.
echo ============================================================
echo  Build complete!
echo.
echo  Your exe:      dist\EVEArbitrageBot.exe
echo  Config file:   dist\config.yaml  (edit this before running)
echo.
echo  To run:  double-click dist\EVEArbitrageBot.exe
echo           or open a terminal and run it from dist\
echo.
echo  The bot will create a  data\  folder next to the exe
echo  to store its database.
echo ============================================================
pause
