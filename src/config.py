"""Configuration loader — reads config.yaml from the project root."""
import os
import yaml

_CONFIG = None

def load_config() -> dict:
    global _CONFIG
    if _CONFIG is not None:
        return _CONFIG

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(root, "config.yaml")

    with open(config_path, "r") as f:
        _CONFIG = yaml.safe_load(f)
    return _CONFIG


def get_region_map(config: dict) -> dict[str, int]:
    """Return {name: id} mapping from config regions list."""
    return {r["name"]: r["id"] for r in config["regions"]}
