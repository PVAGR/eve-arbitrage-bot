"""
EVE ESI API client.

Public endpoints only — no authentication required.
Respects ESI rate-limit headers and caches to SQLite.
"""
from __future__ import annotations

import time
import requests
from typing import Iterator

from models import database as db

BASE_URL = "https://esi.evetech.net/latest"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "eve-arbitrage-bot/1.0 (github.com/PVAGR/eve-arbitrage-bot)"})

# Seconds to wait when ESI error limit is low
_THROTTLE_THRESHOLD = 20
_THROTTLE_SLEEP = 2.0


def _check_rate_limit(response: requests.Response):
    remain = int(response.headers.get("X-ESI-Error-Limit-Remain", 100))
    if remain < _THROTTLE_THRESHOLD:
        time.sleep(_THROTTLE_SLEEP)


def _get(url: str, params: dict = None) -> requests.Response:
    """GET with basic retry on 5xx / connection errors."""
    for attempt in range(3):
        try:
            resp = SESSION.get(url, params=params, timeout=15)
            _check_rate_limit(resp)
            if resp.status_code == 200:
                return resp
            if resp.status_code in (502, 503, 504):
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
        except requests.exceptions.ConnectionError:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to GET {url} after 3 attempts")


# ── Market orders ────────────────────────────────────────────────────────────

def fetch_region_orders(region_id: int, ttl_minutes: int = 5) -> list[dict]:
    """
    Fetch ALL market orders for a region (sell + buy).
    Uses SQLite cache; re-fetches if stale.
    Returns list of ESI order dicts.
    """
    # Get total page count from first page
    url = f"{BASE_URL}/markets/{region_id}/orders/"
    params = {"datasource": "tranquility", "order_type": "all", "page": 1}

    all_orders: list[dict] = []
    page = 1
    total_pages = 1

    while page <= total_pages:
        cached = db.get_cached_orders(region_id, page, ttl_minutes)
        if cached is not None:
            all_orders.extend(cached)
            page += 1
            continue

        params["page"] = page
        resp = _get(url, params)

        if page == 1:
            total_pages = int(resp.headers.get("X-Pages", 1))

        orders = resp.json()
        db.upsert_cached_orders(region_id, page, orders)
        all_orders.extend(orders)
        page += 1

    return all_orders


def get_sell_orders(region_id: int, ttl_minutes: int = 5) -> dict[int, list[dict]]:
    """Return {type_id: [orders...]} for sell orders only (is_buy_order=False)."""
    orders = fetch_region_orders(region_id, ttl_minutes)
    result: dict[int, list[dict]] = {}
    for o in orders:
        if not o.get("is_buy_order", False):
            result.setdefault(o["type_id"], []).append(o)
    return result


def get_buy_orders(region_id: int, ttl_minutes: int = 5) -> dict[int, list[dict]]:
    """Return {type_id: [orders...]} for buy orders only (is_buy_order=True)."""
    orders = fetch_region_orders(region_id, ttl_minutes)
    result: dict[int, list[dict]] = {}
    for o in orders:
        if o.get("is_buy_order", False):
            result.setdefault(o["type_id"], []).append(o)
    return result


def best_sell_price(orders: list[dict]) -> tuple[float, int] | None:
    """
    Given a list of sell orders for one item, return (lowest_price, volume_at_price).
    Returns None if the list is empty.
    """
    if not orders:
        return None
    orders_sorted = sorted(orders, key=lambda o: o["price"])
    best = orders_sorted[0]
    return best["price"], best["volume_remain"]


def best_buy_price(orders: list[dict]) -> tuple[float, int] | None:
    """
    Given a list of buy orders for one item, return (highest_price, volume_at_price).
    Returns None if the list is empty.
    """
    if not orders:
        return None
    orders_sorted = sorted(orders, key=lambda o: -o["price"])
    best = orders_sorted[0]
    return best["price"], best["volume_remain"]


# ── Item info ────────────────────────────────────────────────────────────────

def get_item_info(type_id: int) -> dict:
    """
    Return {"name": str, "volume": float} for a type_id.
    Uses 24-hour SQLite cache.
    """
    cached = db.get_cached_item(type_id)
    if cached:
        return cached

    url = f"{BASE_URL}/universe/types/{type_id}/"
    try:
        resp = _get(url, {"datasource": "tranquility", "language": "en"})
        data = resp.json()
        name = data.get("name", f"Item {type_id}")
        volume = float(data.get("packaged_volume", data.get("volume", 1.0)))
    except Exception:
        name = f"Item {type_id}"
        volume = 1.0

    db.upsert_item(type_id, name, volume)
    return {"name": name, "volume": volume}


