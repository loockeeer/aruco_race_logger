import json
from typing import Dict

from websocket_server import WebsocketServer

from backend import utils
from backend.config import Config
from backend.core.types import Marker

logger = utils.get_logger(__name__)


def new_client(client: dict, server: WebsocketServer):
    addr, port = client["address"][0], client["address"][1]
    # Send an ack to the client
    server.send_message(client, get_ws_ack())
    logger.info(f"New client at {addr}:{str(port)} connected to server ")


def message_received(client, server: WebsocketServer, message: str):
    try:
        data = json.loads(message)
    except:
        return server.send_message(client, get_ws_error("bad_request"))
    try:
        if data.get("t") != "rq":
            logger.debug(f"Received message with bad type: {data.get('type')}")
            return server.send_message(client, get_ws_error("bad_request"))
        if data.get("k") == "h":
            logger.debug(
                f"Received history request from {client['address'][0]}:{str(client['address'][1])}"
            )
            server.send_message(client, get_ws_marker_history(server.markers))
        elif data.get("k") == "c":
            logger.debug(
                f"Received config request from {client['address'][0]}:{str(client['address'][1])}"
            )
            server.send_message(client, get_ws_marker_config(server.config))
        else:
            server.send_message(client, get_ws_error("bad_request"))
    except Exception as e:
        raise e
        logger.error(f"Error while processing request: {e}")
        server.send_message(client, get_ws_error("internal_error"))


def client_left(client: dict, _):
    addr, port = client["address"][0], client["address"][1]
    logger.info(f"Client at {addr}:{str(port)} disconnected")


def get_ws_message(type: str, kind: str, data: Dict) -> str:
    return json.dumps({"t": type, "k": kind, "d": data})


def get_ws_error(kind: str) -> str:
    return get_ws_message("e", kind, {})


def get_ws_marker_detected(time: float, marker: Marker) -> str:
    return get_ws_message(
        "m",
        "d",
        {
            "t": float(time),
            "i": int(marker.id),
            "p": {
                "x": float(marker.current.tvec[0]),
                "y": float(marker.current.tvec[1]),
                "z": float(marker.current.tvec[2]),
            },
            "s": marker.speed,
            "r": {
                "x": float(marker.current.rvec[0]),
                "y": float(marker.current.rvec[1]),
                "z": float(marker.current.rvec[2]),
            },
        },
    )


def get_ws_marker_lap(time: float, marker: Marker) -> str:
    return get_ws_message(
        "m", "l", {"t": float(time), "i": int(marker.id), "l": len(marker.laps)}
    )


def get_ws_marker_history(markers: Dict[int, Marker]) -> str:
    return get_ws_message(
        "rs",
        "h",
        {
            int(marker.id): {
                "l": marker.laps,
                "n": marker.name,
                "i": int(marker.id),
                "s": float(marker.speed),
                "p": {
                    "x": float(marker.current.tvec[0]),
                    "y": float(marker.current.tvec[1]),
                    "z": float(marker.current.tvec[2]),
                } if marker.current is not None else {"x": 0, "y": 0, "z": 0},
                "r": {
                    "x": float(marker.current.rvec[0]),
                    "y": float(marker.current.rvec[1]),
                    "z": float(marker.current.rvec[2]),
                } if marker.current is not None else {"x": 0, "y": 0, "z": 0},
            }
            for marker in markers.values()
        },
    )


def get_ws_marker_config(config: Config) -> str:
    return get_ws_message("rs", "c", {"u": config.unit, "l": config.line_distance, "m": config.markers})


def get_ws_ack() -> str:
    return get_ws_message("a", "c", {})
