import cv2
from dataclasses import dataclass, field
import time
import math


def dist(cA, cB):
    return math.sqrt((cA[0] - cB[0]) ** 2 + (cA[1] - cB[1]) ** 2)


def get_distance(focal, real_length, corners):
    return (real_length * focal) / dist(corners[0], corners[1])


def isPassed(current, before, line):
    return abs(current - line) + abs(before - line) != abs(
        (current - line) + (before - line)
    )


@dataclass
class Point:
    x: float
    y: float
    corners: tuple
    distance: float
    time: float


@dataclass
class Marker:
    parent: "typing.Any"
    x: float
    y: float
    corners: tuple
    id: int
    history: list = field(default_factory=list)
    passed: list = field(default_factory=list)

    def update(self, x, y, corners, marker_passed):
        self.x = x
        self.y = y
        self.corners = corners
        self.history.append(
            Point(
                x,
                y,
                corners,
                get_distance(
                    self.parent.avg_focal, self.parent.marker_real_length, corners
                ),
                time.time(),
            )
        )
        if marker_passed:
            self.passed.append(time.time())

    def distance(self):
        return get_distance(
            self.parent.avg_focal, self.parent.marker_real_length, self.corners
        )

    def speed(self, avg=2):
        if avg < 2:
            raise "Average speed must be at least on 2 points"
        if len(self.history) < avg:
            return -1
        points = self.history[-avg:]

        return abs(
            dist((points[0].x, points[0].y), (points[-1].x, points[-1].y))
            / (points[0].time - points[-1].time)
        )


class ArucoCarDetector:
    def __init__(
        self,
        capture_device,
        marker_real_length,
        line_distance,
        camera_matrix,
        dist_coeff,
        aruco_dict,
    ):
        self.capture_device = capture_device
        self.markers = {}
        self.marker_real_length = marker_real_length
        self.line_distance = line_distance
        self.camera_matrix = camera_matrix
        self.dist_coeff = dist_coeff
        self.avg_focal = (camera_matrix[0][0] + camera_matrix[1][1]) / 2
        self.dict = cv2.aruco.Dictionary_get(aruco_dict)
        self.aruco_params = cv2.aruco.DetectorParameters_create()

    def start_detection(self):
        cap = cv2.VideoCapture(self.capture_device)
        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                yield self.process_frame(frame)
        cap.release()

    def update_marker(self, id, x, y, corners, marker_passed):
        if self.markers.get(id, None):
            self.markers[id].update(x, y, corners, marker_passed)
        else:
            self.markers[id] = Marker(self, x, y, corners, id)

    def process_frame(self, frame):
        gray = cv2.cvtColor(frame.copy(), cv2.COLOR_RGB2GRAY)

        (corners, ids, rejected) = cv2.aruco.detectMarkers(
            gray, self.dict, parameters=self.aruco_params
        )

        draw = cv2.aruco.drawDetectedMarkers(frame.copy(), corners, ids)
        passed = []
        if not len(corners) > 0:
            return draw, passed
        for (corner, id, rej) in zip(corners, ids.flatten(), rejected):
            (top_left, top_right, bottom_right, bottom_left) = corner.reshape((4, 2))
            top_right = (int(top_right[0]), int(top_right[1]))
            bottom_right = (int(bottom_right[0]), int(bottom_right[1]))
            bottom_left = (int(bottom_left[0]), int(bottom_left[1]))
            top_left = (int(top_left[0]), int(top_left[1]))
            center_x = int((top_left[0] + bottom_right[0]) / 2.0)
            center_y = int((top_left[1] + bottom_right[1]) / 2.0)

            current_distance = get_distance(
                self.avg_focal,
                self.marker_real_length,
                (top_left, top_right, bottom_left, bottom_right),
            )
            marker = self.markers.get(id)
            marker_passed = False
            if (
                marker is not None
                and marker.distance() is not None
                and isPassed(current_distance, marker.distance(), self.line_distance)
            ):
                curr_time = time.time()
                print(
                    f"[ {round(curr_time, 4)} ] Marker {id} passed the line with a speed of {marker.speed()}!"
                )
                cv2.imwrite(f"shots/cross_{id}_at_{curr_time}.png", frame)
                passed.append(marker)
                marker_passed = True

            self.update_marker(
                id,
                center_x,
                center_y,
                (top_left, top_right, bottom_left, bottom_right),
                marker_passed,
            )
        return draw, passed
