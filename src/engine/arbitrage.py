"""
Core arbitrage logic.

Given sell orders from a source region and buy orders from a destination region,
finds all items where you can buy cheap in source and sell high in destination.
"""
from __future__ import annotations
from dataclasses import dataclass

from engine.fees import FeeConfig, calculate_profit, is_profitable
from api import esi


@dataclass
class ArbitrageOpportunity:
    type_id: int
    item_name: str
    item_volume_m3: float
    buy_region: str
    sell_region: str
    buy_price: float
    sell_price: float
    volume_available: int
    net_profit_per_unit: float
    profit_margin_pct: float
    total_profit_potential: float

    def to_dict(self) -> dict:
        return {
            "type_id": self.type_id,
            "item_name": self.item_name,
            "item_volume_m3": self.item_volume_m3,
            "buy_region": self.buy_region,
            "sell_region": self.sell_region,
            "buy_price": self.buy_price,
            "sell_price": self.sell_price,
            "volume_available": self.volume_available,
            "net_profit_per_unit": self.net_profit_per_unit,
            "profit_margin_pct": self.profit_margin_pct,
            "total_profit_potential": self.total_profit_potential,
        }


def find_opportunities(
    source_region_name: str,
    source_region_id: int,
    dest_region_name: str,
    dest_region_id: int,
    fee_config: FeeConfig,
    filters: dict,
    ttl_minutes: int = 5,
    progress_cb=None,
) -> list[ArbitrageOpportunity]:
    """
    Find arbitrage opportunities: buy cheap in source, sell high in dest.
    Returns list of ArbitrageOpportunity sorted by total_profit_potential desc.
    """
    min_margin = filters.get("min_profit_margin_pct", 10)
    min_isk = filters.get("min_net_isk_profit", 1_000_000)
    max_invest = filters.get("max_investment_per_item", 0)
    min_vol = filters.get("min_volume_available", 1)

    if progress_cb:
        progress_cb(f"Fetching sell orders from {source_region_name}...")
    source_sells = esi.get_sell_orders(source_region_id, ttl_minutes)

    if progress_cb:
        progress_cb(f"Fetching buy orders from {dest_region_name}...")
    dest_buys = esi.get_buy_orders(dest_region_id, ttl_minutes)

    # Items that appear in both markets
    common_type_ids = set(source_sells.keys()) & set(dest_buys.keys())

    if progress_cb:
        progress_cb(f"Analysing {len(common_type_ids):,} common items...")

    # Bulk fetch item info for unknown items
    esi.get_item_info_bulk(list(common_type_ids))

    opportunities: list[ArbitrageOpportunity] = []

    for type_id in common_type_ids:
        sell_result = esi.best_sell_price(source_sells[type_id])
        buy_result = esi.best_buy_price(dest_buys[type_id])

        if sell_result is None or buy_result is None:
            continue

        buy_price, available_vol = sell_result   # we buy at this sell price
        sell_price, _ = buy_result               # we sell at this buy price

        if available_vol < min_vol:
            continue

        if max_invest > 0 and buy_price > max_invest:
            continue

        item_info = esi.get_item_info(type_id)
        item_volume = item_info["volume"]
        item_name = item_info["name"]

        net_profit, margin_pct = calculate_profit(
            buy_price, sell_price, item_volume, fee_config
        )

        if not is_profitable(net_profit, margin_pct, min_margin, min_isk):
            continue

        total_potential = net_profit * available_vol

        opportunities.append(ArbitrageOpportunity(
            type_id=type_id,
            item_name=item_name,
            item_volume_m3=item_volume,
            buy_region=source_region_name,
            sell_region=dest_region_name,
            buy_price=buy_price,
            sell_price=sell_price,
            volume_available=available_vol,
            net_profit_per_unit=net_profit,
            profit_margin_pct=margin_pct,
            total_profit_potential=total_potential,
        ))

    opportunities.sort(key=lambda o: -o.total_profit_potential)
    return opportunities
