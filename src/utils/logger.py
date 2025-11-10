thonimport logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

_LOGGER_CONFIGURED = False

def setup_logging(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Configure root logger with console and optional file handlers.
    """
    global _LOGGER_CONFIGURED
    if _LOGGER_CONFIGURED:
        return

    config = config or {}
    level_name = config.get("level", "INFO")
    level = getattr(logging, level_name.upper(), logging.INFO)

    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    formatter = logging.Formatter(log_format)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Optional file handler
    log_file = config.get("file")
    if log_file:
        path = Path(log_file).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    _LOGGER_CONFIGURED = True

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a logger with the given name.
    """
    return logging.getLogger(name)