"""
Wormhole tracking and mapping system.

Tracks:
- Wormhole connections and chains
- System security classes (C1-C6, Thera, etc.)
- Statics and wandering connections
- Jump history through wormholes
- Favorite wormhole systems
"""
from __future__ import annotations

import time
import json
import os
from typing import Optional
from dataclasses import dataclass, asdict
import sqlite3

from api import esi


@dataclass
class WormholeSystem:
    system_id: int
    system_name: str
    security_status: float
    wh_class: str  # "C1", "C2", "C3", "C4", "C5", "C6", "Thera", "HS", "LS", "NS"
    statics: list[str]  # ["C3", "HS"] etc
    effect: Optional[str] = None  # "Pulsar", "Magnetar", etc


@dataclass
class WormholeConnection:
    source_system_id: int
    source_system_name: str
    dest_system_id: int
    dest_system_name: str
    wh_type: str  # "K162", "A239", etc
    mass_remaining: str  # "Stable", "Destabilized", "Critical"
    time_remaining: str  # "Fresh", "EOL"
    discovered_at: float
    last_seen: float


class WormholeTracker:
    """Track wormhole connections and systems."""
    
    def __init__(self, config_or_path=None):
        """
        Initialize wormhole tracker.
        
        Args:
            config_or_path: Either a config dict or path string. If config dict,
                          uses wormholes.database_path from it. If string, uses as path directly.
                          If None, uses default 'data/wormholes.db'.
        """
        if isinstance(config_or_path, dict):
            # It's a config dict
            self.db_path = config_or_path.get('wormholes', {}).get('database_path', 'data/wormholes.db')
        elif isinstance(config_or_path, str):
            # It's a path string
            self.db_path = config_or_path
        else:
            # Default
            self.db_path = 'data/wormholes.db'
        
        os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)
        self._init_db()
        self._load_static_data()
    
    def _init_db(self):
        """Initialize wormhole database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS wh_systems (
                    system_id       INTEGER PRIMARY KEY,
                    system_name     TEXT NOT NULL,
                    security_status REAL NOT NULL,
                    wh_class        TEXT NOT NULL,
                    statics_json    TEXT NOT NULL,
                    effect          TEXT,
                    notes           TEXT,
                    is_favorite     INTEGER DEFAULT 0,
                    last_visited    TEXT
                );

                CREATE TABLE IF NOT EXISTS wh_connections (
                    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_system_id    INTEGER NOT NULL,
                    source_system_name  TEXT NOT NULL,
                    dest_system_id      INTEGER NOT NULL,
                    dest_system_name    TEXT NOT NULL,
                    wh_type             TEXT NOT NULL,
                    mass_remaining      TEXT NOT NULL,
                    time_remaining      TEXT NOT NULL,
                    discovered_at       REAL NOT NULL,
                    last_seen           REAL NOT NULL,
                    expired             INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS jump_history (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    system_id   INTEGER NOT NULL,
                    system_name TEXT NOT NULL,
                    timestamp   REAL NOT NULL,
                    notes       TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_connections_source ON wh_connections(source_system_id);
                CREATE INDEX IF NOT EXISTS idx_connections_dest ON wh_connections(dest_system_id);
                CREATE INDEX IF NOT EXISTS idx_connections_expired ON wh_connections(expired);
                CREATE INDEX IF NOT EXISTS idx_jump_history_timestamp ON jump_history(timestamp);
            """)
    
    def _load_static_data(self):
        """Load known wormhole static data."""
        # This would normally load from a data file with wormhole classes and statics
        # For now, we'll track systems as they're discovered
        pass
    
    def add_system(self, system_id: int, wh_class: str, statics: list[str], 
                   effect: Optional[str] = None, notes: str = ""):
        """Add or update a wormhole system."""
        system_info = esi.get_system_info(system_id)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO wh_systems 
                (system_id, system_name, security_status, wh_class, statics_json, effect, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(system_id) DO UPDATE SET
                    wh_class=excluded.wh_class,
                    statics_json=excluded.statics_json,
                    effect=excluded.effect,
                    notes=excluded.notes
            """, (
                system_id,
                system_info["name"],
                system_info["security_status"],
                wh_class,
                json.dumps(statics),
                effect,
                notes,
            ))
    
    def add_connection(self, source_system_id: int, dest_system_id: int,
                       wh_type: str, mass_remaining: str = "Stable",
                       time_remaining: str = "Fresh"):
        """Add a wormhole connection."""
        source_info = esi.get_system_info(source_system_id)
        dest_info = esi.get_system_info(dest_system_id)
        
        now = time.time()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO wh_connections
                (source_system_id, source_system_name, dest_system_id, dest_system_name,
                 wh_type, mass_remaining, time_remaining, discovered_at, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source_system_id, source_info["name"],
                dest_system_id, dest_info["name"],
                wh_type, mass_remaining, time_remaining,
                now, now,
            ))
    
    def update_connection(self, connection_id: int, mass_remaining: str = None,
                          time_remaining: str = None):
        """Update connection status."""
        updates = []
        params = []
        
        if mass_remaining:
            updates.append("mass_remaining=?")
            params.append(mass_remaining)
        
        if time_remaining:
            updates.append("time_remaining=?")
            params.append(time_remaining)
        
        if not updates:
            return
        
        updates.append("last_seen=?")
        params.append(time.time())
        params.append(connection_id)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"UPDATE wh_connections SET {', '.join(updates)} WHERE id=?",
                params
            )
    
    def expire_connection(self, connection_id: int):
        """Mark a connection as expired/collapsed."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE wh_connections SET expired=1 WHERE id=?",
                (connection_id,)
            )
    
    def get_active_connections(self) -> list[dict]:
        """Get all active (non-expired) connections."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM wh_connections
                WHERE expired=0
                ORDER BY last_seen DESC
            """).fetchall()
        
        return [dict(row) for row in rows]
    
    def get_connections_from_system(self, system_id: int) -> list[dict]:
        """Get all connections from a specific system."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM wh_connections
                WHERE source_system_id=? AND expired=0
                ORDER BY last_seen DESC
            """, (system_id,)).fetchall()
        
        return [dict(row) for row in rows]
    
    def get_chain_from_system(self, system_id: int, max_depth: int = 5) -> dict:
        """
        Build a chain/map of connections starting from a system.
        Returns nested structure showing all reachable systems.
        """
        visited = set()
        
        def _build_chain(sys_id: int, depth: int) -> dict:
            if depth >= max_depth or sys_id in visited:
                return {}
            
            visited.add(sys_id)
            connections = self.get_connections_from_system(sys_id)
            
            result = {
                "system_id": sys_id,
                "connections": [],
            }
            
            for conn in connections:
                dest_id = conn["dest_system_id"]
                result["connections"].append({
                    "connection": conn,
                    "chain": _build_chain(dest_id, depth + 1),
                })
            
            return result
        
        return _build_chain(system_id, 0)
    
    def add_jump(self, system_id: int, notes: str = ""):
        """Record a jump to a system."""
        system_info = esi.get_system_info(system_id)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO jump_history (system_id, system_name, timestamp, notes)
                VALUES (?, ?, ?, ?)
            """, (system_id, system_info["name"], time.time(), notes))
            
            # Update last_visited for wh system if tracked
            conn.execute("""
                UPDATE wh_systems
                SET last_visited=?
                WHERE system_id=?
            """, (time.time(), system_id))
    
    def get_jump_history(self, limit: int = 50) -> list[dict]:
        """Get recent jump history."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM jump_history
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,)).fetchall()
        
        return [dict(row) for row in rows]
    
    def toggle_favorite(self, system_id: int):
        """Toggle favorite status for a system."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE wh_systems
                SET is_favorite = CASE WHEN is_favorite = 1 THEN 0 ELSE 1 END
                WHERE system_id=?
            """, (system_id,))
    
    def get_favorites(self) -> list[dict]:
        """Get all favorite wormhole systems."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM wh_systems
                WHERE is_favorite=1
                ORDER BY system_name
            """).fetchall()
        
        return [dict(row) for row in rows]
    
    def auto_track_location(self, system_id: int):
        """
        Automatically track location changes.
        If jumping to a wormhole system, add to jump history.
        """
        system_info = esi.get_system_info(system_id)
        security = system_info.get("security_status", 0.0)
        
        # Wormhole space has security < -0.99
        if security < -0.99 or system_info["name"].startswith("J"):
            self.add_jump(system_id, "Auto-tracked")
