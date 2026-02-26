"""
Personal character tracking via ESI authenticated endpoints.

Tracks all your character activities in real-time:
- Current location and ship
- Assets and inventory across all stations
- Wallet balance and transactions
- Market orders
- Mining ledger
- Jump history
- Skills and training queue
"""
from __future__ import annotations

import time
from typing import Optional
from dataclasses import dataclass, asdict
import requests

from api.oauth import get_authenticated_session
from api import esi

BASE_URL = "https://esi.evetech.net/latest"


@dataclass
class CharacterLocation:
    solar_system_id: int
    solar_system_name: str
    station_id: Optional[int] = None
    station_name: Optional[str] = None
    structure_id: Optional[int] = None
    structure_name: Optional[str] = None


@dataclass
class CharacterShip:
    ship_type_id: int
    ship_type_name: str
    ship_item_id: int
    ship_name: str


@dataclass
class CharacterStatus:
    online: bool
    last_login: Optional[str] = None
    last_logout: Optional[str] = None
    logins: int = 0


@dataclass
class WalletBalance:
    balance: float
    last_updated: float


@dataclass
class MarketTransaction:
    transaction_id: int
    date: str
    type_id: int
    item_name: str
    quantity: int
    unit_price: float
    total_value: float
    client_id: int
    location_id: int
    is_buy: bool
    is_personal: bool


@dataclass
class MarketOrder:
    order_id: int
    type_id: int
    item_name: str
    location_id: int
    volume_total: int
    volume_remain: int
    min_volume: int
    price: float
    is_buy_order: bool
    issued: str
    duration: int
    range: str
    state: str


