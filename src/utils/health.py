"""
Health check and system monitoring.
"""
from __future__ import annotations

import time
import psutil
import sys
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class SystemHealth:
    status: str  # "healthy", "degraded", "unhealthy"
    uptime_seconds: float
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_percent: float
    database_ok: bool
    esi_api_ok: bool
    character_tracking_ok: bool
    wormhole_tracking_ok: bool
    twitch_integration_ok: bool
    errors: list[str]


_start_time = time.time()


def get_system_health() -> SystemHealth:
    """Get current system health status."""
    errors = []
    
    # System metrics
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
    except Exception as e:
        errors.append(f"Failed to get system metrics: {e}")
        cpu = 0
        memory = type('obj', (object,), {'percent': 0, 'used': 0})()
        disk = type('obj', (object,), {'percent': 0})()
    
    # Database check
    db_ok = True
    try:
        from models import database as db
        db.init_db()
    except Exception as e:
        db_ok = False
        errors.append(f"Database error: {e}")
    
    # ESI API check
    esi_ok = True
    try:
        from api import esi
        # Quick check - just verify we can import and have session
        if not hasattr(esi, 'SESSION'):
            esi_ok = False
            errors.append("ESI session not initialized")
    except Exception as e:
        esi_ok = False
        errors.append(f"ESI API error: {e}")
    
    # Character tracking check
    char_ok = True
    try:
        from tracker import character as char_module
        # Just check if module loads
    except Exception as e:
        char_ok = False
        errors.append(f"Character tracking error: {e}")
    
    # Wormhole tracking check
    wh_ok = True
    try:
        from tracker import wormholes as wh_module
    except Exception as e:
        wh_ok = False
        errors.append(f"Wormhole tracking error: {e}")
    
    # Twitch integration check
    twitch_ok = True
    try:
        from integrations import twitch as twitch_module
    except Exception as e:
        twitch_ok = False
        errors.append(f"Twitch integration error: {e}")
    
    # Determine overall status
    if errors:
        if len(errors) > 3:
            status = "unhealthy"
        else:
            status = "degraded"
    elif cpu > 90 or memory.percent > 90 or disk.percent > 90:
        status = "degraded"
    else:
        status = "healthy"
    
    return SystemHealth(
        status=status,
        uptime_seconds=time.time() - _start_time,
        cpu_percent=cpu,
        memory_percent=memory.percent,
        memory_mb=memory.used / (1024 * 1024),
        disk_percent=disk.percent,
        database_ok=db_ok,
        esi_api_ok=esi_ok,
        character_tracking_ok=char_ok,
        wormhole_tracking_ok=wh_ok,
        twitch_integration_ok=twitch_ok,
        errors=errors,
    )


def format_uptime(seconds: float) -> str:
    """Format uptime in human-readable format."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.0f}m"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"
    else:
        days = int(seconds / 86400)
        hours = int((seconds % 86400) / 3600)
        return f"{days}d {hours}h"
