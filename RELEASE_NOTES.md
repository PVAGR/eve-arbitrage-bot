# Release Notes - v2.0.0

## 🎉 EVE Personal Tracker & Arbitrage Bot v2.0.0

**Release Date**: February 26, 2026

This is a **major release** that transforms the project from a simple arbitrage scanner into a comprehensive, all-in-one EVE Online personal tracker and companion tool.

---

## 🌟 Highlights

### Complete Feature Set
- ✅ **Personal Character Tracking** with ESI OAuth
- ✅ **Wormhole Mapping & Chain Visualization**
- ✅ **Twitch Stream Integration**
- ✅ **Enhanced Market Arbitrage**
- ✅ **Unified Web Dashboard**

### Production-Ready
- ✅ **Security hardened** with rate limiting and input validation
- ✅ **Auto-backup system** (every 6 hours)
- ✅ **Health monitoring** with detailed status checks
- ✅ **Comprehensive logging** (console + file)
- ✅ **Error recovery** mechanisms

### User Experience
- ✅ **Setup Wizard** for easy configuration
- ✅ **Quick Start** script for instant launch
- ✅ **One-click executable** (no Python needed)
- ✅ **Modern dark UI** with responsive design

---

## 📦 What's Included

### Executables
- `EVEArbitrageBot.exe` - Main application (Windows)
- `config.yaml` - Configuration file
- `setup.bat` - Setup wizard shortcut
- `quick_start.bat` - One-click launcher

### Documentation
- `README.md` - Overview and quick start
- `SETUP_GUIDE.md` - Detailed setup instructions
- `CHANGELOG.md` - Complete change history
- This `RELEASE_NOTES.md` file

### Source Code
- Complete Python source in `src/`
- Build scripts for creating executables
- Setup wizard for guided configuration

---

## 🚀 Getting Started

### For First-Time Users

1. **Download the release package**
2. **Extract all files** to a folder
3. **Run `quick_start.bat`**
   - Automatically checks configuration
   - Runs setup wizard if needed
   - Starts the application
4. **Open your browser** to http://localhost:5000

### For Python Developers

```bash
git clone https://github.com/PVAGR/eve-arbitrage-bot.git
cd eve-arbitrage-bot
pip install -r requirements.txt
python run.py
```

---

## 🔑 Required Setup (First Time Only)

### For Character Tracking

1. Visit https://developers.eveonline.com/
2. Create a new application
3. Set callback URL: `http://localhost:8888/callback`
4. Copy your Client ID
5. Add to `config.yaml` under `character.esi_client_id`

**First launch will open your browser for EVE login** - this is normal and secure!

### For Twitch Integration (Optional)

1. Visit https://dev.twitch.tv/console/apps
2. Create an application
3. Get Client ID, Client Secret, and your User ID
4. Add to `config.yaml` under `twitch` section

### For Market Arbitrage (No Setup Required!)

Just adjust the fees in `config.yaml` to match your in-game skills:
- Broker Relations → `broker_fee_buy` & `broker_fee_sell`
- Accounting → `sales_tax`

---

## ✨ Key Features Explained

### Character Tracking
Shows you in real-time:
- Where you are (system, station, ship)
- Your wallet balance
- Recent transactions
- Active market orders
- All your assets

Updates automatically every 60 seconds (configurable).

### Wormhole Mapping
Track your wormhole chains:
- Add connections manually
- See full chain visualization
- Track mass/time status
- Auto-log jumps into J-space
- Bookmark favorite systems

Perfect for wormhole explorers and traders!

### Twitch Integration
Automate your stream:
- Updates title with your activity
- Shows live/offline status
- Create markers for big events
- Template: "EVE Online - {name} {activity} in {location}"

Never manually update your stream title again!

### Market Arbitrage
Find profitable trades:
- Scans all major trade hubs
- Calculates exact profit after fees
- Shows best opportunities
- Track your inventory
- Compare prices instantly

---

## 🛡️ Security Features

