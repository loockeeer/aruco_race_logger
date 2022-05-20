import math

import numpy as np

from backend import config
from backend.core.types import Position

import logging


def speed(p1: Position, p2: Position) -> float:
    return math.sqrt(np.sum((p1.tvec - p2.tvec) ** 2)) / (p1.time - p2.time)


def get_logger(name):
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(module)s - %(message)s"
    )

    fileHandler = logging.FileHandler(
        mode="w",
        filename=config.get_config(config.DEFAULT_CONFIG_PATH).log_path,
        encoding="utf-8",
    )
    fileHandler.setFormatter(formatter)
    fileHandler.setLevel(logging.DEBUG)

    logger = logging.getLogger(name)
    logger.setLevel(config.get_config(config.DEFAULT_CONFIG_PATH).log_level)
    logger.addHandler(fileHandler)
    return logger
