"""
Security utilities and validation helpers.
"""
from __future__ import annotations

import re
import time
import hashlib
import secrets
from typing import Optional
from functools import wraps
from collections import defaultdict
import threading

# Rate limiting
_rate_limits = defaultdict(lambda: {"count": 0, "reset_at": 0})
_rate_lock = threading.Lock()


def rate_limit(max_calls: int, period_seconds: int):
    """
    Decorator to rate limit function calls per client.
    Usage: @rate_limit(max_calls=10, period_seconds=60)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get client identifier (use IP from Flask request if available)
            try:
                from flask import request
                client_id = request.remote_addr
            except:
                client_id = "default"
            
            key = f"{func.__name__}:{client_id}"
            
            with _rate_lock:
                now = time.time()
                if _rate_limits[key]["reset_at"] < now:
                    _rate_limits[key] = {"count": 0, "reset_at": now + period_seconds}
                
                _rate_limits[key]["count"] += 1
                
                if _rate_limits[key]["count"] > max_calls:
                    from flask import jsonify
                    return jsonify({
                        "error": "Rate limit exceeded",
                        "retry_after": int(_rate_limits[key]["reset_at"] - now)
                    }), 429
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def sanitize_system_id(system_id: any) -> Optional[int]:
    """Validate and sanitize system ID."""
    try:
        sid = int(system_id)
        # EVE system IDs are typically 30000000-32000000 range
        if 30000000 <= sid <= 32000000:
            return sid
    except (ValueError, TypeError):
        pass
    return None


def sanitize_type_id(type_id: any) -> Optional[int]:
    """Validate and sanitize type ID (item ID)."""
    try:
        tid = int(type_id)
        # EVE type IDs are positive integers
        if 0 < tid < 100000000:
            return tid
    except (ValueError, TypeError):
        pass
    return None


def sanitize_string(text: str, max_length: int = 500) -> str:
    """Sanitize user input string."""
    if not isinstance(text, str):
        return ""
    # Remove any null bytes and control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    # Limit length
    return text[:max_length].strip()


def validate_isk_amount(amount: any) -> Optional[float]:
    """Validate ISK amount."""
    try:
        isk = float(amount)
        # ISK amounts should be reasonable
        if 0 <= isk < 1e15:  # Max ~1 quadrillion ISK
            return isk
    except (ValueError, TypeError):
        pass
    return None


def validate_quantity(qty: any) -> Optional[int]:
    """Validate item quantity."""
    try:
        q = int(qty)
        if 0 < q < 1e12:  # Reasonable max quantity
            return q
    except (ValueError, TypeError):
        pass
    return None


def generate_secure_token() -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash a token for secure storage comparison."""
    return hashlib.sha256(token.encode()).hexdigest()


def validate_config(config: dict) -> tuple[bool, list[str]]:
    """
    Validate configuration file.
    Returns (is_valid, error_messages).
    """
    errors = []
    
    # Check fees
    if "fees" in config:
        fees = config["fees"]
        if not (0 <= fees.get("broker_fee_buy", 0) <= 1):
            errors.append("broker_fee_buy must be between 0 and 1")
        if not (0 <= fees.get("broker_fee_sell", 0) <= 1):
            errors.append("broker_fee_sell must be between 0 and 1")
        if not (0 <= fees.get("sales_tax", 0) <= 1):
            errors.append("sales_tax must be between 0 and 1")
        if not (0 <= fees.get("hauling_isk_per_m3", 0) <= 100000):
            errors.append("hauling_isk_per_m3 seems unreasonably high")
    
    # Check filters
    if "filters" in config:
        filters = config["filters"]
        if filters.get("min_profit_margin_pct", 0) < 0:
            errors.append("min_profit_margin_pct must be >= 0")
        if filters.get("min_net_isk_profit", 0) < 0:
            errors.append("min_net_isk_profit must be >= 0")
    
    # Check regions
    if "regions" in config:
        if not isinstance(config["regions"], list) or not config["regions"]:
            errors.append("regions must be a non-empty list")
    
    # Check web settings
    if "web" in config:
        web = config["web"]
        port = web.get("port", 5000)
        if not (1024 <= port <= 65535):
            errors.append("web.port must be between 1024 and 65535")
    
    return (len(errors) == 0, errors)


class InputValidator:
    """Centralized input validation."""
    
    @staticmethod
    def system_id(value: any) -> int:
        """Validate system ID or raise ValueError."""
        result = sanitize_system_id(value)
        if result is None:
            raise ValueError(f"Invalid system ID: {value}")
        return result
    
    @staticmethod
    def validate_system_id(value: any, **kwargs) -> bool:
        """Validate system ID returns boolean."""
        return sanitize_system_id(value) is not None
    
    @staticmethod
    def type_id(value: any) -> int:
        """Validate type ID or raise ValueError."""
        result = sanitize_type_id(value)
        if result is None:
            raise ValueError(f"Invalid type ID: {value}")
        return result
    
    @staticmethod
    def isk_amount(value: any) -> float:
        """Validate ISK amount or raise ValueError."""
        result = validate_isk_amount(value)
        if result is None:
            raise ValueError(f"Invalid ISK amount: {value}")
        return result
    
    @staticmethod
    def quantity(value: any) -> int:
        """Validate quantity or raise ValueError."""
        result = validate_quantity(value)
        if result is None:
            raise ValueError(f"Invalid quantity: {value}")
        return result
    
    @staticmethod
    def string(value: any, max_length: int = 500) -> str:
        """Sanitize string input."""
        return sanitize_string(str(value), max_length)
    
    @staticmethod
    def validate_string(value: str, min_length: int = 0, max_length: int = 500) -> bool:
        """Validate string length constraints."""
        if not isinstance(value, str):
            return False
        return min_length <= len(value) <= max_length
    
    @staticmethod
    def validate_integer(value: any, min_val: int = None, max_val: int = None) -> bool:
        """Validate integer value and optional bounds."""
        try:
            num = int(value)
            if min_val is not None and num < min_val:
                return False
            if max_val is not None and num > max_val:
                return False
            return True
        except (ValueError, TypeError):
            return False


def require_feature(feature_name: str, feature_instance):
    """
    Decorator to require a feature to be enabled.
    Returns 503 if feature is not available.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not feature_instance:
                from flask import jsonify
                return jsonify({
                    "error": f"{feature_name} not configured",
                    "message": f"Please enable {feature_name} in config.yaml"
                }), 503
            return func(*args, **kwargs)
        return wrapper
    return decorator
