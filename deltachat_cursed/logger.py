"""Logging to log files"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from . import APP_NAME


def create_logger(level: str, folder: Path) -> logging.Logger:
    logger = logging.Logger(APP_NAME)
    logger.parent = None

    if level == "disabled":
        logger.disabled = True
        return logger

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    log_path = folder / "logs"
    log_path.mkdir(parents=True, exist_ok=True)
    log_path /= "log.txt"

    fhandler = RotatingFileHandler(log_path, backupCount=3, maxBytes=2000000)
    fhandler.setLevel(level.upper())
    fhandler.setFormatter(formatter)
    logger.addHandler(fhandler)

    return logger
