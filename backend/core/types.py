from dataclasses import dataclass
from typing import List, NamedTuple
import numpy as np

from backend import utils


class Position(NamedTuple):
    time: float
    rvec: np.ndarray
    tvec: np.ndarray


@dataclass
class Marker:
    id: int
    name: str
    history: List[Position]
    laps: List[float]

    @property
    def current(self) -> Position:
        return self.history[-1] if len(self.history) > 0 else None

    @property
    def position(self) -> np.ndarray:
        return self.current.tvec

    @property
    def rotation(self) -> np.ndarray:
        return self.current.rvec

    @property
    def speed(self) -> float:
        time_range = 1000
        first = None
        points = []
        for point in self.history:
            if not first: first = point.time
            if point.time - first > time_range: break
            points.append(point)
        speeds = [utils.speed(points[i], points[i + 1]) for i in range(len(points) - 1)]
        if len(points) > 1:
            return abs(sum(speeds)/len(speeds))
            # weights = range(1, len(speeds) + 1)
            # speeds = [speeds[i] * weights[i] for i in range(len(speeds))]
            # return abs(sum(speeds)/sum(weights))
        else:
            return -1
