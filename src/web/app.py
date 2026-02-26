"""
Flask web server for the EVE Arbitrage Bot dashboard.

Endpoints:
  GET  /                          Dashboard HTML
  GET  /api/opportunities         Latest arbitrage results (JSON)
  GET  /api/inventory             Current inventory (JSON)
  POST /api/inventory             Add inventory item
  DELETE /api/inventory/<id>      Remove inventory item
  GET  /api/scan/status           Last scan time + result count
  POST /api/scan/run              Trigger a background scan
  GET  /api/prices/<query>        Search item prices across all hubs
  
  Character Tracking:
  GET  /api/character/status      Full character status
  GET  /api/character/location    Current location
  GET  /api/character/wallet      Wallet balance
  GET  /api/character/transactions Recent transactions
  GET  /api/character/orders      Active market orders
  
  Wormhole Tracking:
  GET  /api/wormholes/connections Active connections
  POST /api/wormholes/connection  Add new connection
  PATCH /api/wormholes/connection/<id> Update connection
  DELETE /api/wormholes/connection/<id> Expire connection
  GET  /api/wormholes/chain/<system_id> Get connection chain
  GET  /api/wormholes/history     Jump history
  POST /api/wormholes/jump        Record jump
  GET  /api/wormholes/favorites   Favorite systems
  
  Twitch Integration:
  GET  /api/twitch/status         Stream status
  POST /api/twitch/title          Update stream title
  POST /api/twitch/marker         Create stream marker
"""
from __future__ import annotations

import os
import sys
import threading
from flask import Flask, jsonify, render_template, request, abort

from config import load_config, get_region_map
from models import database as db
from engine import scanner
from api import esi
from version import __version__, get_full_version_info
from utils.health import get_system_health, format_uptime
from utils.backup import get_backup_manager
from utils.logging import setup_logging
from utils.security import rate_limit, require_feature

# When frozen by PyInstaller, templates and static files live in sys._MEIPASS.
# In dev, Flask resolves them relative to this file automatically.
if getattr(sys, "frozen", False):
    _web_root = sys._MEIPASS
    app = Flask(
        __name__,
        template_folder=os.path.join(_web_root, "templates"),
        static_folder=os.path.join(_web_root, "static"),
    )
else:
    app = Flask(__name__)

# Setup logging
logger = setup_logging("eve-tracker.web")
logger.info(f"Initializing EVE Tracker v{__version__}")

db.init_db()

# Start auto-backup
backup_manager = get_backup_manager()
backup_manager.start_auto_backup(interval_hours=6)
logger.info("Auto-backup system started (6 hour interval)")

_scan_lock = threading.Lock()
_scan_running = False

# Global instances for character tracking, wormholes, and Twitch
_character_tracker = None
_wormhole_tracker = None
_twitch_integration = None


def _init_integrations():
    """Initialize character tracking, wormholes, and Twitch if configured."""
    global _character_tracker, _wormhole_tracker, _twitch_integration
    
    cfg = load_config()
    
    # Character tracker
    if cfg.get("character", {}).get("esi_client_id"):
        try:
            from tracker.character import CharacterTracker
            _character_tracker = CharacterTracker(cfg["character"]["esi_client_id"])
        except Exception as e:
            print(f"Failed to initialize character tracker: {e}")
    
    # Wormhole tracker
    if cfg.get("wormholes", {}).get("enabled", True):
        try:
            from tracker.wormholes import WormholeTracker
            _wormhole_tracker = WormholeTracker()
        except Exception as e:
            print(f"Failed to initialize wormhole tracker: {e}")
    
    # Twitch integration
    if cfg.get("twitch", {}).get("enabled", False):
        try:
            from integrations.twitch import TwitchIntegration, TwitchConfig
            twitch_cfg = cfg["twitch"]
            _twitch_integration = TwitchIntegration(TwitchConfig(
                client_id=twitch_cfg["client_id"],
                client_secret=twitch_cfg["client_secret"],
                broadcaster_id=twitch_cfg["broadcaster_id"],
            ))
        except Exception as e:
            print(f"Failed to initialize Twitch integration: {e}")


# ── Global error handlers ─────────────────────────────────────────────────

@app.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request errors."""
    logger.warning(f"Bad request: {error}")
    return jsonify({
        "error": "Bad Request",
        "message": str(error.description) if hasattr(error, 'description') else str(error)
    }), 400


@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors."""
    return jsonify({
        "error": "Not Found",
        "message": str(error.description) if hasattr(error, 'description') else "Resource not found"
    }), 404


