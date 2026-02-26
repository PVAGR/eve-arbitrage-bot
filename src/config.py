"""Configuration loader — reads config.yaml from the project root."""
import os
import sys
import yaml

_CONFIG = None


def _base_dir() -> str:
    """
    Return the directory that contains config.yaml.
    - When running as a PyInstaller .exe: same folder as the executable.
    - When running as a script: project root (parent of src/).
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config() -> dict:
    global _CONFIG
    if _CONFIG is not None:
        return _CONFIG

    config_path = os.path.join(_base_dir(), "config.yaml")
    with open(config_path, "r") as f:
        _CONFIG = yaml.safe_load(f)
    return _CONFIG


def get_region_map(config: dict) -> dict[str, int]:
    """Return {name: id} mapping from config regions list."""
    return {r["name"]: r["id"] for r in config["regions"]}
