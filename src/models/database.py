"""
SQLite database layer.
Tables:
  - market_cache   : cached ESI market order pages
  - item_names     : item_id → name/volume lookup cache
  - arbitrage_results : last scan results
  - inventory      : user's stock tracking
"""
import sqlite3
import os
import sys
import json
from datetime import datetime, timezone


def _db_path() -> str:
    """
    Resolve the database file path.
    - Frozen (.exe): next to the executable so data persists between runs.
    - Script: <project_root>/data/eve_arbitrage.db
    """
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, "data", "eve_arbitrage.db")


def get_connection() -> sqlite3.Connection:
    db_path = _db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create all tables if they do not exist."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS market_cache (
                region_id   INTEGER NOT NULL,
                page        INTEGER NOT NULL,
                fetched_at  TEXT    NOT NULL,
                orders_json TEXT    NOT NULL,
                PRIMARY KEY (region_id, page)
            );

            CREATE TABLE IF NOT EXISTS item_names (
                type_id     INTEGER PRIMARY KEY,
                name        TEXT    NOT NULL,
                volume      REAL    NOT NULL DEFAULT 1.0,
                fetched_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS arbitrage_results (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                scanned_at      TEXT    NOT NULL,
                buy_region      TEXT    NOT NULL,
                sell_region     TEXT    NOT NULL,
                type_id         INTEGER NOT NULL,
                item_name       TEXT    NOT NULL,
                buy_price       REAL    NOT NULL,
                sell_price      REAL    NOT NULL,
                volume_available INTEGER NOT NULL,
                net_profit_per_unit REAL NOT NULL,
                profit_margin_pct   REAL NOT NULL,
                total_profit_potential REAL NOT NULL,
                item_volume_m3  REAL    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS inventory (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                type_id         INTEGER NOT NULL,
                item_name       TEXT    NOT NULL,
                quantity        INTEGER NOT NULL,
                cost_basis_isk  REAL    NOT NULL,
                station         TEXT    NOT NULL DEFAULT '',
                added_at        TEXT    NOT NULL
            );
        """)


# ── Market cache ────────────────────────────────────────────────────────────

def get_cached_orders(region_id: int, page: int, ttl_minutes: int) -> list | None:
    """Return cached orders list or None if stale/missing."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT orders_json, fetched_at FROM market_cache WHERE region_id=? AND page=?",
            (region_id, page)
        ).fetchone()
    if row is None:
        return None
    fetched = datetime.fromisoformat(row["fetched_at"])
    age_minutes = (datetime.now(timezone.utc).replace(tzinfo=None) - fetched).total_seconds() / 60
    if age_minutes > ttl_minutes:
        return None
    return json.loads(row["orders_json"])


def upsert_cached_orders(region_id: int, page: int, orders: list):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO market_cache (region_id, page, fetched_at, orders_json)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(region_id, page) DO UPDATE SET
                 fetched_at=excluded.fetched_at,
                 orders_json=excluded.orders_json""",
            (region_id, page, datetime.now(timezone.utc).replace(tzinfo=None).isoformat(), json.dumps(orders))
        )


# ── Item name cache ──────────────────────────────────────────────────────────

def get_cached_item(type_id: int, ttl_hours: int = 24) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT name, volume, fetched_at FROM item_names WHERE type_id=?",
            (type_id,)
        ).fetchone()
    if row is None:
        return None
    fetched = datetime.fromisoformat(row["fetched_at"])
    age_hours = (datetime.now(timezone.utc).replace(tzinfo=None) - fetched).total_seconds() / 3600
    if age_hours > ttl_hours:
        return None
    return {"name": row["name"], "volume": row["volume"]}


def upsert_item(type_id: int, name: str, volume: float):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO item_names (type_id, name, volume, fetched_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(type_id) DO UPDATE SET
                 name=excluded.name,
                 volume=excluded.volume,
                 fetched_at=excluded.fetched_at""",
            (type_id, name, volume, datetime.now(timezone.utc).replace(tzinfo=None).isoformat())
        )


# ── Arbitrage results ────────────────────────────────────────────────────────

def save_results(results: list[dict]):
    """Persist a list of arbitrage result dicts, replacing old results for same region pair."""
    if not results:
        return
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    with get_connection() as conn:
        # Delete previous results for each unique pair in this batch
        pairs = {(r["buy_region"], r["sell_region"]) for r in results}
        for buy_r, sell_r in pairs:
            conn.execute(
                "DELETE FROM arbitrage_results WHERE buy_region=? AND sell_region=?",
                (buy_r, sell_r)
            )
        conn.executemany(
            """INSERT INTO arbitrage_results
               (scanned_at, buy_region, sell_region, type_id, item_name,
                buy_price, sell_price, volume_available,
                net_profit_per_unit, profit_margin_pct,
                total_profit_potential, item_volume_m3)
               VALUES (:scanned_at, :buy_region, :sell_region, :type_id, :item_name,
                       :buy_price, :sell_price, :volume_available,
                       :net_profit_per_unit, :profit_margin_pct,
                       :total_profit_potential, :item_volume_m3)""",
            [{**r, "scanned_at": now} for r in results]
        )


def get_results(limit: int = 100) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM arbitrage_results
               ORDER BY total_profit_potential DESC
               LIMIT ?""",
            (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_last_scan_time() -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT MAX(scanned_at) as last FROM arbitrage_results"
        ).fetchone()
    return row["last"] if row else None


# ── Inventory ────────────────────────────────────────────────────────────────

def add_inventory(type_id: int, item_name: str, quantity: int,
                  cost_basis_isk: float, station: str = "") -> int:
    """Insert or update an inventory row. Returns the row id."""
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO inventory
               (type_id, item_name, quantity, cost_basis_isk, station, added_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (type_id, item_name, quantity, cost_basis_isk, station,
             datetime.now(timezone.utc).replace(tzinfo=None).isoformat())
        )
        return cur.lastrowid


def get_inventory() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM inventory ORDER BY item_name"
        ).fetchall()
    return [dict(r) for r in rows]


def delete_inventory(row_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM inventory WHERE id=?", (row_id,))
    return cur.rowcount > 0


def update_inventory_quantity(row_id: int, new_quantity: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE inventory SET quantity=? WHERE id=?",
            (new_quantity, row_id)
        )
    return cur.rowcount > 0
