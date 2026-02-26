"""
Scanner: orchestrates full market scans across all configured region pairs.
Uses Rich console for live progress output in CLI mode.
"""
from __future__ import annotations

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn

from config import load_config, get_region_map
from engine.fees import FeeConfig
from engine.arbitrage import find_opportunities, ArbitrageOpportunity
from models import database as db

console = Console()


def run_scan(
    region_pairs: list[tuple[str, str]] | None = None,
    silent: bool = False,
) -> list[ArbitrageOpportunity]:
    """
    Run a full arbitrage scan.

    Args:
        region_pairs: List of (source_name, dest_name) tuples.
                      If None, uses all pairs from config.yaml.
        silent:       Suppress Rich console output (for web-triggered scans).

    Returns:
        All opportunities found, sorted by total_profit_potential desc.
    """
    cfg = load_config()
    region_map = get_region_map(cfg)
    fee_config = FeeConfig.from_config(cfg)
    filters = cfg.get("filters", {})
    ttl = cfg.get("scan", {}).get("cache_ttl_minutes", 5)

    # Resolve region pairs
    if region_pairs is None:
        pairs_cfg = cfg.get("scan", {}).get("pairs", [])
        region_pairs = [(p[0], p[1]) for p in pairs_cfg]
        # Also add reverse direction
        all_pairs = []
        for a, b in region_pairs:
            all_pairs.append((a, b))
            all_pairs.append((b, a))
        region_pairs = all_pairs

    # Validate region names
    valid_pairs = []
    for src, dst in region_pairs:
        if src not in region_map or dst not in region_map:
            if not silent:
                console.print(f"[yellow]Warning: Unknown region in pair ({src}, {dst}) — skipping[/yellow]")
            continue
        valid_pairs.append((src, dst))

    all_results: list[ArbitrageOpportunity] = []

    if not silent:
        console.rule("[bold cyan]EVE Arbitrage Scanner[/bold cyan]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        console=console,
        disable=silent,
        transient=True,
    ) as progress:
        task = progress.add_task("Scanning pairs...", total=len(valid_pairs))

        for src_name, dst_name in valid_pairs:
            src_id = region_map[src_name]
            dst_id = region_map[dst_name]

            progress.update(
                task,
                description=f"[cyan]{src_name}[/cyan] → [green]{dst_name}[/green]"
            )

            def cb(msg: str):
                if not silent:
                    console.log(f"  {msg}")

            try:
                results = find_opportunities(
                    source_region_name=src_name,
                    source_region_id=src_id,
                    dest_region_name=dst_name,
                    dest_region_id=dst_id,
                    fee_config=fee_config,
                    filters=filters,
                    ttl_minutes=ttl,
                    progress_cb=cb,
                )
                all_results.extend(results)

                if not silent:
                    console.log(
                        f"  [green]✓[/green] {src_name}→{dst_name}: "
                        f"[bold]{len(results)}[/bold] opportunities"
                    )
            except Exception as exc:
                if not silent:
                    console.log(f"  [red]✗[/red] {src_name}→{dst_name}: {exc}")

            progress.advance(task)

    # Sort globally by total profit potential
    all_results.sort(key=lambda o: -o.total_profit_potential)

    # Persist to database
    db.save_results([o.to_dict() for o in all_results])

    if not silent:
        console.rule(f"[bold green]Scan complete — {len(all_results)} opportunities found[/bold green]")

    return all_results
