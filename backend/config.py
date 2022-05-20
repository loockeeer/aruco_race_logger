from dataclasses import dataclass
from typing import Any, TypeVar, Union, Callable

import cv2.aruco
import numpy as np
import toml
import logging

DEFAULT_CONFIG_PATH = "./config.toml"


@dataclass
class Config:
    unit: str
    capture_device: int
    marker_size: float
    line_distance: float
    ws_port: int
    ws_host: str
    camera_matrix: np.ndarray
    dist_coeffs: np.ndarray
    log_level: int
    aruco_dict: int
    log_path: str
    markers: dict[int, str]

def _get_dict_from_id(id, size=250):
    return cv2.aruco.Dictionary_get(
        getattr(cv2.aruco, f"DICT_{str(id)}X{str(id)}_{str(size)}")
    )


def get_config(file: str) -> Config:
    with open(file, "r") as file:
        config = toml.loads(file.read())

    unit = _get_config_as_type(config, str, "aruco.unit", None)
    capture_device = _get_config_as_type(config, int, "aruco.capture_device", None)
    marker_size = _get_config_as_type(config, float, "aruco.marker_size", None)
    line_distance = _get_config_as_type(config, float, "aruco.line_distance", None)
    ws_port = _get_config_as_type(config, int, "ws.port", 8080)
    ws_host = _get_config_as_type(config, str, "ws.host", "0.0.0.0")
    camera_matrix = _get_config_as_type(config, np.array, "aruco.camera_matrix", None)
    dist_coeffs = _get_config_as_type(config, np.array, "aruco.dist_coeffs", None)
    log_level = _get_config_as_type(
        config,
        lambda lvl: getattr(logging, lvl) or logging.INFO,
        "logs.level",
        logging.INFO,
    )
    log_path = _get_config_as_type(config, str, "logs.path", "logs.log")
    aruco_dict = _get_config_as_type(
        config, _get_dict_from_id, "aruco.aruco_dict", cv2.aruco.DICT_4X4_250
    )
    markers = _get_config_as_type(config, dict, "aruco.markers", {})
    markers = {int(k): v["name"] for k, v in markers.items()}
    return Config(
        unit=unit,
        capture_device=capture_device,
        marker_size=marker_size,
        line_distance=line_distance,
        ws_port=ws_port,
        ws_host=ws_host,
        camera_matrix=camera_matrix,
        dist_coeffs=dist_coeffs,
        log_level=log_level,
        aruco_dict=aruco_dict,
        log_path=log_path,
        markers=markers
    )


K = TypeVar("K")


def _get_config_as_type(
    config: object,
    value_type: Union[K, Callable[[Any], Union[type(K), None]]],
    key: str,
    default: Union[type(K), None],
    error_missing="Missing '{}' value in config",
    error_type="Value '{}' is incorrect in config",
) -> type(K):
    print(key)
    keys = key.split(".")
    try:
        value = config
        for key in keys:
            if key not in value:
                if default:
                    return default
                raise ValueError(error_missing.format(key))
            else:
                value = value[key]
        return value_type(value)
    except KeyError:
        raise KeyError(error_type.format(key))
