"""
Command-line interface for the EVE Arbitrage Bot.
Uses Click for command parsing and Rich for output formatting.
"""
from __future__ import annotations

import sys
import os

import click
from rich.console import Console
from rich.table import Table
from rich.text import Text

# Ensure src/ is importable when invoked via run.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import database as db
from engine import scanner
from api import esi
from config import load_config, get_region_map

console = Console()


@click.group()
def cli():
    """EVE Online Arbitrage Bot — find cross-region market opportunities."""
    db.init_db()


# ── scan ─────────────────────────────────────────────────────────────────────

@cli.command()
@click.option(
    "--regions", "-r",
    nargs=2,
    multiple=True,
    metavar="SOURCE DEST",
    help="Region pair to scan, e.g. --regions Jita Amarr. Repeatable. "
         "Defaults to all pairs in config.yaml.",
)
def scan(regions):
    """Run a market scan and save arbitrage opportunities to the database."""
    region_pairs = list(regions) if regions else None
    results = scanner.run_scan(region_pairs=region_pairs, silent=False)
    console.print(f"\n[bold green]{len(results)}[/bold green] opportunities saved.")


# ── top ──────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("n", default=20, type=int)
def top(n):
    """Show the top N arbitrage opportunities from the last scan. Default: 20."""
    rows = db.get_results(limit=n)
    if not rows:
        console.print("[yellow]No results found. Run [bold]scan[/bold] first.[/yellow]")
        return

    table = Table(
        title=f"Top {n} Arbitrage Opportunities",
        show_lines=False,
        header_style="bold cyan",
    )
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Item", min_width=24)
    table.add_column("Buy Region", min_width=12)
    table.add_column("Sell Region", min_width=12)
    table.add_column("Buy Price", justify="right")
    table.add_column("Sell Price", justify="right")
    table.add_column("Profit/unit", justify="right")
    table.add_column("Margin %", justify="right")
    table.add_column("Vol", justify="right")
    table.add_column("Total ISK", justify="right", style="bold green")

    for i, r in enumerate(rows, 1):
        margin_color = "green" if r["profit_margin_pct"] >= 10 else "yellow"
        table.add_row(
            str(i),
            r["item_name"],
            r["buy_region"],
            r["sell_region"],
            _isk(r["buy_price"]),
            _isk(r["sell_price"]),
            _isk(r["net_profit_per_unit"]),
            Text(f"{r['profit_margin_pct']:.1f}%", style=margin_color),
            str(r["volume_available"]),
            _isk(r["total_profit_potential"]),
        )

    console.print(table)
    last = db.get_last_scan_time()
    if last:
        console.print(f"[dim]Last scan: {last}[/dim]")


# ── lookup ───────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("query")
def lookup(query):
    """Look up current prices for an item across all market hubs."""
    console.print(f"Searching for [bold]{query}[/bold]...")

    matches = esi.search_type_ids(query)
    if not matches:
        console.print(f"[red]No items found matching '{query}'.[/red]")
        return

    hit = matches[0]
    type_id = hit["type_id"]
    item_name = hit["name"]
    item_info = esi.get_item_info(type_id)

    console.print(
        f"\n[bold cyan]{item_name}[/bold cyan] "
        f"(type_id={type_id}, volume={item_info['volume']} m³)\n"
    )

    cfg = load_config()
    region_map = get_region_map(cfg)

    table = Table(header_style="bold cyan", show_lines=False)
    table.add_column("Region", min_width=12)
    table.add_column("Lowest Sell", justify="right")
    table.add_column("Sell Vol", justify="right")
    table.add_column("Highest Buy", justify="right")
    table.add_column("Buy Vol", justify="right")

    for region_name, region_id in region_map.items():
        try:
            sells = esi.get_sell_orders(region_id, ttl_minutes=10)
            buys = esi.get_buy_orders(region_id, ttl_minutes=10)
            best_sell = esi.best_sell_price(sells.get(type_id, []))
            best_buy = esi.best_buy_price(buys.get(type_id, []))
        except Exception as exc:
            table.add_row(region_name, f"[red]Error: {exc}[/red]", "", "", "")
            continue

        table.add_row(
            region_name,
            _isk(best_sell[0]) if best_sell else "[dim]—[/dim]",
            str(best_sell[1]) if best_sell else "[dim]—[/dim]",
            _isk(best_buy[0]) if best_buy else "[dim]—[/dim]",
            str(best_buy[1]) if best_buy else "[dim]—[/dim]",
        )

    console.print(table)


