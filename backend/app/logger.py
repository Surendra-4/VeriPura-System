import logging
import sys

from app.config import get_settings


def setup_logger() -> logging.Logger:
    """
    Configure structured logging with sensible defaults.
    Logs to stdout (captured by hosting platforms).
    """
    settings = get_settings()

    logger = logging.getLogger("veripura")
    logger.setLevel(settings.log_level)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(settings.log_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


# Global logger instance
logger = setup_logger()
