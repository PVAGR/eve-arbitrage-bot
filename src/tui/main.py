"""
Interactive TUI for EVE Arbitrage Bot.
A menu-driven terminal interface — no command-line arguments needed.
"""
from __future__ import annotations

import os
import sys
import time
import threading
import webbrowser

from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

# Allow running standalone or via run.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import database as db
from engine import scanner
from api import esi
from config import load_config, get_region_map

console = Console()

# ── Helpers ───────────────────────────────────────────────────────────────────

def _clear():
    console.clear()


def _isk(value: float | None) -> str:
    if value is None:
        return "—"
    if value >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:.2f}T"
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.2f}"


def _pause(msg: str = "Press ENTER to continue"):
    console.print()
    Prompt.ask(f"  [dim]{msg}[/dim]", default="", show_default=False)


def _header(subtitle: str = ""):
    _clear()
    title = "◆  EVE  ARBITRAGE  BOT  ◆"
    sub = subtitle or "Market Intelligence System"
    console.print(Panel(
        Align.center(f"[bold cyan]{title}[/bold cyan]\n[dim]{sub}[/dim]"),
        border_style="cyan",
        padding=(0, 6),
    ))


def _status_line():
    """Print a one-line status bar below the header."""
    last = db.get_last_scan_time()
    results = db.get_results(10000)
    inv = db.get_inventory()

    if last:
        ts = last[:16].replace("T", " ")
        line = (
            f"[dim]Scan:[/dim] [cyan]{ts}[/cyan]  "
            f"[dim]|[/dim]  [dim]Opps:[/dim] [green]{len(results)}[/green]  "
            f"[dim]|[/dim]  [dim]Inventory:[/dim] [yellow]{len(inv)}[/yellow] items"
        )
    else:
        line = "[dim]No scan data — choose [bold]Run Scan[/bold] to get started[/dim]"
    console.print(Align.center(line))
    console.print()


# ── Screens ───────────────────────────────────────────────────────────────────

def main_menu():
    while True:
        _header()
        _status_line()

        console.print(Panel(
            "\n".join([
                "  [bold cyan]1[/bold cyan]   Run Market Scan",
                "  [bold cyan]2[/bold cyan]   View Opportunities",
                "  [bold cyan]3[/bold cyan]   Manage Inventory",
                "  [bold cyan]4[/bold cyan]   Price Lookup",
                "  [bold cyan]5[/bold cyan]   Web Dashboard",
                "",
                "  [bold red]Q[/bold red]   Quit",
            ]),
            title="[bold white]MAIN MENU[/bold white]",
            border_style="dim white",
            padding=(1, 4),
        ))

        choice = Prompt.ask(
            "[bold cyan]Select[/bold cyan]",
            choices=["1", "2", "3", "4", "5", "q", "Q"],
            show_choices=False,
        ).lower()

        if choice == "1":
            _screen_scan()
        elif choice == "2":
            _screen_opportunities()
        elif choice == "3":
            _screen_inventory()
        elif choice == "4":
            _screen_lookup()
        elif choice == "5":
            _screen_web()
        elif choice == "q":
            console.print()
            console.print(Align.center("[dim italic]Fly safe, capsuleer.[/dim italic]"))
            console.print()
            sys.exit(0)


# ── Scan ──────────────────────────────────────────────────────────────────────

def _screen_scan():
    _header("Run Market Scan")
    console.print()

    cfg = load_config()
    pairs = cfg.get("scan", {}).get("pairs", [])
    console.print(f"  [dim]Configured pairs: {len(pairs)} ({len(pairs) * 2} directions)[/dim]\n")

    custom = Prompt.ask(
        "  Scan [cyan]A[/cyan]ll pairs or enter [cyan]SOURCE DEST[/cyan] for one route",
        default="A",
    ).strip()

    console.print()
    if custom.upper() == "A":
        region_pairs = None
    else:
        parts = custom.split()
        if len(parts) != 2:
            console.print("  [red]Expected two region names, e.g. Jita Amarr[/red]")
            time.sleep(1.5)
            return
        region_pairs = [tuple(parts)]

    results = scanner.run_scan(region_pairs=region_pairs, silent=False)

    console.print()
    if results:
        console.print(f"  [bold green]✓ {len(results)} opportunities found.[/bold green] Top 5:\n")
        _render_opps(results[:5])
    else:
        console.print("  [yellow]No profitable opportunities found with current filter settings.[/yellow]")

    _pause()


# ── Opportunities ─────────────────────────────────────────────────────────────

