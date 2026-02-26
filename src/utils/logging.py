"""
Logging and monitoring utilities.
"""
from __future__ import annotations

import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Create logs directory
LOGS_DIR = Path("data/logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)


class ColoredFormatter(logging.Formatter):
    """Colored console output for better readability."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(name: str = "eve-tracker", level: str = "INFO") -> logging.Logger:
    """
    Setup application logging with both file and console output.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler (detailed logs)
    log_file = LOGS_DIR / f"eve-tracker-{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def log_api_call(endpoint: str, duration_ms: float, status_code: int = 200):
    """Log API call metrics."""
    logger = logging.getLogger("eve-tracker.api")
    level = logging.INFO if status_code < 400 else logging.WARNING
    logger.log(level, f"API {endpoint} | {duration_ms:.0f}ms | {status_code}")


def log_error(error: Exception, context: str = ""):
    """Log error with context."""
    logger = logging.getLogger("eve-tracker.error")
    if context:
        logger.error(f"{context}: {type(error).__name__}: {error}", exc_info=True)
    else:
        logger.error(f"{type(error).__name__}: {error}", exc_info=True)


def log_security_event(event_type: str, details: str):
    """Log security-related events."""
    logger = logging.getLogger("eve-tracker.security")
    logger.warning(f"SECURITY | {event_type} | {details}")
