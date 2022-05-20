import logging
import time
from websocket_server import WebsocketServer

import cv2

import backend.core.ws_handlers
from backend import config, utils
from backend.config import Config
from backend.core.aruco import get_markers
from backend.core.types import Position, Marker
from backend.core import ws_handlers


def main(configuration: Config, config_path: str):
    logging.basicConfig()
    logger = utils.get_logger("main")
    logger.info(f"Loaded configuration from {config_path}")
    logger.info(f"Starting WebSocket Server")

    server = WebsocketServer(
        host=configuration.ws_host, port=configuration.ws_port, loglevel=logging.ERROR
    )
    server.set_fn_new_client(ws_handlers.new_client)
    server.set_fn_message_received(ws_handlers.message_received)
    server.set_fn_client_left(ws_handlers.client_left)
    server.run_forever(threaded=True)

    logger.info("Starting main aruco loop")
    markers = {}

    for id, name in configuration.markers.items():
        markers[id] = Marker(id, name, [], [])

    server.markers = markers
    server.config = configuration

    capture = cv2.VideoCapture(configuration.capture_device)
    aruco_parameters = cv2.aruco.DetectorParameters_create()
    while capture.isOpened():
        ret, frame = capture.read()
        if not ret:
            continue
        detected_markers, draw = get_markers(
            frame,
            dict=configuration.aruco_dict,
            parameters=aruco_parameters,
            real_size=configuration.marker_size,
            camera_matrix=configuration.camera_matrix,
            dist_coeffs=configuration.dist_coeffs,
        )
        cv2.imshow("draw", draw)
        t = time.time()
        for id, rvec, tvec in detected_markers:
            marker = markers.get(id, None)
            if not marker:
                marker = Marker(id, configuration.markers.get(id, None), [Position(time.time(), rvec, tvec)], [])
                markers[id] = marker
            else:
                marker.history.append(Position(time.time(), rvec, tvec))

            distance = marker.current.tvec[2]
            if len(marker.history) > 1:
                previous_distance = marker.history[-2].tvec[2]
                if previous_distance > configuration.line_distance > distance:
                    logger.debug(f"Marker {id} passed the line")
                    arrived_time = t
                    if marker.speed != -1: arrived_time -= (marker.current.tvec[2] - configuration.line_distance) / marker.speed
                    marker.laps.append(arrived_time)
                    server.send_message_to_all(backend.core.ws_handlers.get_ws_marker_lap(arrived_time, marker))

            server.send_message_to_all(backend.core.ws_handlers.get_ws_marker_detected(t, marker))
            logger.debug(
                f"Marker {id} detected, distance : {str(round(marker.current.tvec[2], 2))}"
            )
        cv2.waitKey(1)
    capture.release()
    logger.info("Closing race logger")


if __name__ == "__main__":
    configuration = config.get_config(config.DEFAULT_CONFIG_PATH)
    main(configuration, config.DEFAULT_CONFIG_PATH)
