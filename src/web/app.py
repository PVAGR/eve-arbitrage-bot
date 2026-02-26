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
"""
from __future__ import annotations

import threading
from flask import Flask, jsonify, render_template, request, abort

from config import load_config, get_region_map
from models import database as db
from engine import scanner
from api import esi

app = Flask(__name__)
db.init_db()

_scan_lock = threading.Lock()
_scan_running = False


# ── HTML page ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    cfg = load_config()
    return render_template(
        "index.html",
        auto_refresh=cfg.get("web", {}).get("auto_refresh_seconds", 60),
    )


# ── Opportunities ─────────────────────────────────────────────────────────

@app.route("/api/opportunities")
def api_opportunities():
    limit = int(request.args.get("limit", 100))
    results = db.get_results(limit)
    return jsonify({"results": results, "count": len(results)})


# ── Scan control ──────────────────────────────────────────────────────────

@app.route("/api/scan/status")
def api_scan_status():
    global _scan_running
    last = db.get_last_scan_time()
    count = len(db.get_results(10000))
    return jsonify({
        "last_scan": last,
        "opportunities_count": count,
        "scan_running": _scan_running,
    })


@app.route("/api/scan/run", methods=["POST"])
def api_scan_run():
    global _scan_running
    if _scan_running:
        return jsonify({"status": "already_running"}), 409

    def _do_scan():
        global _scan_running
        _scan_running = True
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
    quantity = int(data.get("quantity", 0))
    cost_basis = float(data.get("cost_basis_isk", 0))
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

    row_id = db.add_inventory(
        type_id=int(type_id),
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
    new_qty = int(data.get("quantity", 0))
    if new_qty <= 0:
        abort(400, "quantity must be > 0")
    db.update_inventory_quantity(row_id, new_qty)
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


def start_web(host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
    """Start the Flask development server."""
    app.run(host=host, port=port, debug=debug, use_reloader=False)