# ── inventory ────────────────────────────────────────────────────────────────

@cli.group()
def inventory():
    """Manage your item inventory."""


@inventory.command("list")
def inventory_list():
    """List all items in your inventory."""
    items = db.get_inventory()
    if not items:
        console.print("[yellow]Inventory is empty.[/yellow]")
        return

    table = Table(title="Inventory", header_style="bold cyan", show_lines=False)
    table.add_column("ID", style="dim", width=5, justify="right")
    table.add_column("Item", min_width=24)
    table.add_column("Qty", justify="right")
    table.add_column("Cost Basis/unit", justify="right")
    table.add_column("Total Cost", justify="right")
    table.add_column("Station")
    table.add_column("Added At", style="dim")

    for item in items:
        total_cost = item["quantity"] * item["cost_basis_isk"]
        table.add_row(
            str(item["id"]),
            item["item_name"],
            str(item["quantity"]),
            _isk(item["cost_basis_isk"]),
            _isk(total_cost),
            item.get("station") or "[dim]—[/dim]",
            item["added_at"][:16],
        )

    console.print(table)


@inventory.command("add")
@click.argument("item_name")
@click.argument("quantity", type=int)
@click.argument("cost_basis", type=float)
@click.option("--station", "-s", default="", help="Station or system name.")
def inventory_add(item_name, quantity, cost_basis, station):
    """Add an item to inventory.

    \b
    ITEM_NAME   Item name (will be looked up in EVE universe)
    QUANTITY    Number of units
    COST_BASIS  ISK per unit paid
    """
    if quantity <= 0:
        console.print("[red]Quantity must be greater than 0.[/red]")
        return
    if cost_basis < 0:
        console.print("[red]Cost basis cannot be negative.[/red]")
        return

    console.print(f"Looking up [bold]{item_name}[/bold]...")
    matches = esi.search_type_ids(item_name)
    if not matches:
        console.print(f"[red]Item '{item_name}' not found in EVE universe.[/red]")
        return

    hit = matches[0]
    type_id = hit["type_id"]
    resolved_name = hit["name"]

    row_id = db.add_inventory(
        type_id=type_id,
        item_name=resolved_name,
        quantity=quantity,
        cost_basis_isk=cost_basis,
        station=station,
    )
    console.print(
        f"[green]Added[/green] [bold]{resolved_name}[/bold] "
        f"x{quantity} @ {_isk(cost_basis)}/unit "
        f"(id={row_id})"
    )


@inventory.command("remove")
@click.argument("item_id", type=int)
def inventory_remove(item_id):
    """Remove an item from inventory by its ID."""
    deleted = db.delete_inventory(item_id)
    if deleted:
        console.print(f"[green]Removed inventory item id={item_id}.[/green]")
    else:
        console.print(f"[red]No inventory item with id={item_id}.[/red]")


@inventory.command("update")
@click.argument("item_id", type=int)
@click.argument("quantity", type=int)
def inventory_update(item_id, quantity):
    """Update the quantity of an inventory item by its ID."""
    if quantity <= 0:
        console.print("[red]Quantity must be greater than 0.[/red]")
        return
    db.update_inventory_quantity(item_id, quantity)
    console.print(f"[green]Updated id={item_id} quantity to {quantity}.[/green]")


# ── web ───────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--host", default=None, help="Host to bind to. Default: from config.yaml.")
@click.option("--port", default=None, type=int, help="Port to listen on. Default: from config.yaml.")
@click.option("--debug", is_flag=True, default=False, help="Enable Flask debug mode.")
def web(host, port, debug):
    """Start the web dashboard."""
    cfg = load_config()
    web_cfg = cfg.get("web", {})

    host = host or web_cfg.get("host", "127.0.0.1")
    port = port or web_cfg.get("port", 5000)

    console.print(
        f"Starting web dashboard at [bold cyan]http://{host}:{port}[/bold cyan] — "
        f"press Ctrl+C to stop."
    )

    from web.app import start_web
    start_web(host=host, port=port, debug=debug)


# ── helpers ──────────────────────────────────────────────────────────────────

def _isk(value: float | None) -> str:
    """Format a number as ISK with thousand separators."""
    if value is None:
        return "[dim]—[/dim]"
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.2f}"
