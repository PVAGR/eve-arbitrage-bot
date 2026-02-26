# Changelog

All notable changes to EVE Personal Tracker & Arbitrage Bot will be documented in this file.

## [2.0.0] - 2026-02-26

### 🎉 Major Release - Complete Rewrite

Complete transformation from simple arbitrage bot to comprehensive EVE Online tracking platform.

### ✨ New Features

#### Character Tracking
- **ESI OAuth Authentication** - Secure login with EVE SSO
- **Real-time Location Tracking** - Current system, station, and ship
- **Wallet Monitoring** - Balance and transaction history
- **Market Orders** - Track all active buy/sell orders
- **Asset Overview** - All items across all stations
- **Skills Display** - Total SP and skill information

#### Wormhole Tools
- **Connection Mapping** - Track all wormhole connections
- **Chain Visualization** - Recursive chain building up to 5 jumps
- **Auto Jump Logging** - Automatic logging when entering J-space
- **Mass & Time Tracking** - Monitor connection stability
- **Favorite Systems** - Bookmark your home systems
- **Jump History** - Complete history with timestamps

#### Twitch Integration
- **Auto Stream Title Updates** - Update based on current activity
- **Live Status Monitoring** - Stream status in dashboard
- **Stream Markers** - Create markers for important events
- **Configurable Templates** - Customize title format
- **OAuth Token Management** - Secure credential storage

#### Enhanced Web Dashboard
- **Tabbed Interface** - Character, Wormholes, Arbitrage, Inventory, Lookup
- **Real-time Updates** - Auto-refresh with configurable interval
- **Status Badges** - Character online status and stream status
- **Interactive Management** - Add/update/remove connections and data
- **Modern Dark Theme** - Space-themed UI with improved UX

### 🔒 Security Enhancements
- Input validation and sanitization
- Rate limiting on API endpoints
- Secure token storage with hashing
- Configuration validation on startup
- SQL injection protection
- XSS prevention in web interface

### 📊 Monitoring & Quality of Life
- **Health Check System** - Monitor system resources and component health
- **Comprehensive Logging** - Colored console output and detailed file logs
- **Auto-Backup System** - Automatic backups of databases and config (every 6 hours)
- **Error Handling** - Improved error messages and recovery
- **Setup Wizard** - Interactive configuration tool
- **Quick Start Script** - One-click startup with auto-setup

### 🛠️ Infrastructure Improvements
- Modular architecture with clear separation of concerns
- Type hints throughout codebase
- Dataclasses for structured data
- Thread-safe operations
- Connection pooling
- Database migrations support

### 📚 Documentation
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Comprehensive setup instructions
- **[README.md](README.md)** - Complete feature overview
- Inline code documentation
- API endpoint documentation
- Configuration examples

### 🔧 Developer Experience
- **setup_wizard.py** - Interactive configuration wizard
- **quick_start.bat** - Streamlined startup process
- Better error messages
- Development mode support
- Hot reload for web server

### 🐛 Bug Fixes
- Fixed database locking issues
- Improved ESI error handling
- Fixed memory leaks in long-running processes
- Corrected timezone handling
- Fixed cache invalidation edge cases

### 📦 Dependencies
- Added `psutil` for system monitoring
- Updated Flask to 3.0+
- All dependencies pinned to stable versions

### 🔄 Breaking Changes
- Configuration file structure changed (see [config.yaml](config.yaml))
- Database schema updated (auto-migrates on first run)
- New authentication flow for ESI (requires client ID)
- Web dashboard port default changed to 5000

---

## [1.0.0] - Previous Version

### Features
- Basic market arbitrage scanning
- Multi-region price comparison
- Web dashboard
- CLI interface
- SQLite caching

---

## Migration Guide from 1.x to 2.0

### Configuration
1. Backup your old `config.yaml`
2. Run `setup_wizard.py` to generate new config
3. Or manually update config.yaml structure:
   - Add `character:` section with `esi_client_id`
   - Add `twitch:` section (optional)
   - Add `wormholes:` section (optional)

### Database
- No manual migration needed - automatic on first run
- Old arbitrage data will be preserved
- New tables will be created automatically

### Authentication
- Get ESI Client ID from https://developers.eveonline.com/
- Set callback URL to `http://localhost:8888/callback`
- Run application - will prompt for EVE login on first character access

### Features
- All old features still work
- Character tracking requires ESI authentication
- Twitch integration optional
- Wormhole tracking optional

---

## Roadmap

### v2.1.0 (Planned)
- [ ] Discord integration
- [ ] Mobile-optimized UI
- [ ] Export to CSV/Excel
- [ ] Advanced analytics dashboard
- [ ] Contract tracking
- [ ] Industry job tracking

### v2.2.0 (Planned)
- [ ] Multi-character support
- [ ] Corporation wallet access
- [ ] Fleet tracking
- [ ] Kill/loss mail integration
- [ ] Structure management
- [ ] Planetary interaction tracking

### v3.0.0 (Future)
- [ ] Web API for third-party integration
- [ ] Plugin system
- [ ] Machine learning price predictions
- [ ] Advanced route planning
- [ ] Hauling optimization
- [ ] Market manipulation detection