def get_item_info_bulk(type_ids: list[int], progress_callback=None) -> dict[int, dict]:
    """
    Fetch info for multiple type_ids.
    Returns {type_id: {"name": ..., "volume": ...}}.
    Skips items already in cache.
    """
    result: dict[int, dict] = {}
    to_fetch = []

    for tid in type_ids:
        cached = db.get_cached_item(tid)
        if cached:
            result[tid] = cached
        else:
            to_fetch.append(tid)

    for i, tid in enumerate(to_fetch):
        result[tid] = get_item_info(tid)
        if progress_callback and i % 50 == 0:
            progress_callback(i, len(to_fetch))

    return result


# ── Adjusted prices (market reference) ──────────────────────────────────────

def fetch_adjusted_prices() -> dict[int, float]:
    """
    Fetch ESI adjusted prices for all items.
    Returns {type_id: adjusted_price}.
    Useful as a reference but not used for arbitrage directly.
    """
    resp = _get(f"{BASE_URL}/markets/prices/", {"datasource": "tranquility"})
    return {entry["type_id"]: entry.get("adjusted_price", 0.0) for entry in resp.json()}


# ── Search items by name ─────────────────────────────────────────────────────

def search_type_ids(query: str) -> list[dict]:
    """
    Search EVE universe for items matching a name query.
    Returns list of {type_id, name} dicts (up to 20 results).
    """
    url = f"{BASE_URL}/search/"
    params = {
        "categories": "inventory_type",
        "datasource": "tranquility",
        "language": "en",
        "search": query,
        "strict": False,
    }
    resp = _get(url, params)
    data = resp.json()
    type_ids = data.get("inventory_type", [])[:20]

    results = []
    for tid in type_ids:
        info = get_item_info(tid)
        results.append({"type_id": tid, "name": info["name"]})
    return results


# ── System and station info ──────────────────────────────────────────────────

def get_system_info(system_id: int) -> dict:
    """
    Get solar system information.
    Returns dict with name, security_status, etc.
    Cached for 24 hours.
    """
    cached = db.get_cached_system(system_id)
    if cached:
        return cached
    
    url = f"{BASE_URL}/universe/systems/{system_id}/"
    try:
        resp = _get(url, {"datasource": "tranquility"})
        data = resp.json()
        info = {
            "system_id": system_id,
            "name": data.get("name", f"System {system_id}"),
            "security_status": data.get("security_status", 0.0),
            "constellation_id": data.get("constellation_id"),
            "star_id": data.get("star_id"),
        }
    except Exception:
        info = {
            "system_id": system_id,
            "name": f"System {system_id}",
            "security_status": 0.0,
        }
    
    db.upsert_system(system_id, info)
    return info


def get_station_info(station_id: int) -> dict:
    """
    Get station information.
    Returns dict with name, system_id, etc.
    Cached for 24 hours.
    """
    cached = db.get_cached_station(station_id)
    if cached:
        return cached
    
    url = f"{BASE_URL}/universe/stations/{station_id}/"
    try:
        resp = _get(url, {"datasource": "tranquility"})
        data = resp.json()
        info = {
            "station_id": station_id,
            "name": data.get("name", f"Station {station_id}"),
            "system_id": data.get("system_id"),
            "type_id": data.get("type_id"),
        }
    except Exception:
        info = {
            "station_id": station_id,
            "name": f"Station {station_id}",
        }
    
    db.upsert_station(station_id, info)
    return info


# ── ESI class interface ──────────────────────────────────────────────────────

class ESI:
    """Class wrapper for ESI API operations."""
    
    def __init__(self, config: dict = None):
        """Initialize ESI client. Config parameter is optional for compatibility."""
        pass
    
    def get_sell_orders(self, region_id: int, ttl_minutes: int = 60) -> dict:
        """Get sell orders for a region."""
        return get_sell_orders(region_id)
    
    def get_buy_orders(self, region_id: int, ttl_minutes: int = 60) -> dict:
        """Get buy orders for a region."""
        return get_buy_orders(region_id)
    
    def best_sell_price(self, orders: list) -> tuple:
        """Get best sell price from orders list."""
        return best_sell_price(orders)
    
    def best_buy_price(self, orders: list) -> tuple:
        """Get best buy price from orders list."""
        return best_buy_price(orders)
    
    def search_type_ids(self, search_term: str) -> list:
        """Search for items by name."""
        return search_types(search_term)
    
    def get_item_info(self, type_id: int) -> dict:
        """Get item information."""
        return get_item_info(type_id)
    
    def get_system_info(self, system_id: int) -> dict:
        """Get system information."""
        return get_system_info(system_id)
    
    def get_station_info(self, station_id: int) -> dict:
        """Get station information."""
        return get_station_info(station_id)

