# EVE Arbitrage Bot v2.0.0 - Quick Start Guide

## First Time Setup (5 Minutes)

### Step 1: Download & Extract
1. Download the latest release from GitHub
2. Extract all files to a folder (e.g., `C:\EVE\ArbitrageBot\`)
3. You should see: `EVEArbitrageBot.exe`, `config.yaml`, `quick_start.bat`, etc.

### Step 2: Quick Configuration
**Option A: Use the Setup Wizard (Recommended)**
- Double-click `setup.bat`
- Follow the prompts to configure your settings
- The wizard will create a valid `config.yaml` for you

**Option B: Manual Configuration**
- Open `config.yaml` in a text editor
- Adjust the fees based on your skills (see below)
- Save the file

### Step 3: Launch!
- Double-click `quick_start.bat`
- Or double-click `EVEArbitrageBot.exe`
- Or run `EVEArbitrageBot.exe web` for direct dashboard access

The web dashboard will open at: **http://localhost:5000**

---

## Essential Configuration

### Market Arbitrage Fees (Required)
Edit these in `config.yaml` under the `fees:` section:

```yaml
fees:
  broker_fee_buy: 0.03     # 3% = Level 0 Broker Relations
  broker_fee_sell: 0.03    # Skills reduce this: 0.5% per level
  sales_tax: 0.02          # 2% = Level 0 Accounting (0.2% per level)
```

**How to calculate your fees:**
- **Broker Relations**: Level 5 = 0.5% per level = 2.5% reduction = 0.5% fee
- **Accounting**: Level 5 = 0.2% per level = 1.0% reduction = 1.0% tax

Example with max skills:
```yaml
fees:
  broker_fee_buy: 0.005    # 0.5%
  broker_fee_sell: 0.005   # 0.5%
  sales_tax: 0.010         # 1.0%
```

### ESI Character Tracking (Optional)
To enable character tracking:

1. **Create an ESI Application:**
   - Go to https://developers.eveonline.com/
   - Click "Create New Application"
   - Name: "My Personal Tracker"
   - Description: "Personal character tracking"
   - Callback URL: `http://localhost:8888/callback`
   - Scopes: Select ALL character scopes (read permissions)
   - Save and copy your **Client ID**

2. **Add to config.yaml:**
```yaml
character:
  enabled: true
  esi_client_id: "your_client_id_here"
  track_interval_seconds: 60
```

3. **First Launch:**
   - Your browser will open asking for EVE login
   - This is normal and secure (OAuth 2.0)
   - Click "Authorize" to grant access
   - Your character data will start tracking

### Twitch Integration (Optional)
To enable Twitch integration:

1. **Create a Twitch App:**
   - Go to https://dev.twitch.tv/console/apps
   - Click "Register Your Application"
   - Name: "EVE Stream Bot"
   - OAuth Redirect URL: `http://localhost:8888/callback`
   - Category: "Application Integration"
   - Save and get your **Client ID** and **Client Secret**

2. **Get Your User ID:**
   - Go to https://www.streamweasels.com/tools/convert-twitch-username-to-user-id/
   - Enter your Twitch username
   - Copy the numeric User ID

3. **Add to config.yaml:**
```yaml
twitch:
  enabled: true
  client_id: "your_client_id"
  client_secret: "your_client_secret"
  broadcaster_id: "your_user_id"
  auto_update: true
  title_template: "EVE Online - {name} {activity} in {location}"
```

---

## Using the Dashboard

### Navigation Tabs
- **Opportunities**: Market arbitrage scanner (always available)
- **Inventory**: Track your items and profit/loss
- **Character**: Your real-time character data (if configured)
- **Wormholes**: Wormhole chain mapping (if enabled)
- **Twitch**: Stream status and controls (if configured)

### Market Scanning
1. Click "Run New Scan" button
2. Wait 30-60 seconds
3. View top opportunities sorted by profit
4. Click any item to see full details

### Inventory Management
1. Go to "Inventory" tab
2. Click "Add Item" button
3. Enter: Item name, quantity, cost per unit, location
4. Save to track profit/loss
5. Update quantities as you trade

### Character Tracking
Shows in real-time:
- Where you are (system, station, ship)
- Wallet balance
- Recent transactions
- Active market orders
- All your assets

### Wormhole Mapping
1. Go to "Wormholes" tab
2. Click "Add Connection"
3. Enter: Source system, Destination system, WH type
4. Track mass/time status
5. View full chain visualization

### Twitch Controls
- See live/offline status
- Update stream title automatically
- Create markers for big events
- Title updates based on your in-game activity

---

## Common Issues & Solutions

### "Character tracking not configured"
**Solution**: You need to set up ESI OAuth (see section above)

### "Twitch showing offline when I'm live"
**Solutions**:
1. Verify your `broadcaster_id` is correct (not your username!)
2. Check your Client ID and Secret are valid
3. Make sure your stream is actually live
4. Click "Refresh Status" button

### "No opportunities found"
**Solutions**:
1. Check your internet connection
2. Run a scan (it can take 30-60 seconds)
3. Adjust filters in `config.yaml` (lower `min_profit`)
4. Make sure regions are configured correctly

### "Database errors"
**Solutions**:
1. Delete `data/eve_arbitrage.db` and restart (rebuilds database)
2. Check you have write permissions in the folder
3. Make sure no other instance is running

### "Web dashboard won't load"
**Solutions**:
1. Make sure port 5000 isn't in use by another program
2. Try changing the port: `EVEArbitrageBot.exe web --port 8080`
3. Check firewall isn't blocking the application
4. Try accessing: http://127.0.0.1:5000

---

## Advanced Features

### Health Monitoring
- View system health: `EVEArbitrageBot.exe health`
- Or visit: http://localhost:5000/health

Shows:
- CPU, memory, disk usage
- Component status (Database, ESI API, etc.)
- Any errors or warnings

### Manual Backups
- Create backup: `EVEArbitrageBot.exe backup`
- Auto-backups run every 6 hours
- Backups stored in: `data/backups/`

### Command Line Usage
```bash
# Interactive menu
EVEArbitrageBot.exe

# Commands
EVEArbitrageBot.exe scan                    # Run market scan
EVEArbitrageBot.exe top 20                  # Show top 20 opportunities
EVEArbitrageBot.exe lookup "Tritanium"      # Price check
EVEArbitrageBot.exe inventory list          # Show inventory
EVEArbitrageBot.exe web                     # Start web dashboard
EVEArbitrageBot.exe health                  # System health check
EVEArbitrageBot.exe backup                  # Create backup
EVEArbitrageBot.exe version                 # Show version info
```

### Data Files Location
All data is stored in the `data/` folder:
- `eve_arbitrage.db` - Market data and inventory
- `wormholes.db` - Wormhole connections and jumps
- `logs/` - Application logs
- `backups/` - Automatic backups (kept for 30 days)

---

## Tips & Tricks

### Maximizing Profit
1. **Update your skill fees** - Max trade skills = 10x more profit!
2. **Use Station Trading** - Set filters to same region for quick flips
3. **Track your inventory** - Don't lose track of profit/loss
4. **Scan regularly** - Market changes fast, scan every hour

### Character Tracking
1. **Set low refresh interval** (30-60 seconds) for real-time data
2. **Use with Twitch** - Auto-update title with your location
3. **Track transactions** - See exactly what you bought/sold
4. **Monitor orders** - Never miss an expired order

### Wormhole Exploration
1. **Add favorites** - Bookmark your home systems
2. **Track jumps** - See where you've been
3. **Chain visualization** - Never get lost in J-space
4. **Mass/time tracking** - Know when holes will collapse

### Twitch Streaming
1. **Enable auto-update** - Title updates with your activity
2. **Create markers** - Mark big loot drops or kills
3. **Status badge** - Always know if you're live
4. **Template customization** - Personalize your stream title

---

## Performance Tuning

### For Slower Computers
In `config.yaml`:
```yaml
cache_ttl_minutes: 30              # Cache data longer
web:
  auto_refresh_seconds: 120        # Refresh dashboard less often
character:
  track_interval_seconds: 120      # Update character data less often
```

### For Faster Scans
```yaml
cache_ttl_minutes: 5               # Fresher data
filters:
  min_profit: 100000               # Only show big opportunities
  min_roi_percent: 5.0             # Higher ROI threshold
```

### To Reduce Memory Usage
- Close unused tabs in dashboard
- Reduce scan history: Delete old data in database
- Disable features you don't use

---

## Getting Help

### Check Logs
Logs are in: `data/logs/eve-tracker.log`

Look for:
- ERROR messages (red) - Something failed
- WARNING messages (yellow) - Something might be wrong
- INFO messages (white) - Normal operations

### Common Log Messages
- `"Token expired"` → Re-authenticate (ESI or Twitch)
- `"Rate limited"` → Slow down API requests
- `"Connection timeout"` → Check internet
- `"Database locked"` → Close other instances

### Report Issues
If you find a bug:
1. Check `data/logs/` for error details
2. Try the fix suggestions in this guide
3. Open an issue on GitHub with:
   - What you were doing
   - Error message from logs
   - Your config.yaml (remove sensitive data!)

---

## Next Steps

### After Basic Setup
1. ✅ Run your first market scan
2. ✅ Set up ESI character tracking
3. ✅ Configure your trade skill fees
4. ✅ Enable auto-backup (already on by default!)

### Advanced Usage
1. ⚡ Enable Twitch integration for streaming
2. ⚡ Set up wormhole tracking for exploration
3. ⚡ Use CLI commands for automation
4. ⚡ Integrate with your corp/alliance workflow

---

## Safety & Security

### Your Data
- ✅ Everything stored **locally** (no cloud)
- ✅ No passwords stored (OAuth tokens only)
- ✅ Tokens encrypted and hashed
- ✅ Auto-backup protects against data loss

### ESI OAuth
- ✅ Industry-standard OAuth 2.0 PKCE
- ✅ Your EVE password is **never** shared
- ✅ You can revoke access anytime at https://community.eveonline.com/support/third-party-applications/
- ✅ Only requests "read" permissions (can't modify your character)

### Twitch OAuth
- ✅ Standard OAuth app token flow
- ✅ Your Twitch password is **never** shared
- ✅ Only requests permissions for title/markers
- ✅ Can revoke at: https://www.twitch.tv/settings/connections

---

**Enjoy! Fly safe! o7**

*Need more help? Check the full [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions.*
