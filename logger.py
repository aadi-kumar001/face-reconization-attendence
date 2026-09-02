"""
Rotating, structured logging so a long-running kiosk deployment doesn't
fill the disk and problems are traceable by module + timestamp.
"""
import logging
import os
from logging.handlers import RotatingFileHandler

from config import Config


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured, avoid duplicate handlers

    logger.setLevel(logging.DEBUG if Config.DEBUG else logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)

    try:
        os.makedirs(Config.LOG_DIR, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(Config.LOG_DIR, "fras.log"),
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
        )
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    except OSError:
        # Read-only filesystem or similar — console logging still works.
        pass

    logger.propagate = False
    return logger