def _screen_opportunities():
    page_size = 40

    while True:
        _header("Opportunities")
        rows = db.get_results(limit=500)

        if not rows:
            console.print("\n  [yellow]No results yet — run a scan first.[/yellow]")
            _pause("Press ENTER to return")
            return

        # Filter
        name_filter = ""
        pair_filter = ""

        _render_opps(rows[:page_size], name_filter=name_filter)
        console.print(
            f"\n  [dim]Showing {min(page_size, len(rows))} of {len(rows)}[/dim]  "
            "  [cyan]F[/cyan] filter   [cyan]A[/cyan] all   [cyan]B[/cyan] back"
        )

        choice = Prompt.ask("  [bold cyan]>[/bold cyan]", default="b").strip().lower()

        if choice == "f":
            name_filter = Prompt.ask("  Filter by item name").strip().lower()
            filtered = [r for r in rows if name_filter in r["item_name"].lower()]
            _header(f"Opportunities — filter: '{name_filter}'")
            console.print(f"\n  [dim]{len(filtered)} matches[/dim]\n")
            _render_opps(filtered[:page_size])
            _pause()

        elif choice == "a":
            _header("All Opportunities")
            console.print()
            _render_opps(rows)
            _pause()

        else:
            return


def _render_opps(rows: list, name_filter: str = ""):
    if not rows:
        console.print("  [dim]No results.[/dim]")
        return

    table = Table(header_style="bold cyan", show_lines=False, box=box.SIMPLE)
    table.add_column("#",       style="dim",  width=4,  justify="right")
    table.add_column("Item",                  min_width=20)
    table.add_column("Route",                 min_width=16)
    table.add_column("Buy",                   justify="right")
    table.add_column("Sell",                  justify="right")
    table.add_column("Margin",                justify="right")
    table.add_column("Vol",                   justify="right")
    table.add_column("Total ISK", style="bold green", justify="right")

    for i, r in enumerate(rows, 1):
        pct = r["profit_margin_pct"]
        mc = "green" if pct >= 25 else ("yellow" if pct >= 15 else "white")
        table.add_row(
            str(i),
            r["item_name"],
            f"{r['buy_region']} → {r['sell_region']}",
            _isk(r["buy_price"]),
            _isk(r["sell_price"]),
            Text(f"{pct:.1f}%", style=mc),
            str(r["volume_available"]),
            _isk(r["total_profit_potential"]),
        )

    console.print(table)


# ── Inventory ─────────────────────────────────────────────────────────────────

def _screen_inventory():
    while True:
        _header("Inventory")
        items = db.get_inventory()
        console.print()

        if items:
            table = Table(header_style="bold cyan", show_lines=False, box=box.SIMPLE)
            table.add_column("ID",        style="dim", width=5,  justify="right")
            table.add_column("Item",                   min_width=20)
            table.add_column("Qty",                    justify="right")
            table.add_column("Cost/unit",              justify="right")
            table.add_column("Total",                  justify="right")
            table.add_column("Station",  style="dim")

            total = 0.0
            for item in items:
                cost = item["quantity"] * item["cost_basis_isk"]
                total += cost
                table.add_row(
                    str(item["id"]),
                    item["item_name"],
                    f"{item['quantity']:,}",
                    _isk(item["cost_basis_isk"]),
                    _isk(cost),
                    item.get("station") or "—",
                )

            console.print(table)
            console.print(f"\n  Total invested: [bold green]{_isk(total)} ISK[/bold green]")
        else:
            console.print("  [dim]Inventory is empty.[/dim]")

        console.print()
        console.print(
            "  [cyan]A[/cyan] add   [cyan]R[/cyan] remove   "
            "[cyan]U[/cyan] update qty   [cyan]B[/cyan] back"
        )
        choice = Prompt.ask("  [bold cyan]>[/bold cyan]", default="b").strip().lower()

        if choice == "a":
            _inv_add()
        elif choice == "r":
            _inv_remove()
        elif choice == "u":
            _inv_update()
        else:
            return


def _inv_add():
    console.print()
    name = Prompt.ask("  Item name").strip()
    if not name:
        return

    console.print(f"  [dim]Looking up '{name}'…[/dim]")
    matches = esi.search_type_ids(name)
    if not matches:
        console.print("  [red]Not found in EVE universe.[/red]")
        time.sleep(1.5)
        return

    hit = matches[0]
    console.print(f"  → [cyan]{hit['name']}[/cyan] (type_id={hit['type_id']})")

    try:
        qty  = int(Prompt.ask("  Quantity"))
        cost = float(Prompt.ask("  Cost per unit (ISK)"))
        stn  = Prompt.ask("  Station [dim](optional, ENTER to skip)[/dim]", default="")
    except (ValueError, KeyboardInterrupt):
        return

    if qty <= 0 or cost < 0:
        console.print("  [red]Invalid quantity or cost.[/red]")
        time.sleep(1.5)
        return

    row_id = db.add_inventory(
        type_id=hit["type_id"],
        item_name=hit["name"],
        quantity=qty,
        cost_basis_isk=cost,
        station=stn,
    )
    console.print(f"  [green]Added {hit['name']} ×{qty:,} @ {_isk(cost)}/unit (id={row_id})[/green]")
    time.sleep(1.2)


