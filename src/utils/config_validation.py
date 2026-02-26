"""
Configuration validation and utilities.
Validates config.yaml structure and provides helper functions.
"""
from typing import Dict, Tuple, List, Any


def validate_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate configuration structure and values.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Required top-level sections
    required_sections = ['fees', 'filters', 'regions']
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required section: {section}")
    
    # Validate fees
    if 'fees' in config:
        fees = config['fees']
        fee_fields = ['broker_fee_buy', 'broker_fee_sell', 'sales_tax']
        for field in fee_fields:
            if field not in fees:
                errors.append(f"Missing fee: {field}")
            elif not isinstance(fees[field], (int, float)) or fees[field] < 0:
                errors.append(f"Invalid fee value for {field}: must be >= 0")
    
    # Validate filters
    if 'filters' in config:
        filters = config['filters']
        if 'min_profit' in filters and filters['min_profit'] < 0:
            errors.append("min_profit must be >= 0")
        if 'min_roi_percent' in filters and filters['min_roi_percent'] < 0:
            errors.append("min_roi_percent must be >= 0")
        if 'max_age_days' in filters and filters['max_age_days'] <= 0:
            errors.append("max_age_days must be > 0")
    
    # Validate regions
    if 'regions' in config:
        regions = config['regions']
        if not isinstance(regions, dict):
            errors.append("regions must be a dictionary")
        elif len(regions) == 0:
            errors.append("At least one region must be configured")
    
    # Validate character section (if present)
    if 'character' in config:
        char = config['character']
        if char.get('enabled'):
            if not char.get('esi_client_id'):
                errors.append("ESI Client ID required when character tracking is enabled")
    
    # Validate Twitch section (if present)
    if 'twitch' in config:
        twitch = config['twitch']
        if twitch.get('enabled'):
            required = ['client_id', 'client_secret', 'user_id']
            for field in required:
                if not twitch.get(field):
                    errors.append(f"Twitch {field} required when Twitch integration is enabled")
    
    # Validate wormholes section (if present)
    if 'wormholes' in config:
        wh = config['wormholes']
        if 'auto_track_interval_seconds' in wh:
            if not isinstance(wh['auto_track_interval_seconds'], int) or wh['auto_track_interval_seconds'] < 60:
                errors.append("auto_track_interval_seconds must be >= 60")
    
    return len(errors) == 0, errors


def get_enabled_features(config: Dict[str, Any]) -> Dict[str, bool]:
    """
    Get dictionary of enabled features from config.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary of feature names to enabled status
    """
    return {
        'market_arbitrage': True,  # Always enabled
        'character_tracking': config.get('character', {}).get('enabled', False),
        'wormhole_mapping': config.get('wormholes', {}).get('enabled', False),
        'twitch_integration': config.get('twitch', {}).get('enabled', False),
        'auto_backup': config.get('backup', {}).get('enabled', True),
        'health_monitoring': True,  # Always enabled
    }


def get_database_paths(config: Dict[str, Any]) -> Dict[str, str]:
    """
    Get paths to all databases from config.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary of database names to file paths
    """
    base_db = config.get('database', {}).get('path', 'data/eve_arbitrage.db')
    wh_db = config.get('wormholes', {}).get('database_path', 'data/wormholes.db')
    
    return {
        'arbitrage': base_db,
        'wormholes': wh_db,
    }