### Implemented Protections
- ✅ **OAuth 2.0 PKCE** for EVE authentication (industry standard)
- ✅ **Rate limiting** on all API endpoints
- ✅ **Input validation** and sanitization
- ✅ **SQL injection** protection
- ✅ **XSS prevention** in web interface
- ✅ **Secure token storage** (local only)

### What We Don't Store
- ❌ Your EVE password (never)
- ❌ Your Twitch password (never)
- ❌ Personal information beyond what you configure
- ❌ Data on any external servers (everything is local)

---

## 📊 System Requirements

### Minimum
- **OS**: Windows 10/11, Linux, macOS
- **RAM**: 512 MB
- **Disk**: 100 MB free space
- **Internet**: Required for ESI API access

### Recommended
- **OS**: Windows 11
- **RAM**: 1 GB
- **Disk**: 500 MB (for logs and backups)
- **Browser**: Chrome, Firefox, or Edge (for dashboard)

###Python (if running from source)
- **Version**: Python 3.10 or higher
- **Dependencies**: See `requirements.txt`

---

## 🐛 Known Issues

### Current Limitations
1. **Windows only** for .exe builds (Python works on all platforms)
2. **Single character** tracking (multi-char support in v2.1)
3. **English UI only** (localization in future release)
4. **Desktop browser required** (mobile UI coming in v2.1)

### Workarounds
1. **On Linux/Mac**: Use Python directly (`python run.py`)
2. **Multiple chars**: Run separate instances with different configs
3. **Mobile access**: Dashboard works but not optimized yet

---

## 📈 Performance

### What to Expect
- **Startup time**: 2-5 seconds
- **Memory usage**: 100-200 MB
- **CPU usage**: <5% idle, <20% during scans
- **Network**: ~1-5 MB per scan (cached)

### Optimization Tips
- Increase `cache_ttl_minutes` in config for less API calls
- Reduce `track_interval_seconds` if you don't need frequent updates
- Disable features you don't use
- Close inactive tabs in dashboard

---

## 🔄 Upgrading from v1.x

### Automatic Migration
1. Backup your old `config.yaml`
2. Download v2.0.0
3. Run `setup_wizard.py` or update config manually
4. Your old arbitrage data will be preserved
5. New features require new config sections

### What's Preserved
- ✅ All market scan results
- ✅ Inventory data
- ✅ Database cache

### What's New (Needs Setup)
- ⚙️ Character tracking (needs ESI Client ID)
- ⚙️ Wormhole tracking (auto-enabled)
- ⚙️ Twitch integration (optional, needs API keys)

---

## 💬 Support & Community

### Get Help
- **GitHub Issues**: Report bugs or request features
- **Documentation**: See SETUP_GUIDE.md for detailed help
- **Logs**: Check `data/logs/` for error details

### Contributing
- **Pull Requests**: Always welcome!
- **Feature Requests**: Open an issue with your idea
- **Bug Reports**: Include log files and steps to reproduce

---

## 🎯 What's Next?

### v2.1.0 (Coming Soon)
- Discord integration
- Mobile-optimized UI
- CSV/Excel export
- Advanced analytics

### v2.2.0 (Planned)
- Multi-character support
- Corporation features
- Fleet tracking
- Contract tracking

### v3.0.0 (Future)
- Public API
- Plugin system
- ML price predictions
- Advanced automation

---

## ⭐ Show Your Support

If you find this tool useful:
- ⭐ **Star the repository** on GitHub
- 📢 **Share with your corp** or alliance
- 💬 **Provide feedback** via issues
- 🤝 **Contribute code** or documentation

---

## 📜 License

MIT License - Free for personal and commercial use.

---

## ⚠️ Disclaimer

This tool uses CCP Games' EVE Online ESI API but is not endorsed by or affiliated with CCP Games. Use at your own risk. Always follow CCP's Terms of Service and EULA.

---

**Enjoy your new EVE companion! Fly safe! o7**

*- PVAGR*
