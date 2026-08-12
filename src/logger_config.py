"""Logging setup shared by all pipeline modules."""

from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(log_path: Path) -> logging.Logger:
    """Configure console and file logging once and return the app logger."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("airport_pipeline")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

