# EVE Arbitrage Bot

[![Build](https://github.com/PVAGR/eve-arbitrage-bot/actions/workflows/build.yml/badge.svg)](https://github.com/PVAGR/eve-arbitrage-bot/actions/workflows/build.yml)

A market arbitrage scanner for EVE Online. Finds items you can buy cheaply at one trade hub and sell at a profit at another, accounting for broker fees, sales tax, and hauling costs.

---

## Download & Play (No Python required)

**Every push to main automatically builds a Windows exe.**

### Steps:
1. Go to **[Releases](https://github.com/PVAGR/eve-arbitrage-bot/releases/tag/latest)**
2. Download **`EVEArbitrageBot.exe`** and **`config.yaml`**
3. Put them in the **same folder**
4. Double-click **`EVEArbitrageBot.exe`**

That's it. The interactive menu opens in your terminal window.

> The bot creates a `data/` folder next to the exe to store its database. No other setup needed.

---

## What It Does

All market data is fetched from the public [EVE ESI API](https://esi.evetech.net/) — no login or character authentication required.

- Scans all major trade hubs (Jita, Amarr, Dodixie, Rens, Hek) for cross-region arbitrage
- Full fee model: broker fees, sales tax, and per-m³ hauling costs
- SQLite caching — avoids hammering ESI on repeated scans
- Web dashboard with live opportunity table, inventory tracker, and price lookup
- Interactive TUI menu — just run the exe and navigate with number keys
- CLI for scripting and headless use

---

## Interactive Menu

When you launch the exe (or run `python run.py` with no arguments), you get a full menu:

```
◆  EVE  ARBITRAGE  BOT  ◆

  1   Run Market Scan
  2   View Opportunities
  3   Manage Inventory
  4   Price Lookup
  5   Web Dashboard

  Q   Quit
```

Navigate with number keys. No command-line flags needed.

---

## Configuration

Edit `config.yaml` to match your in-game skills and set profit thresholds:

```yaml
fees:
  broker_fee_buy: 0.03      # Match your Broker Relations skill level
  broker_fee_sell: 0.03
  sales_tax: 0.08           # Match your Accounting skill level
  hauling_isk_per_m3: 800   # Set 0 to ignore hauling cost

filters:
  min_profit_margin_pct: 10   # Only show opps with >= 10% margin
  min_net_isk_profit: 1000000 # Only show opps with >= 1M ISK profit/unit
  max_investment_per_item: 0  # 0 = no cap on total trade size
  min_volume_available: 1

scan:
  cache_ttl_minutes: 5        # How long to cache ESI market data
  pairs:                      # Region pairs to compare (both directions scanned)
    - [Jita, Amarr]
    - [Jita, Dodixie]
    ...
```

---

## Build from Source (optional)

If you have Python 3.10+ installed and want to build the exe yourself:

```bash
git clone https://github.com/PVAGR/eve-arbitrage-bot.git
cd eve-arbitrage-bot
pip install -r requirements.txt

# Run directly (no build needed)
python run.py

# Or build your own exe
build.bat
```

---

## CLI Usage (for scripting)

```bash
python run.py scan                          # Full market scan
python run.py scan --regions Jita Amarr     # Scan one route
python run.py top 20                        # Show top 20 opportunities
python run.py lookup "Tritanium"            # Price check across all hubs
python run.py inventory list
python run.py inventory add "Tritanium" 100000 5.50
python run.py inventory update ID NEW_QTY
python run.py inventory remove ID
python run.py web                           # Start web dashboard
python run.py web --port 8080
```

---

## Web Dashboard

From the menu select **5**, or run `python run.py web`, then open [http://127.0.0.1:5000](http://127.0.0.1:5000).

**Opportunities** — sortable/filterable table of arbitrage results. Click "Run Scan" to refresh.

**Inventory** — track items with cost basis. Shows Jita market price and unrealized P&L.

**Price Lookup** — search any item name to see prices across all trade hubs.

---

## Notes

- Opportunities are based on **buying at the cheapest sell order** in the source region and **hitting the highest buy order** in the destination — the conservative, instantly executable trade.
- Market data is cached to reduce API calls. Lower `cache_ttl_minutes` for fresher data.
- The bot does not place orders. All ESI calls are read-only.
