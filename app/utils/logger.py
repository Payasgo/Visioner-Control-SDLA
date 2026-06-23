# app/utils/logger.py

import logging


def setup_logger(name: str = "VisionerSDLA") -> logging.Logger:
    """Configure root logging once and return a named logger."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    return logging.getLogger(name)
