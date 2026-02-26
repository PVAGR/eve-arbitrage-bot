"""
Fee and profit calculations for EVE Online market trading.

Cost model:
  You buy at: buy_price  (you pay this + broker fee on buy order)
  You sell at: sell_price (you receive this - broker fee - sales tax)

  net_profit = sell_price * (1 - broker_fee_sell - sales_tax)
             - buy_price  * (1 + broker_fee_buy)
             - hauling_cost_per_m3 * item_volume_m3
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class FeeConfig:
    broker_fee_buy: float = 0.03
    broker_fee_sell: float = 0.03
    sales_tax: float = 0.08
    hauling_isk_per_m3: float = 800.0

    @classmethod
    def from_config(cls, cfg: dict) -> "FeeConfig":
        fees = cfg.get("fees", {})
        return cls(
            broker_fee_buy=fees.get("broker_fee_buy", 0.03),
            broker_fee_sell=fees.get("broker_fee_sell", 0.03),
            sales_tax=fees.get("sales_tax", 0.08),
            hauling_isk_per_m3=fees.get("hauling_isk_per_m3", 800.0),
        )


def calculate_profit(
    buy_price: float,
    sell_price: float,
    item_volume_m3: float,
    fee_config: FeeConfig,
) -> tuple[float, float]:
    """
    Returns (net_profit_per_unit, profit_margin_pct).

    net_profit_per_unit: ISK earned per unit after all fees
    profit_margin_pct:   net_profit / buy_price * 100
    """
    effective_cost = buy_price * (1.0 + fee_config.broker_fee_buy)
    effective_revenue = sell_price * (1.0 - fee_config.broker_fee_sell - fee_config.sales_tax)
    hauling = fee_config.hauling_isk_per_m3 * item_volume_m3

    net_profit = effective_revenue - effective_cost - hauling
    margin_pct = (net_profit / effective_cost * 100) if effective_cost > 0 else 0.0
    return net_profit, margin_pct


def is_profitable(
    net_profit: float,
    margin_pct: float,
    min_margin_pct: float,
    min_net_isk: float,
) -> bool:
    return net_profit >= min_net_isk and margin_pct >= min_margin_pct
