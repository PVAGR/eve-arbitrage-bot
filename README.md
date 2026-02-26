# EVE Arbitrage Bot

A market arbitrage scanner for EVE Online. Finds items you can buy cheaply at one trade hub and sell at a profit at another, accounting for broker fees, sales tax, and hauling costs.

All market data is fetched from the public [EVE ESI API](https://esi.evetech.net/) — no login or character authentication required.

---

## Features

- Scans all major trade hubs (Jita, Amarr, Dodixie, Rens, Hek) for cross-region arbitrage
- Full fee model: broker fees, sales tax, and per-m³ hauling costs
- SQLite caching — avoids hammering ESI on repeated scans
- Web dashboard with live opportunity table, inventory tracker, and price lookup
- CLI for scripting and headless use

---

## Requirements

- Python 3.10+
- pip

## Installation

```bash
git clone https://github.com/PVAGR/eve-arbitrage-bot.git
cd eve-arbitrage-bot
pip install -r requirements.txt
```

---

## Configuration

Edit `config.yaml` before running. Key settings:

```yaml
fees:
  broker_fee_buy: 0.03      # Match your Broker Relations skill level
  broker_fee_sell: 0.03
  sales_tax: 0.08           # Match your Accounting skill level
  hauling_isk_per_m3: 800   # Set 0 to ignore hauling cost

filters:
  min_profit_margin_pct: 10   # Only show opps with >= 10% margin
  min_net_isk_profit: 1000000 # Only show opps with >= 1M ISK profit/unit
  max_investment_per_item: 0  # 0 = no cap
  min_volume_available: 1

scan:
  cache_ttl_minutes: 5   # How long to cache ESI market pages
  pairs:                 # Region pairs to compare (both directions scanned)
    - [Jita, Amarr]
    - [Jita, Dodixie]
    ...
```

---

## CLI Usage

```bash
# Run a full scan across all configured region pairs
python run.py scan

# Scan one specific route only
python run.py scan --regions Jita Amarr

# Show top 20 opportunities from the last scan
python run.py top 20

# Price check an item across all hubs
python run.py lookup "Tritanium"

# Inventory management
python run.py inventory list
python run.py inventory add "Tritanium" 100000 5.50
python run.py inventory add "Tritanium" 100000 5.50 --station "Jita IV - Moon 4"
python run.py inventory update ID NEW_QTY
python run.py inventory remove ID

# Start the web dashboard
python run.py web
python run.py web --port 8080
python run.py web --host 0.0.0.0 --port 8080
```

---

## Web Dashboard

```bash
python run.py web
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

**Opportunities tab** — sortable/filterable table of all arbitrage results from the last scan. Click "Run Scan" to trigger a fresh scan in the background.

**Inventory tab** — track items you own with cost basis. Shows current Jita sell price and unrealized P&L.

**Price Lookup tab** — search any item to see current best prices across all hubs.

---

## Project Structure

```
run.py                  # Entry point
config.yaml             # All user-configurable settings
requirements.txt

src/
  config.py             # YAML config loader
  api/
    esi.py              # ESI API client with caching + rate limiting
  engine/
    fees.py             # Profit/margin calculations
    arbitrage.py        # Core opportunity-finding algorithm
    scanner.py          # Orchestrates full scans, saves results
  models/
    database.py         # SQLite layer (cache, results, inventory)
  cli/
    main.py             # Click CLI commands
  web/
    app.py              # Flask REST API
    templates/          # Dashboard HTML
    static/             # JS + CSS
data/
  eve_arbitrage.db      # SQLite database (created on first run)
```

---

## Notes

- Market data is cached in SQLite to reduce ESI calls. Set `cache_ttl_minutes` lower for fresher data (at the cost of more API requests).
- Opportunities are based on **buying at the cheapest sell order** in the source region and **hitting the highest buy order** in the destination. This is the conservative, instantly executable trade.
- The bot does not place orders. All actions are read-only against ESI.
