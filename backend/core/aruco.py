from typing import Any, Union

import cv2
import numpy as np


def get_markers(
    frame: np.ndarray,
    dict: int = None,
    parameters: cv2.aruco_DetectorParameters = None,
    real_size: float = None,
    camera_matrix: np.ndarray = None,
    dist_coeffs: np.ndarray = None,
) -> Union[tuple[list, Any], tuple[tuple[tuple[Any, Any, Any], ...], Any]]:
    gray = cv2.cvtColor(frame.copy(), cv2.COLOR_RGB2GRAY)
    (corners, ids, rejected) = cv2.aruco.detectMarkers(
        gray, dict, parameters=parameters
    )
    if len(corners) == 0:
        return [], frame.copy()
    draw = cv2.aruco.drawDetectedMarkers(frame.copy(), corners, ids)
    ret = cv2.aruco.estimatePoseSingleMarkers(
        corners, real_size, cameraMatrix=camera_matrix, distCoeffs=dist_coeffs
    )
    return (
        tuple(zip(ids.flatten(), [x[0] for x in ret[0]], [x[0] for x in ret[1]])),
        draw,
    )