@app.errorhandler(409)
def conflict(error):
    """Handle 409 Conflict errors."""
    return jsonify({
        "error": "Conflict",
        "message": str(error.description) if hasattr(error, 'description') else "Request conflicts with current state"
    }), 409


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server Error."""
    logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred. Please check logs for details."
    }), 500


@app.errorhandler(503)
def service_unavailable(error):
    """Handle 503 Service Unavailable."""
    return jsonify({
        "error": "Service Unavailable",
        "message": str(error.description) if hasattr(error, 'description') else "Service temporarily unavailable"
    }), 503


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    """Catch-all handler for unexpected exceptions."""
    logger.error(f"Unexpected error: {error}", exc_info=True)
    return jsonify({
        "error": "Unexpected Error",
        "message": "An unexpected error occurred. Please check logs for details.",
        "type": type(error).__name__
    }), 500


# ── System endpoints ──────────────────────────────────────────────────────

@app.route("/health")
def health_check():
    """Health check endpoint for monitoring."""
    health = get_system_health()
    status_code = 200 if health.status == "healthy" else 503
    
    return jsonify({
        "status": health.status,
        "version": __version__,
        "uptime": format_uptime(health.uptime_seconds),
        "uptime_seconds": health.uptime_seconds,
        "system": {
            "cpu_percent": health.cpu_percent,
            "memory_percent": health.memory_percent,
            "memory_mb": health.memory_mb,
            "disk_percent": health.disk_percent,
        },
        "components": {
            "database": health.database_ok,
            "esi_api": health.esi_api_ok,
            "character_tracking": health.character_tracking_ok,
            "wormhole_tracking": health.wormhole_tracking_ok,
            "twitch_integration": health.twitch_integration_ok,
        },
        "errors": health.errors,
    }), status_code


@app.route("/version")
def version_info():
    """Get version and build information."""
    return jsonify(get_full_version_info())


@app.route("/api/backups")
def api_backups():
    """List all available backups."""
    try:
        backups = backup_manager.list_backups()
        return jsonify({"backups": backups})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/backup/create", methods=["POST"])
@rate_limit(max_calls=5, period_seconds=300)  # Max 5 manual backups per 5 min
def api_create_backup():
    """Manually trigger a backup."""
    try:
        backup_manager.backup_databases()
        backup_manager.backup_config()
        return jsonify({"success": True, "message": "Backup created"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── HTML page ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    _init_integrations()  # Lazy init
    cfg = load_config()
    return render_template(
        "index.html",
        auto_refresh=cfg.get("web", {}).get("auto_refresh_seconds", 60),
        has_character=_character_tracker is not None,
        has_wormholes=_wormhole_tracker is not None,
        has_twitch=_twitch_integration is not None,
    )


# ── Opportunities ─────────────────────────────────────────────────────────

@app.route("/api/opportunities")
def api_opportunities():
    try:
        limit = int(request.args.get("limit", 100))
    except (ValueError, TypeError):
        abort(400, "limit must be an integer")
    
    try:
        results = db.get_results(limit)
        return jsonify({"results": results, "count": len(results)})
    except Exception as e:
        logger.error(f"Failed to fetch opportunities: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch opportunities", "details": str(e)}), 500


# ── Scan control ──────────────────────────────────────────────────────────

@app.route("/api/scan/status")
def api_scan_status():
    global _scan_running
    try:
        last = db.get_last_scan_time()
        count = len(db.get_results(10000))
        return jsonify({
            "last_scan": last,
            "opportunities_count": count,
            "scan_running": _scan_running,
        })
    except Exception as e:
        logger.error(f"Failed to get scan status: {e}", exc_info=True)
        return jsonify({"error": "Failed to get scan status", "details": str(e)}), 500


@app.route("/api/scan/run", methods=["POST"])
def api_scan_run():
    global _scan_running
    with _scan_lock:
        if _scan_running:
            return jsonify({"status": "already_running"}), 409
        _scan_running = True

    def _do_scan():
        global _scan_running
        try:
            scanner.run_scan(silent=True)
        finally:
            _scan_running = False

    t = threading.Thread(target=_do_scan, daemon=True)
    t.start()
    return jsonify({"status": "started"})


# ── Inventory ─────────────────────────────────────────────────────────────

@app.route("/api/inventory", methods=["GET"])
def api_inventory_get():
    items = db.get_inventory()

    # Enrich with current market value from cache
    cfg = load_config()
    region_map = get_region_map(cfg)
    jita_id = region_map.get("Jita", 10000002)

    enriched = []
    try:
        sell_orders = esi.get_sell_orders(jita_id, ttl_minutes=10)
    except Exception:
        sell_orders = {}

    for item in items:
        current_price = None
        type_id = item["type_id"]
        if type_id in sell_orders:
            result = esi.best_sell_price(sell_orders[type_id])
            if result:
                current_price = result[0]

        enriched.append({
            **item,
            "current_market_price": current_price,
            "unrealized_pnl": (
                (current_price - item["cost_basis_isk"]) * item["quantity"]
                if current_price is not None else None
            ),
        })

    return jsonify({"inventory": enriched})


@app.route("/api/inventory", methods=["POST"])
def api_inventory_add():
    data = request.get_json()
    if not data:
        abort(400, "JSON body required")

    item_name = data.get("item_name", "").strip()
    try:
        quantity = int(data.get("quantity", 0))
        cost_basis = float(data.get("cost_basis_isk", 0))
    except (ValueError, TypeError):
        abort(400, "quantity must be an integer and cost_basis_isk must be a number")
    station = data.get("station", "").strip()

    if not item_name or quantity <= 0 or cost_basis < 0:
        abort(400, "item_name, quantity > 0, and cost_basis_isk >= 0 required")

    # Look up type_id by name
    type_id = data.get("type_id")
    if not type_id:
        results = esi.search_type_ids(item_name)
        if not results:
            abort(404, f"Item '{item_name}' not found in EVE universe")
        # Use the first (best) match
        type_id = results[0]["type_id"]
        item_name = results[0]["name"]

    try:
        type_id = int(type_id)
    except (ValueError, TypeError):
        abort(400, "type_id must be an integer")

    row_id = db.add_inventory(
        type_id=type_id,
        item_name=item_name,
        quantity=quantity,
        cost_basis_isk=cost_basis,
        station=station,
    )
    return jsonify({"id": row_id, "item_name": item_name, "type_id": type_id}), 201


@app.route("/api/inventory/<int:row_id>", methods=["DELETE"])
def api_inventory_delete(row_id: int):
    deleted = db.delete_inventory(row_id)
    if not deleted:
        abort(404, "Inventory item not found")
    return jsonify({"deleted": True})


@app.route("/api/inventory/<int:row_id>", methods=["PATCH"])
def api_inventory_patch(row_id: int):
    data = request.get_json() or {}
    try:
        new_qty = int(data.get("quantity", 0))
    except (ValueError, TypeError):
        abort(400, "quantity must be an integer")
    if new_qty <= 0:
        abort(400, "quantity must be > 0")
    if not db.update_inventory_quantity(row_id, new_qty):
        abort(404, "Inventory item not found")
    return jsonify({"updated": True})


# ── Price lookup ──────────────────────────────────────────────────────────

@app.route("/api/prices/<query>")
def api_prices(query: str):
    cfg = load_config()
    region_map = get_region_map(cfg)

    search_results = esi.search_type_ids(query)
    if not search_results:
        return jsonify({"error": "Item not found"}), 404

    type_id = search_results[0]["type_id"]
    item_name = search_results[0]["name"]
    item_info = esi.get_item_info(type_id)

    hub_prices = []
    for region_name, region_id in region_map.items():
        try:
            sells = esi.get_sell_orders(region_id, ttl_minutes=10)
            buys = esi.get_buy_orders(region_id, ttl_minutes=10)

            best_sell = esi.best_sell_price(sells.get(type_id, []))
            best_buy = esi.best_buy_price(buys.get(type_id, []))

            hub_prices.append({
                "region": region_name,
                "lowest_sell": best_sell[0] if best_sell else None,
                "sell_volume": best_sell[1] if best_sell else None,
                "highest_buy": best_buy[0] if best_buy else None,
                "buy_volume": best_buy[1] if best_buy else None,
            })
        except Exception as exc:
            hub_prices.append({"region": region_name, "error": str(exc)})

    return jsonify({
        "type_id": type_id,
        "item_name": item_name,
        "volume_m3": item_info["volume"],
        "hubs": hub_prices,
    })


# ── Character Tracking ───────────────────────────────────────────────────────

@app.route("/api/character/status")
def api_character_status():
    if not _character_tracker:
        return jsonify({"error": "Character tracking not configured"}), 503
    try:
        status = _character_tracker.get_full_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/character/location")
def api_character_location():
    if not _character_tracker:
        return jsonify({"error": "Character tracking not configured"}), 503
    try:
        location = _character_tracker.get_location()
        return jsonify(location.__dict__)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/character/wallet")
def api_character_wallet():
    if not _character_tracker:
        return jsonify({"error": "Character tracking not configured"}), 503
    try:
        wallet = _character_tracker.get_wallet_balance()
        return jsonify(wallet.__dict__)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/character/transactions")
def api_character_transactions():
    if not _character_tracker:
        return jsonify({"error": "Character tracking not configured"}), 503
    try:
        limit = int(request.args.get("limit", 50))
        transactions = _character_tracker.get_wallet_transactions(limit)
        return jsonify({"transactions": [t.__dict__ for t in transactions]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/character/orders")
def api_character_orders():
    if not _character_tracker:
        return jsonify({"error": "Character tracking not configured"}), 503
    try:
        orders = _character_tracker.get_market_orders()
        return jsonify({"orders": [o.__dict__ for o in orders]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Wormhole Tracking ────────────────────────────────────────────────────────

@app.route("/api/wormholes/connections")
def api_wormholes_connections():
    if not _wormhole_tracker:
        return jsonify({"error": "Wormhole tracking not enabled"}), 503
    try:
        connections = _wormhole_tracker.get_active_connections()
        return jsonify({"connections": connections})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/wormholes/connection", methods=["POST"])
def api_wormholes_add_connection():
    if not _wormhole_tracker:
        return jsonify({"error": "Wormhole tracking not enabled"}), 503
    
    data = request.get_json()
    if not data:
        abort(400, "JSON body required")
    
    try:
        source_id = int(data["source_system_id"])
        dest_id = int(data["dest_system_id"])
        wh_type = data.get("wh_type", "Unknown")
        mass = data.get("mass_remaining", "Stable")
        time_left = data.get("time_remaining", "Fresh")
        
        _wormhole_tracker.add_connection(source_id, dest_id, wh_type, mass, time_left)
        return jsonify({"added": True}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/wormholes/connection/<int:conn_id>", methods=["PATCH"])
def api_wormholes_update_connection(conn_id: int):
    if not _wormhole_tracker:
        return jsonify({"error": "Wormhole tracking not enabled"}), 503
    
    data = request.get_json() or {}
    try:
        _wormhole_tracker.update_connection(
            conn_id,
            mass_remaining=data.get("mass_remaining"),
            time_remaining=data.get("time_remaining"),
        )
        return jsonify({"updated": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/wormholes/connection/<int:conn_id>", methods=["DELETE"])
def api_wormholes_expire_connection(conn_id: int):
    if not _wormhole_tracker:
        return jsonify({"error": "Wormhole tracking not enabled"}), 503
    
    try:
        _wormhole_tracker.expire_connection(conn_id)
        return jsonify({"expired": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/wormholes/chain/<int:system_id>")
def api_wormholes_chain(system_id: int):
    if not _wormhole_tracker:
        return jsonify({"error": "Wormhole tracking not enabled"}), 503
    
    try:
        max_depth = int(request.args.get("max_depth", 5))
        chain = _wormhole_tracker.get_chain_from_system(system_id, max_depth)
        return jsonify(chain)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/wormholes/history")
def api_wormholes_history():
    if not _wormhole_tracker:
        return jsonify({"error": "Wormhole tracking not enabled"}), 503
    
    try:
        limit = int(request.args.get("limit", 50))
        history = _wormhole_tracker.get_jump_history(limit)
        return jsonify({"history": history})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/wormholes/jump", methods=["POST"])
def api_wormholes_add_jump():
    if not _wormhole_tracker:
        return jsonify({"error": "Wormhole tracking not enabled"}), 503
    
    data = request.get_json()
    if not data:
        abort(400, "JSON body required")
    
    try:
        system_id = int(data["system_id"])
        notes = data.get("notes", "")
        _wormhole_tracker.add_jump(system_id, notes)
        return jsonify({"added": True}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/wormholes/favorites")
def api_wormholes_favorites():
    if not _wormhole_tracker:
        return jsonify({"error": "Wormhole tracking not enabled"}), 503
    
    try:
        favorites = _wormhole_tracker.get_favorites()
        return jsonify({"favorites": favorites})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Twitch Integration ───────────────────────────────────────────────────────

@app.route("/api/twitch/status")
def api_twitch_status():
    if not _twitch_integration:
        return jsonify({"error": "Twitch integration not configured"}), 503
    
    try:
        status = _twitch_integration.get_stream_status()
        return jsonify({
            "live": status is not None,
            "stream": status,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/twitch/title", methods=["POST"])
def api_twitch_update_title():
    if not _twitch_integration:
        return jsonify({"error": "Twitch integration not configured"}), 503
    
    data = request.get_json()
    if not data or "title" not in data:
        abort(400, "title required in JSON body")
    
    try:
        success = _twitch_integration.update_stream_title(data["title"])
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/twitch/marker", methods=["POST"])
def api_twitch_create_marker():
    if not _twitch_integration:
        return jsonify({"error": "Twitch integration not configured"}), 503
    
    data = request.get_json() or {}
    description = data.get("description", "")
    
    try:
        success = _twitch_integration.create_marker(description)
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def start_web(host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
    """Start the Flask development server."""
    app.run(host=host, port=port, debug=debug, use_reloader=False)