class CharacterTracker:
    """Tracks personal character data via ESI."""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.session: Optional[requests.Session] = None
        self.character_info: Optional[dict] = None
        self._connect()
    
    def _connect(self):
        """Establish authenticated connection."""
        self.session, self.character_info = get_authenticated_session(self.client_id)
    
    def _get(self, endpoint: str, params: dict = None) -> requests.Response:
        """Make authenticated GET request."""
        if not self.session:
            self._connect()
        
        url = f"{BASE_URL}{endpoint}"
        resp = self.session.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp
    
    @property
    def character_id(self) -> int:
        return self.character_info["character_id"]
    
    @property
    def character_name(self) -> str:
        return self.character_info["character_name"]
    
    def get_location(self) -> CharacterLocation:
        """Get current character location."""
        resp = self._get(f"/characters/{self.character_id}/location/")
        data = resp.json()
        
        solar_system_id = data["solar_system_id"]
        
        # Get system name
        system_info = esi.get_system_info(solar_system_id)
        solar_system_name = system_info.get("name", f"System {solar_system_id}")
        
        location = CharacterLocation(
            solar_system_id=solar_system_id,
            solar_system_name=solar_system_name,
        )
        
        # Station or structure
        if "station_id" in data:
            location.station_id = data["station_id"]
            station_info = esi.get_station_info(data["station_id"])
            location.station_name = station_info.get("name", f"Station {data['station_id']}")
        elif "structure_id" in data:
            location.structure_id = data["structure_id"]
            try:
                structure_info = self._get(f"/universe/structures/{data['structure_id']}/").json()
                location.structure_name = structure_info.get("name", f"Structure {data['structure_id']}")
            except:
                location.structure_name = f"Structure {data['structure_id']}"
        
        return location
    
    def get_ship(self) -> CharacterShip:
        """Get current ship."""
        resp = self._get(f"/characters/{self.character_id}/ship/")
        data = resp.json()
        
        type_info = esi.get_item_info(data["ship_type_id"])
        
        return CharacterShip(
            ship_type_id=data["ship_type_id"],
            ship_type_name=type_info["name"],
            ship_item_id=data["ship_item_id"],
            ship_name=data["ship_name"],
        )
    
    def get_online_status(self) -> CharacterStatus:
        """Get online status."""
        resp = self._get(f"/characters/{self.character_id}/online/")
        data = resp.json()
        
        return CharacterStatus(
            online=data.get("online", False),
            last_login=data.get("last_login"),
            last_logout=data.get("last_logout"),
            logins=data.get("logins", 0),
        )
    
    def get_wallet_balance(self) -> WalletBalance:
        """Get wallet balance."""
        resp = self._get(f"/characters/{self.character_id}/wallet/")
        balance = resp.json()
        
        return WalletBalance(
            balance=float(balance),
            last_updated=time.time(),
        )
    
    def get_wallet_transactions(self, limit: int = 100) -> list[MarketTransaction]:
        """
        Get recent wallet transactions (market trades).
        Returns up to `limit` most recent transactions.
        """
        resp = self._get(
            f"/characters/{self.character_id}/wallet/transactions/",
            params={"from_id": 0}  # Can paginate with from_id if needed
        )
        transactions_data = resp.json()
        
        transactions = []
        for t in transactions_data[:limit]:
            item_info = esi.get_item_info(t["type_id"])
            
            transactions.append(MarketTransaction(
                transaction_id=t["transaction_id"],
                date=t["date"],
                type_id=t["type_id"],
                item_name=item_info["name"],
                quantity=t["quantity"],
                unit_price=t["unit_price"],
                total_value=t["unit_price"] * t["quantity"],
                client_id=t["client_id"],
                location_id=t["location_id"],
                is_buy=t["is_buy"],
                is_personal=t["is_personal"],
            ))
        
        return transactions
    
    def get_market_orders(self) -> list[MarketOrder]:
        """Get all active market orders."""
        resp = self._get(f"/characters/{self.character_id}/orders/")
        orders_data = resp.json()
        
        orders = []
        for o in orders_data:
            item_info = esi.get_item_info(o["type_id"])
            
            orders.append(MarketOrder(
                order_id=o["order_id"],
                type_id=o["type_id"],
                item_name=item_info["name"],
                location_id=o["location_id"],
                volume_total=o["volume_total"],
                volume_remain=o["volume_remain"],
                min_volume=o.get("min_volume", 1),
                price=o["price"],
                is_buy_order=o["is_buy_order"],
                issued=o["issued"],
                duration=o["duration"],
                range=o["range"],
                state=o.get("state", "open"),
            ))
        
        return orders
    
    def get_assets_summary(self) -> dict:
        """
        Get summary of all assets.
        Returns dict with total value estimate and item counts.
        """
        resp = self._get(f"/characters/{self.character_id}/assets/")
        assets = resp.json()
        
        # Group by type_id
        summary = {}
        total_items = 0
        
        for asset in assets:
            type_id = asset["type_id"]
            quantity = asset["quantity"]
            
            if type_id not in summary:
                item_info = esi.get_item_info(type_id)
                summary[type_id] = {
                    "type_id": type_id,
                    "name": item_info["name"],
                    "quantity": 0,
                }
            
            summary[type_id]["quantity"] += quantity
            total_items += quantity
        
        return {
            "total_items": total_items,
            "unique_types": len(summary),
            "by_type": list(summary.values()),
        }
    
    def get_skills_summary(self) -> dict:
        """Get skills summary."""
        resp = self._get(f"/characters/{self.character_id}/skills/")
        data = resp.json()
        
        skills = data.get("skills", [])
        
        return {
            "total_sp": data.get("total_sp", 0),
            "unallocated_sp": data.get("unallocated_sp", 0),
            "total_skills": len(skills),
        }
    
    def get_full_status(self) -> dict:
        """
        Get complete character status snapshot.
        Returns dict with all current character data.
        """
        try:
            location = self.get_location()
            ship = self.get_ship()
            online = self.get_online_status()
            wallet = self.get_wallet_balance()
            skills = self.get_skills_summary()
            
            return {
                "character_id": self.character_id,
                "character_name": self.character_name,
                "location": asdict(location),
                "ship": asdict(ship),
                "online": asdict(online),
                "wallet": asdict(wallet),
                "skills": skills,
                "timestamp": time.time(),
            }
        except Exception as e:
            return {
                "error": str(e),
                "character_id": self.character_id,
                "character_name": self.character_name,
                "timestamp": time.time(),
            }
