#!/usr/bin/env python3
"""
Integration test script for EVE Arbitrage Bot v2.0.0
Tests all major components and integrations.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from config import load_config
from utils.logging import setup_logging
from utils.health import get_system_health
from utils.security import validate_config, InputValidator
from version import __version__, get_version_string

# Test results tracker
tests_passed = 0
tests_failed = 0
failures = []


def test(name: str, func):
    """Run a test and track results."""
    global tests_passed, tests_failed, failures
    try:
        print(f"Testing {name}...", end=" ")
        func()
        print("✓ PASS")
        tests_passed += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
        tests_failed += 1
        failures.append((name, str(e)))


def test_config():
    """Test configuration loading and validation."""
    config = load_config()
    assert config is not None, "Config should load"
    assert 'fees' in config, "Config should have fees section"
    assert 'regions' in config, "Config should have regions section"
    
    is_valid, errors = validate_config(config)
    if not is_valid:
        raise AssertionError(f"Config validation failed: {errors}")


def test_logging():
    """Test logging system."""
    logger = setup_logging("test")
    assert logger is not None, "Logger should be created"
    logger.info("Test log message")
    logger.warning("Test warning")


def test_health_monitoring():
    """Test health monitoring system."""
    health = get_system_health()
    assert health is not None, "Health check should return data"
    assert health.status in ["healthy", "degraded", "unhealthy"], "Health status should be valid"
    assert health.cpu_percent >= 0, "CPU should be non-negative"
    assert health.memory_percent >= 0, "Memory should be non-negative"


def test_input_validation():
    """Test input validation."""
    validator = InputValidator()
    
    # Test string validation
    assert validator.validate_string("test", min_length=1, max_length=100), "Valid string should pass"
    assert not validator.validate_string("", min_length=1), "Empty string should fail min length"
    assert not validator.validate_string("a" * 1000, max_length=100), "Long string should fail max length"
    
    # Test integer validation
    assert validator.validate_integer(50, min_val=0, max_val=100), "Valid int should pass"
    assert not validator.validate_integer(-1, min_val=0), "Negative int should fail min"
    assert not validator.validate_integer(200, max_val=100), "Large int should fail max"
    
    # Test system ID validation
    assert validator.validate_system_id(30000142), "Valid system ID should pass (Jita)"
    assert not validator.validate_system_id(-1), "Negative system ID should fail"


def test_database():
    """Test database operations."""
    from models.database import Database
    config = load_config()
    db = Database(config)
    
    # Test basic operations
    assert db is not None, "Database should be created"
    
    # Test inventory operations
    row_id = db.add_inventory(
        type_id=34,
        item_name="Tritanium",
        quantity=1000,
        cost_basis_isk=5.0,
        station="Test Station"
    )
    assert row_id > 0, "Should return row ID"
    
    inventory = db.get_inventory()
    assert len(inventory) > 0, "Should have inventory items"
    
    # Test update
    assert db.update_inventory_quantity(row_id, 2000), "Should update quantity"
    
    # Test delete
    assert db.delete_inventory(row_id), "Should delete item"


def test_esi_api():
    """Test ESI API connection."""
    from api.esi import ESI
    config = load_config()
    esi = ESI(config)
    
    # Test basic search
    results = esi.search_type_ids("Tritanium")
    assert len(results) > 0, "Should find Tritanium"
    assert results[0]["name"] == "Tritanium", "First result should be exact match"
    
    # Test system info caching
    system_info = esi.get_system_info(30000142)  # Jita
    assert system_info is not None, "Should get Jita info"
    assert "name" in system_info, "System info should have name"


def test_character_tracking():
    """Test character tracking (if configured)."""
    config = load_config()
    if not config.get('character', {}).get('enabled'):
        print("Character tracking not enabled, skipping")
        return
    
    from tracker.character import CharacterTracker
    tracker = CharacterTracker(config)
    assert tracker is not None, "Tracker should be created"
    
    # Note: Can't test actual API calls without OAuth token


def test_wormhole_tracking():
    """Test wormhole tracking system."""
    config = load_config()
    if not config.get('wormholes', {}).get('enabled', True):
        print("Wormhole tracking not enabled, skipping")
        return
    
    from tracker.wormholes import WormholeTracker
    tracker = WormholeTracker(config)
    assert tracker is not None, "Tracker should be created"
    
    # Test adding a connection
    tracker.add_connection(
        source_system_id=31000005,  # J-space system
        dest_system_id=30000142,    # Jita
        wh_type="C248",
        mass_remaining="Stable",
        time_remaining="Fresh"
    )
    
    # Test getting connections
    connections = tracker.get_active_connections()
    assert isinstance(connections, list), "Should return list of connections"


def test_twitch_integration():
    """Test Twitch integration (if configured)."""
    config = load_config()
    if not config.get('twitch', {}).get('enabled'):
        print("Twitch integration not enabled, skipping")
        return
    
    from integrations.twitch import TwitchIntegration, TwitchConfig
    twitch_cfg = config['twitch']
    
    integration = TwitchIntegration(TwitchConfig(
        client_id=twitch_cfg['client_id'],
        client_secret=twitch_cfg['client_secret'],
        broadcaster_id=twitch_cfg['broadcaster_id'],
    ))
    assert integration is not None, "Integration should be created"
    
    # Note: Can't test actual API calls without valid tokens


def test_backup_system():
    """Test backup system."""
    from utils.backup import get_backup_manager
    
    manager = get_backup_manager()
    assert manager is not None, "Backup manager should be created"
    
    # Test backup operations
    manager.backup_databases()
    manager.backup_config()
    
    backups = manager.list_backups()
    assert len(backups) > 0, "Should have at least one backup"


def test_web_app():
    """Test web application initialization."""
    from web.app import app
    
    assert app is not None, "Flask app should be created"
    
    with app.test_client() as client:
        # Test health endpoint
        response = client.get('/health')
        assert response.status_code in [200, 503], "Health endpoint should respond"
        data = response.get_json()
        assert 'status' in data, "Health response should have status"
        
        # Test version endpoint
        response = client.get('/version')
        assert response.status_code == 200, "Version endpoint should work"
        data = response.get_json()
        assert 'version' in data, "Version response should have version"
        
        # Test index page
        response = client.get('/')
        assert response.status_code == 200, "Index page should load"


def main():
    """Run all integration tests."""
    print("=" * 70)
    print(f"EVE Arbitrage Bot v{__version__} - Integration Tests")
    print("=" * 70)
    print()
    
    # Core tests (always run)
    test("Configuration", test_config)
    test("Logging System", test_logging)
    test("Health Monitoring", test_health_monitoring)
    test("Input Validation", test_input_validation)
    test("Database Operations", test_database)
    test("ESI API", test_esi_api)
    
    # Optional features (run if enabled)
    test("Character Tracking", test_character_tracking)
    test("Wormhole Tracking", test_wormhole_tracking)
    test("Twitch Integration", test_twitch_integration)
    
    # System tests
    test("Backup System", test_backup_system)
    test("Web Application", test_web_app)
    
    # Print results
    print()
    print("=" * 70)
    print(f"Test Results: {tests_passed} passed, {tests_failed} failed")
    print("=" * 70)
    
    if tests_failed > 0:
        print("\nFailures:")
        for name, error in failures:
            print(f"  ✗ {name}: {error}")
        sys.exit(1)
    else:
        print("\n✓ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
