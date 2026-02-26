# EVE Personal Tracker & Arbitrage Bot

[![Build](https://github.com/PVAGR/eve-arbitrage-bot/actions/workflows/build.yml/badge.svg)](https://github.com/PVAGR/eve-arbitrage-bot/actions/workflows/build.yml)

**Your all-in-one EVE Online companion** — Track your character in real-time, map wormhole chains, integrate with Twitch streaming, and find profitable arbitrage opportunities across trade hubs.

---

## 🚀 Features

### 🧑‍🚀 Personal Character Tracking
- **Live location tracking** — Current system, station, and ship
- **Wallet monitoring** — Balance and transaction history
- **Market orders** — Track all your active buy/sell orders
- **Asset overview** — All your items across all stations
- **Skills & training** — Current SP and skill queue

### 🌌 Wormhole Tools
- **Connection mapping** — Track all active wormhole connections
- **Chain visualization** — See full connection chains up to 5 jumps deep
- **Auto jump logging** — Automatically log wormhole jumps
- **Mass & time tracking** — Monitor connection stability
- **Favorite systems** — Bookmark your home holes

### 🎥 Twitch Integration
- **Auto stream title updates** — Updates based on your activity
- **Live status monitoring** — See if you're streaming in the dashboard
- **Stream markers** — Create markers for important events
- **Chat integration ready** — Built for future chat bot features

### 📈 Market Arbitrage
- **Multi-region scanning** — Jita, Amarr, Dodixie, Rens, Hek
- **Full fee calculations** — Broker fees, sales tax, hauling costs
- **Smart filtering** — Customizable profit thresholds
- **Inventory tracking** — Track profit/loss on your trades
- **Price comparison** — Real-time prices across all hubs

---

## 📥 Download & Play (No Python Required)

**Every push to main automatically builds a Windows exe.**

### Steps:
1. Go to **[Releases](https://github.com/PVAGR/eve-arbitrage-bot/releases/tag/latest)**
2. Download **`EVEArbitrageBot.exe`** and **`config.yaml`**
3. Edit `config.yaml` (see [Setup Guide](SETUP_GUIDE.md))
4. Double-click **`EVEArbitrageBot.exe`**
5. Open browser to **http://localhost:5000**

> 📖 **Full setup instructions**: See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed configuration

---

## ⚙️ Quick Configuration

### Minimum Setup (Arbitrage Only)
Edit `config.yaml` with your in-game skill levels:

```yaml
fees:
  broker_fee_buy: 0.03       # Your Broker Relations skill
  broker_fee_sell: 0.03
  sales_tax: 0.08            # Your Accounting skill
```

### Full Setup (Character + Twitch + Wormholes)

1. **Get EVE ESI Client ID**:
   - Visit: https://developers.eveonline.com/
   - Create app with callback: `http://localhost:8888/callback`
   - Add to `config.yaml`

2. **Get Twitch Credentials** (optional):
   - Visit: https://dev.twitch.tv/console/apps
   - Add to `config.yaml`

3. **Run the program** — First run will prompt for EVE login

📖 **Detailed setup**: [SETUP_GUIDE.md](SETUP_GUIDE.md)

---

## 🖥️ Dashboard

Once running, open: **http://localhost:5000**

### Tabs:

- **Character** — Real-time status, location, wallet, transactions
- **Wormholes** — Active connections, jump history, chain mapping
- **Arbitrage** — Market opportunities sorted by profit
- **Inventory** — Your stock with live profit/loss calculations
- **Price Lookup** — Compare prices across all hubs instantly

---

## 🎯 What It Does

All data is fetched from public [EVE ESI API](https://esi.evetech.net/). For personal character data, you authenticate once with EVE SSO (OAuth 2.0).

### No Login Required:
- Market data from all trade hubs
- Item information and prices
- Basic arbitrage calculations

### With Authentication:
- Your character's location and ship
- Wallet balance and transactions
- Active market orders
- Assets across all stations
- Jump history through wormholes
- Twitch stream integration

---

## 💻 CLI Mode

For automation and scripting:

```bash
# Run market scan
python run.py scan

# Scan specific region pair
python run.py scan --regions Jita Amarr

# Show top opportunities
python run.py top 20

# Price lookup
python run.py lookup "Tritanium"

# Manage inventory
python run.py inventory list
python run.py inventory add "Tritanium" 10000 5.50

# Start web dashboard
python run.py web
python run.py web --port 8080
```

---

## 🔧 Building from Source

If you have Python 3.10+ and want to build/modify:

```bash
git clone https://github.com/PVAGR/eve-arbitrage-bot.git
cd eve-arbitrage-bot
pip install -r requirements.txt

# Run directly
python run.py

# Build your own exe
build.bat
```

---

## 📊 How It Works

### Market Arbitrage
1. Fetches all market orders from configured regions
2. Finds items sold in one region and bought in another
3. Calculates net profit after:
   - Broker fees (buying and selling)
   - Sales tax
   - Hauling cost (per m³)
4. Filters by your minimum profit thresholds
5. Caches data in SQLite to avoid API spam

### Character Tracking
1. Authenticates with EVE SSO (OAuth 2.0 PKCE)
2. Polls ESI authenticated endpoints every 60 seconds
3. Tracks location changes, wallet transactions, market orders
4. Automatically logs wormhole jumps
5. Updates Twitch stream title based on activity

### Wormhole Mapping
1. Manually add connections via web interface
2. Tracks mass and time status
3. Builds connection chains recursively
4. Auto-logs jumps when entering J-space
5. Stores in separate SQLite database

---

## 🗂️ Data Storage

The program creates a `data/` folder:

```
data/
├── eve_arbitrage.db      # Market cache and scan results
├── wormholes.db          # Wormhole connections and jumps
├── token.json            # Your ESI authentication token
└── twitch_config.json    # Twitch API credentials (if enabled)
```

All data is stored locally — nothing is sent to any third-party servers.

---

## 🔐 Security & Privacy

- **No passwords stored** — Uses OAuth tokens only
- **Token encryption** — Stored securely in local files
- **ESI scopes** — Requests only what's needed for features you enable
- **Open source** — All code is visible and auditable
- **Local only** — Runs entirely on your machine

---

## 🎮 Perfect For

- **Wormhole dwellers** — Track connections and chains
- **Day traders** — Find arbitrage opportunities
- **Streamers** — Auto-update Twitch with your activity  
- **Corp logistics** — Monitor market orders and inventory
- **Station traders** — Track profit/loss across items
- **Exploration** — Log jump history and discoveries

---

## 🤝 Contributing

Pull requests welcome! Areas for contribution:

- Additional ESI endpoints (contracts, industry, etc.)
- Discord integration
- Advanced wormhole features
- Better mobile UI
- Market prediction/analytics
- Chat bot commands for Twitch

---

## 📜 License

MIT License — Free for personal and commercial use.

---

## ⚠️ Disclaimer

This tool uses CCP Games' EVE Online ESI API but is not endorsed by or affiliated with CCP Games.
