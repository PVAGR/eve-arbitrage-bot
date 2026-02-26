# EVE Online Personal Tracker & Arbitrage Bot — Setup Guide

This comprehensive tool tracks your personal EVE Online character activities, wormhole chains, integrates with Twitch streaming, AND finds profitable arbitrage opportunities across trade hubs.

---

## Quick Start

### Download the Pre-Built Executable

1. Go to **[Releases](https://github.com/PVAGR/eve-arbitrage-bot/releases/tag/latest)**
2. Download **`EVEArbitrageBot.exe`** and **`config.yaml`**
3. Put them in the same folder
4. **Option A**: Run `setup.bat` for interactive configuration wizard
5. **Option B**: Edit `config.yaml` manually (see below)
6. Double-click **`EVEArbitrageBot.exe`**

---

## Setup Wizard (Recommended)

The easiest way to configure everything:

```bash
# Windows
setup.bat

# Or with Python
python setup_wizard.py
```

The wizard will guide you through:
- EVE ESI authentication setup
- Twitch integration (optional)
- Wormhole tracking preferences
- Market fee configuration
- Profit filter settings

---

## Manual Configuration

### 1. EVE Character Tracking (Recommended)

To track your personal character data (location, wallet, transactions, etc.):

#### Get ESI Credentials:
1. Go to https://developers.eveonline.com/
2. Create a new application
3. Set the callback URL to: `http://localhost:8888/callback`
4. Copy your **Client ID**
5. Add to `config.yaml`:

```yaml
character:
  esi_client_id: "your_client_id_here"
  auto_track: true
  track_interval_seconds: 60
```

6. Run the program — it will open your browser for EVE login (first time only)

---

### 2. Twitch Integration (Optional)

Automatically update your stream title and status:

#### Get Twitch Credentials:
1. Go to https://dev.twitch.tv/console/apps
2. Create a new application
3. Copy your **Client ID** and **Client Secret**
4. Get your **Broadcaster ID** (your Twitch user ID)
   - Use: https://www.streamweasels.com/tools/convert-twitch-username-to-user-id/
5. Add to `config.yaml`:

```yaml
twitch:
  enabled: true
  client_id: "your_twitch_client_id"
  client_secret: "your_twitch_client_secret"
  broadcaster_id: "your_twitch_user_id"
  auto_update_title: true
  update_title_template: "EVE Online - {character_name} {activity} in {location}"
```

---

### 3. Wormhole Tracking (Optional)

Track wormhole connections and chains:

```yaml
wormholes:
  enabled: true
  auto_track_jumps: true
  home_systems:
    - name: "J123456"
      system_id: 31000005
      class: "C5"
      statics: ["C5", "NS"]
```

---

### 4. Market Arbitrage Settings

Adjust these to match your in-game skills:

```yaml
fees:
  broker_fee_buy: 0.03       # Based on Broker Relations skill
  broker_fee_sell: 0.03
  sales_tax: 0.08            # Based on Accounting skill
  hauling_isk_per_m3: 800

filters:
  min_profit_margin_pct: 10
  min_net_isk_profit: 1000000
```

---

## Features

### Character Tracking
- **Real-time location** tracking (system, station, ship)
- **Wallet balance** and transaction history
- **Active market orders** monitoring
- **Asset tracking** across all stations
- **Skills and training queue**

### Wormhole Tools
- **Connection mapping** — track all wormhole connections
- **Chain visualization** — see your wormhole chain depth
- **Jump history** — automatic logging of wormhole jumps
- **Favorite systems** — bookmark your home systems
- **Mass/time status** tracking

### Twitch Integration
- **Auto-update stream title** with current activity
- **Live status badge** in dashboard
- **Stream markers** for important events
- **Manual title updates** via web interface

### Market Arbitrage
- **Multi-region scanning** (Jita, Amarr, Dodixie, Rens, Hek)
- **Full fee calculations** (broker fees, sales tax, hauling)
- **Inventory tracking** with profit/loss
- **Price lookup** across all hubs
- **SQLite caching** for performance

---

## Using the Dashboard

Once running, open your browser to: **http://localhost:5000**

### Tabs:

1. **Character** — Your current status, location, wallet, transactions
2. **Wormholes** — Active connections, jump history, chain mapping
3. **Arbitrage** — Market opportunities across regions
4. **Inventory** — Track your stock and profit/loss
5. **Price Lookup** — Compare prices across all hubs

---

## CLI Mode

For automation and scripting:

```bash
# Run market scan
python run.py scan

# Show top opportunities
python run.py top 20

# Price lookup
python run.py lookup "Tritanium"

# Start web dashboard
python run.py web
```

---

## Data Storage

The program creates a `data/` folder next to the exe:

- `eve_arbitrage.db` — Market cache and arbitrage results
- `wormholes.db` — Wormhole connections and history
- `token.json` — Your ESI authentication token
- `twitch_config.json` — Twitch API credentials

---

## Building from Source

```bash
git clone https://github.com/PVAGR/eve-arbitrage-bot.git
cd eve-arbitrage-bot
pip install -r requirements.txt

# Run directly
python run.py

# Build exe
build.bat
```

---

## Security Notes

- **Token storage**: Your ESI token is stored locally in `data/token.json`
- **Scopes**: The app requests all available ESI scopes for full functionality
- **OAuth**: Uses standard OAuth 2.0 PKCE flow (no client secret needed)
- **Twitch**: Uses app access tokens (not user OAuth)

---

## Troubleshooting

### "Character tracking not configured"
- Make sure you've added your `esi_client_id` to `config.yaml`
- Delete `data/token.json` and restart to re-authenticate

### "Twitch integration not configured"
- Verify all three Twitch credentials in `config.yaml`
- Check that your Client ID and Secret are correct
- Ensure your Broadcaster ID is your numeric user ID, not username

### Web dashboard doesn't load
- Check that port 5000 is not already in use
- Try changing the port in `config.yaml` under `web.port`

### Build fails
- Make sure you have Python 3.10+ installed
- Run `pip install -r requirements.txt` manually
- Check that all dependencies installed successfully

---

## Support

For issues, feature requests, or questions:
- Open an issue on GitHub
- Check existing issues for solutions

---

## License

MIT License — use freely for personal or commercial purposes.
