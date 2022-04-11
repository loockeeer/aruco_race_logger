import time
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtGui import QPixmap, Qt
from PySide6.QtWidgets import (
    QTableWidget,
    QHeaderView,
    QTableWidgetItem,
    QMainWindow,
    QVBoxLayout,
    QPushButton,
    QHBoxLayout, QSizePolicy,
)
import json

class OpenCVImageWidget(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super(OpenCVImageWidget, self).__init__(parent)
        self.last_preserve = -99999.0

    def show_image(self, image, preserve=False, force=False):
        if (self.last_preserve + 0.75) > time.time() and not force:
            return
        if preserve:
            self.last_preserve = time.time()
        qimage = QtGui.QImage(
            image.data, image.shape[1], image.shape[0], QtGui.QImage.Format_RGB888
        ).rgbSwapped()
        self.setPixmap(QPixmap.fromImage(qimage).scaledToWidth(self.geometry().width()))

    def closeEvent(self, event):
        if self.parent() is not None:
            self.parent().close()

class RaceTable(QTableWidget):
    def __init__(self, win, *args):
        QTableWidget.__init__(self, *args)
        self.win = win
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(("ID", "Nom", "Tours", "Vitesse Arrivée", "Temps Tour"))
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        for i in range(4):
            self.horizontalHeader().setSectionResizeMode(
                i, QHeaderView.ResizeMode.Stretch
            )

        with open("./config.json", 'r') as file:
            self.config = json.loads(file.read())

    def addElements(self, index, elements, format):
        for i, element in enumerate(elements):
            widget = QTableWidgetItem("N/A" if not element else str(element))
            if format:
                format(widget)
            self.setItem(index, i, widget)

    def setMarker(self, i, marker, best_time):
        arrival_time = (
            -1
            if len(marker.passed) == 0
            else (
                marker.passed[0] - self.win.start_time
                if len(marker.passed) == 1
                else marker.passed[-1] - marker.passed[-2]
            )
        )
        format = None
        if best_time:
            format = lambda widget: widget.setBackground(Qt.yellow)
        if arrival_time == -1 or marker.speed == -1:
            return
        self.addElements(
            i,
            (
                marker.id,
                self.config.get(str(marker.id), ""),
                len(marker.passed),
                round(marker.speed(), 2),
                round(arrival_time, 2),
            ),
            format,
        )

    def setData(self, markers):
        markers = list(
            filter(
                lambda marker: len(marker.passed) != 0,
                reversed(
                    sorted(markers.values(), key=lambda marker: (
                    len(marker.passed), 0 if len(marker.passed) == 0 else -marker.passed[-1]))
                ),
            )
        )
        ordered_by_time = list(
            sorted(
                markers,
                key=lambda marker: 99999
                if len(marker.passed) == 0
                else marker.passed[-1],
            )
        )
        i = 0
        for i, marker in enumerate(markers):
            self.setMarker(i, marker, ordered_by_time[0].id == marker.id)

        for id, nickname in self.config.items():
            if len([True for marker in markers if str(marker.id) == id]) == 0:
                self.addElements(i, (id, nickname, None, None, None), None)
                i+=1
        self.setRowCount(i)


class RaceGui(QMainWindow):
    def __init__(self, *args):
        QMainWindow.__init__(self, *args)
        self.state = False
        self.setWindowTitle("Affichage Course")

        layout = QVBoxLayout()

        self.start_time = None

        self.table = RaceTable(self)
        self.video = OpenCVImageWidget()
        self.video.show()
        layout.addWidget(self.table)

        self.button = QPushButton("Démarrer")
        self.button.clicked.connect(self.button_clicked)
        layout.addWidget(self.button)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def setData(self, markers):
        self.table.setData(markers)

    def button_clicked(self, b):
        self.state = not self.state
        if self.state:
            self.start_time = time.time()
        self.button.setText("Démarrer" if not self.state else "Arrêter")

    def show_image(self, frame, preserve=False, force=False):
        self.video.show_image(frame, preserve, force)

    def closeEvent(self, event):
        self.video.close()