def _inv_remove():
    console.print()
    try:
        row_id = int(Prompt.ask("  Item ID to remove"))
    except (ValueError, KeyboardInterrupt):
        return

    deleted = db.delete_inventory(row_id)
    if deleted:
        console.print(f"  [green]Removed id={row_id}.[/green]")
    else:
        console.print(f"  [red]No item with id={row_id}.[/red]")
    time.sleep(1.2)


def _inv_update():
    console.print()
    try:
        row_id = int(Prompt.ask("  Item ID to update"))
        qty    = int(Prompt.ask("  New quantity"))
    except (ValueError, KeyboardInterrupt):
        return

    if qty <= 0:
        console.print("  [red]Quantity must be > 0.[/red]")
        time.sleep(1.2)
        return

    db.update_inventory_quantity(row_id, qty)
    console.print(f"  [green]Updated id={row_id} → {qty:,} units.[/green]")
    time.sleep(1.2)


# ── Price Lookup ──────────────────────────────────────────────────────────────

def _screen_lookup():
    while True:
        _header("Price Lookup")
        console.print()

        query = Prompt.ask(
            "  Item name  [dim](B to go back)[/dim]"
        ).strip()

        if query.lower() == "b" or not query:
            return

        console.print(f"\n  [dim]Searching for '{query}'…[/dim]")
        matches = esi.search_type_ids(query)
        if not matches:
            console.print(f"  [red]No items found for '{query}'.[/red]")
            time.sleep(1.5)
            continue

        hit = matches[0]
        type_id  = hit["type_id"]
        name     = hit["name"]
        info     = esi.get_item_info(type_id)

        console.print(
            f"\n  [bold cyan]{name}[/bold cyan]  "
            f"[dim]type_id={type_id}  volume={info['volume']} m³[/dim]\n"
        )

        cfg        = load_config()
        region_map = get_region_map(cfg)

        table = Table(header_style="bold cyan", show_lines=False, box=box.SIMPLE)
        table.add_column("Hub",          min_width=12)
        table.add_column("Lowest Sell",  justify="right")
        table.add_column("Sell Vol",     justify="right")
        table.add_column("Highest Buy",  justify="right")
        table.add_column("Buy Vol",      justify="right")

        for region_name, region_id in region_map.items():
            try:
                sells     = esi.get_sell_orders(region_id, ttl_minutes=10)
                buys      = esi.get_buy_orders(region_id, ttl_minutes=10)
                best_sell = esi.best_sell_price(sells.get(type_id, []))
                best_buy  = esi.best_buy_price(buys.get(type_id, []))
            except Exception as exc:
                table.add_row(region_name, f"[red]{exc}[/red]", "", "", "")
                continue

            table.add_row(
                region_name,
                _isk(best_sell[0]) if best_sell else "[dim]—[/dim]",
                str(best_sell[1]) if best_sell else "[dim]—[/dim]",
                _isk(best_buy[0]) if best_buy else "[dim]—[/dim]",
                str(best_buy[1]) if best_buy else "[dim]—[/dim]",
            )

        console.print(table)
        _pause()


# ── Web Dashboard ─────────────────────────────────────────────────────────────

def _screen_web():
    _header("Web Dashboard")
    console.print()

    cfg     = load_config()
    web_cfg = cfg.get("web", {})
    host    = web_cfg.get("host", "127.0.0.1")
    port    = web_cfg.get("port", 5000)
    url     = f"http://{host}:{port}"

    console.print(f"  Starting server at [bold cyan]{url}[/bold cyan]")
    console.print("  [dim]Opening browser… press Ctrl+C to stop and return to menu.[/dim]\n")

    from web.app import start_web

    def _open_browser():
        time.sleep(1.2)
        webbrowser.open(url)

    threading.Thread(target=_open_browser, daemon=True).start()

    try:
        start_web(host=host, port=port, debug=False)
    except KeyboardInterrupt:
        pass

    console.print("\n  [dim]Server stopped.[/dim]")
    time.sleep(0.8)


# ── Entry point ───────────────────────────────────────────────────────────────

def run_tui():
    db.init_db()
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print("\n\n  [dim italic]Fly safe, capsuleer.[/dim italic]\n")
        sys.exit(0)
