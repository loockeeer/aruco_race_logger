import csv
import threading
from aruco import *
from gui import *
import sys
import yaml
import numpy as np
from signal import signal, SIGINT, SIG_DFL



def gather_data(arucoInstance, gui):
    thread = threading.current_thread()
    while not gui.state and getattr(thread, "running", True):
        pass
    if not getattr(thread, "running", True):
        return
    for (frame, passed) in arucoInstance.start_detection():
        while not gui.state and getattr(thread, "running", True):
            pass
        if not getattr(thread, "running", True):
            break
        gui.setData(arucoInstance.markers)
        saveDataCSV("./race_data.csv", arucoInstance.markers, gui.start_time)
        gui.show_image(frame, len(passed) > 0, len(passed) > 0)


def saveDataCSV(filename, markers, start_time):
    with open(filename, "w") as file:
        markers = list(
            filter(
                lambda marker: len(marker.passed) != 0,
                reversed(
                    sorted(markers.values(), key=lambda marker: sum(marker.passed))
                ),
            )
        )
        formatted = [
            [
                marker.id,
                len(marker.passed),
                marker.speed(),
                -1
                if len(marker.passed) == 0
                else (
                    marker.passed[0] - start_time
                    if len(marker.passed) == 1
                    else marker.passed[-1] - marker.passed[-2]
                ),
            ]
            for marker in markers
        ]
        fields = ["id", "laps", "speed", "last_lap_time"]
        writer = csv.writer(file)
        writer.writerow(fields)
        writer.writerows(formatted)

def get_dict_from_input(inp):
    return getattr(cv2.aruco, f"DICT_{inp}X{inp}_250")

if __name__ == "__main__":
    with open("./parameters.yaml", "r") as file:
        loaded = yaml.load(file, Loader=yaml.FullLoader)
    matrix = np.array(loaded.get("camera_matrix"))
    dist = np.array(loaded.get("dist_coeff"))
    maxSpeed = 0.0
    detector = ArucoCarDetector(
        int(sys.argv[1]),
        float(sys.argv[2]),
        float(sys.argv[3]),
        matrix,
        dist,
        get_dict_from_input(sys.argv[4]),
    )

    app = QtWidgets.QApplication(sys.argv)
    gui = RaceGui()
    signal(SIGINT, SIG_DFL)

    thread = threading.Thread(target=gather_data, args=(detector, gui))
    thread.start()
    gui.show()
    app.exec()
    thread.running = False
    thread.join()
