import time
from PyQt5.QtCore import (
    Qt,
    QObject,
    QRect,
    pyqtSlot,
    pyqtSignal,
    QThreadPool,
    QRunnable,
    QTimer,
    QRect,
)
from PyQt5.QtGui import QIcon, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QLabel,
    QSizePolicy,
    QMainWindow,
    QLineEdit,
    QFrame,
    QGroupBox,
)
from PyQt5 import QtWidgets, QtCore, QtCore, QtWidgets, QtPrintSupport

from waitingspinnerwidget import QtWaitingSpinner

import traceback, sys, json, requests, time, cups, os, pyqrcode
#import usb.core

from barcode import Code128
from barcode.writer import ImageWriter


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QRunnable):
    def __init__(self, func, *args, **kwargs):
        super(Worker, self).__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class QImageViewer(QMainWindow):
    # sendMessageSignal = QtCore.pyqtSignal(dict)
    def __init__(self):
        super().__init__()

        # variables
        self.con_key = "asdsdgfgasrrtg"
        self.panel_id = ""
        self.counter = 0
        self.maxCounter = 6
        self.memory = []
        self.printerLabel = ""

        # QtThread
        self.threadpool = QThreadPool()
        self.spinner = QtWaitingSpinner(self)

        self.main_widget = QtWidgets.QWidget(self)
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        # vertical separator lin
        self.separatorLine = QFrame()
        self.separatorLine.setFrameShape(QFrame.VLine)
        self.separatorLine.setFrameShadow(QFrame.Raised)
        self.separatorLine.setLineWidth(50)
        self.separatorLine.setMidLineWidth(5)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHeightForWidth(
            self.separatorLine.sizePolicy().hasHeightForWidth()
        )
        self.separatorLine.setSizePolicy(sizePolicy)
        self.separatorLine.setStyleSheet("font: 9pt;")
        self.separatorLine.setLineWidth(0)
        self.separatorLine.setMidLineWidth(10)

        # device counter
        # self.deviceCounter = len(list(usb.core.find(find_all=True, idVendor=1133, idProduct=1555)))

        # product Counter lable
        self.counterLabel = QLabel()
        self.counterLabel.setAlignment(Qt.AlignCenter)
        self.counterLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.counterLabel.setScaledContents(True)
        self.counterLabel.setText(str(self.counter))
        self.counterLabel.setStyleSheet(
            """
            QLabel{
                margin: 35px;
                color:#120a36;
                font-size: 400px;
            }
        """
        )

        # Serial number list
        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.setStyleSheet(
            "border:0px;font-size:18px;margin: 35px;background-color:#efefef;color:black;"
        )
        self.listWidget.setDisabled(True)

        self.lineEdit = QLineEdit()
        self.lineEdit.setStyleSheet(
            "background-color: rgba(10, 0, 0, 0); color: rgba(10, 0, 0, 0); border:0px;"
        )
        self.lineEdit.setFrame(False)
        self.lineEdit.textChanged.connect(self.sync_lineEdit)

        self.anytext = QtWidgets.QLabel("")

        self.combo = QtWidgets.QComboBox()
        self.combo.addItems(
            ["6", "8", "10", "12", "14", "20", "22", "24", "26", "28", "30"]
        )
        self.combo.setCurrentText(str(self.maxCounter))
        self.combo.setStyleSheet(
            """
            height:40px;
            font-size:20px
            """
        )
        self.comth = [6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
        self.comth2 = [6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
        self.combo.activated.connect(self.setdatastrength)

        # self.btn1 = QtWidgets.QPushButton()
        # self.btn1.setStyleSheet("margin-left:60px; padding: 20px")
        # self.btn1.setFixedSize(70, 70)
        # self.btn1.setIcon(QIcon("scanner.png"))
        # self.btn1.setIconSize(self.btn1.size())
        # self.btn1.setFlat(True)

        # self.btn2 = QtWidgets.QPushButton()
        # self.btn2.setStyleSheet("margin-left:60px;")
        # self.btn2.setFixedSize(70, 70)
        # self.btn2.setIcon(QIcon("scanner.png"))
        # self.btn2.setIconSize(self.btn2.size())
        # self.btn2.setFlat(True)

        # self.scannerLayout.addWidget(self.btn2,5)
        # self.scannerLayout.addWidget(self.btn1,5)

        self.scannerLayout = QtWidgets.QVBoxLayout()
        self.scannerLayout.addWidget(self.combo, 3)
        self.scannerLayout.addWidget(self.lineEdit)
        self.scannerLayout.addWidget(self.anytext)

        self.groupBox3 = QGroupBox("EXTRA INFO")
        self.groupBox3.setLayout(self.scannerLayout)
        self.groupBox3.setStyleSheet("background-color:#eaff80;")

        self.firmLable = QLabel()
        self.firmLable.setText("Vodka")
        self.firmLable.setStyleSheet(
            "font-size: 24px; color: white; font-family:Times New Roman; font-weight: bold; background-color:#120a36; padding:5px;"
        )

        self.zoneLable = QLabel()
        self.zoneLable.setText("ZONE: Rezka")
        self.zoneLable.setStyleSheet(
            "color: white; font-family:Times New Roman;  background-color:#120a36; padding:5px;"
        )

        self.panelLabel = QLabel()
        self.panelLabel.setText("L1-01")
        self.panelLabel.setStyleSheet(
            "color: white; font-family:Times New Roman;  background-color:#120a36; padding:5px;"
        )

        self.errorlabel = QLabel()
        self.errorlabel.setText("Error:")
        self.errorlabel.setAlignment(Qt.AlignTop)
        self.errorlabel.setStyleSheet(
            "font-size: 18px; color: red; font-family:Times New Roman;background-color:#120a36"
        )

        vh1 = QtWidgets.QVBoxLayout()
        vh1.setSpacing(0)
        vh1.addWidget(self.firmLable)
        vh1.addWidget(self.zoneLable)
        vh1.addWidget(self.panelLabel)

        vh2 = QtWidgets.QVBoxLayout()
        vh2.setSpacing(0)
        vh2.addWidget(self.errorlabel)

        h1 = QtWidgets.QHBoxLayout()
        h1.setSpacing(0)
        h1.addLayout(vh1, 3)
        h1.addLayout(vh2, 7)

        v12 = QtWidgets.QVBoxLayout()
        v12.addWidget(self.counterLabel)

        v13 = QtWidgets.QVBoxLayout()
        v13.addWidget(self.listWidget)
        v13.addWidget(self.spinner)

        v1 = QtWidgets.QHBoxLayout()
        v1.setSpacing(0)
        v1.addLayout(v12, 6)
        v1.addWidget(self.separatorLine)
        v1.addLayout(v13, 4)

        v2 = QtWidgets.QVBoxLayout()
        v2.setSpacing(0)
        v2.addWidget(self.groupBox3)

        h2 = QtWidgets.QHBoxLayout()
        h2.setSpacing(0)
        h2.addLayout(v1, 12)
        h2.addLayout(v2, 1)

        l = QtWidgets.QVBoxLayout(self.main_widget)
        l.setSpacing(0)
        l.setContentsMargins(0, 0, 0, 0)
        l.addLayout(h1, 1)
        l.addLayout(h2, 15)

        self.setWindowTitle("AROQ")
        self.setGeometry(QRect(400, 100, 1200, 800))
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        # self.setCursor(Qt.BlankCursor)
        self.showMaximized()
        self.showFullScreen()
        self.starter()
        self.timer = QTimer()
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.editFocuser)
        self.timer.start()

    @QtCore.pyqtSlot(int)
    def setdatastrength(self, index):
        value = self.comth2[index]
        if self.counter < self.maxCounter:
            self.maxCounter = value
        elif self.counter == self.maxCounter:
            self.counter = 0
            self.maxCounter = value
            self.counterLabel.setText(str(self.counter))
        self.lineEdit.setFocus()

    def editFocuser(
        self,
    ):
        self.lineEdit.setFocus()

    def sync_lineEdit(self, text):
        if len(text) == 14:
            self.validating()

    def print_output(self, s):
        if s != True:
            self.errorlabel.setText(f"Error:Server is not responding")
            # self.errorlabel.setText(f"Error:{s}")

    def thread_complete(self):
        if not self.printerLabel:
            self.printerLabel = "AABBCCDDEEFFGG"

        # filename = os.path.abspath(os.path.realpath('somefile.jpg'))
        # with open(filename, "wb") as f:
        #     Code128(self.printerLabel, writer=ImageWriter()).write(f)
        qr = pyqrcode.create(self.printerLabel)
        qr.png('qrcode.png', scale=10)
        filename = os.path.abspath(os.path.realpath('qrcode.png'))
        conn = cups.Connection()
        def_print = conn.getDefault()
        filename = os.path.abspath(os.path.realpath('somefile.jpg'))
        conn.printFile(def_print, filename, "Project Report", {})
        
        self.printerLabel = ""
        self.spinner.stop()
        self.counterLabel.setText("0")
        self.listWidget.clear()
        self.counterLabel.setStyleSheet(
            """
            QLabel{
                margin: 35px;
                color:#120a36;
                font-size: 400px;
            }
        """
        )

    def reload(self):
        reload_url = "http://127.0.0.1:8080/api-container/containers/"
        headers = {
            "Content-Type": "application/json",
        }
        auth = ("admin", "admin2020")
        data = {
            "volume": self.maxCounter,
            "panel": self.panel_id,
            "product_items": [{"serial_name": i} for i in self.memory],
        }
        data = json.dumps(data)
        self.memory = []
        time.sleep(2)
        try:
            r = requests.post(
                reload_url,
                data=data,
                auth=requests.auth.HTTPBasicAuth(*auth),
                headers=headers,
            )
            if r.status_code == 201:
                self.printerLabel = r.json()["serial_name"]
                return True
            else:
                return r.json()
        except Exception as e:
            return e

    def starter(self):
        starter_url = f"http://127.0.0.1:8080/api-panel/panels/?con_key={self.con_key}"
        headers = {
            "Content-Type": "application/json",
        }
        auth = ("admin", "admin2020")
        self.memory = []
        try:
            r = requests.get(
                starter_url, auth=requests.auth.HTTPBasicAuth(*auth), headers=headers
            )
            if r.status_code == 200:
                data = r.json()
                data = data.get("results", None)
                if data:
                    self.panel_id = data[0]["id"]
                    if data[0]["zone"]:
                        zone = data[0]["zone"]
                        self.firmLable.setText(zone["factory"]["name"])
                        self.zoneLable.setText(f"Zone: {zone['name']} {zone['code']}")
                        self.panelLabel.setText(f"Panel: {data[0]['code']}")

        except Exception as e:
            self.errorlabel.setText(
                f"Serverga bog'lanishda xatolik!, Serveriga bog'lana olmadi. Xatolik sababi:TimeOutError"
            )

    def validating(self):
        if len(self.lineEdit.text()) > 0:
            if not self.lineEdit.text() in self.memory:
                self.memory.append(self.lineEdit.text())
                self.listWidget.addItem(f"{len(self.memory)}. {self.lineEdit.text()}")
                self.counter += 1
                if self.counter < min(self.comth):
                    self.combo.clear()
                    self.combo.addItems(list(map(str, self.comth)))
                    self.combo.setCurrentText(str(self.maxCounter))
                    self.comth2 = self.comth
                elif self.counter >= min(self.comth) and self.counter < self.maxCounter:
                    self.combo.clear()
                    if self.counter % 2 == 0:
                        self.combo.addItems(
                            list(
                                map(
                                    str,
                                    self.comth[self.comth.index(self.counter) + 1 :],
                                )
                            )
                        )
                        self.comth2 = self.comth[self.comth.index(self.counter) + 1 :]
                    else:
                        self.combo.addItems(
                            list(
                                map(
                                    str,
                                    self.comth[self.comth.index(self.counter + 1) :],
                                )
                            )
                        )
                        self.comth2 = self.comth[self.comth.index(self.counter + 1) :]
                    self.combo.setCurrentText(str(self.maxCounter))
                else:
                    self.combo.clear()
                    self.combo.addItems(list(map(str, self.comth)))

                    self.comth2 = self.comth
                    self.combo.setCurrentText(str(self.maxCounter))
            self.counterLabel.setText(str(self.counter))
            self.lineEdit.setText("")
            if self.counter % 2 == 0:
                self.counterLabel.setStyleSheet(
                    """
                    QLabel{
                        background-color:yellow;
                        margin: 35px;
                        color:#120a36;
                        font-size: 400px;
                    }
                """
                )
            else:
                self.counterLabel.setStyleSheet(
                    """
                    QLabel{
                        background-color:green;
                        margin: 35px;
                        color:#120a36;
                        font-size: 400px;
                    }
                """
                )

            if self.counter == self.maxCounter:
                self.spinner.start()
                self.combo.clear()
                self.combo.addItems(list(map(str, self.comth)))
                self.comth2 = self.comth
                self.combo.setCurrentText(str(self.maxCounter))
                self.counter = 0
                worker = Worker(self.reload)
                worker.signals.result.connect(self.print_output)
                worker.signals.finished.connect(self.thread_complete)
                self.threadpool.start(worker)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    imageViewer = QImageViewer()
    imageViewer.show()
    imageViewer.lineEdit.setFocus()
    sys.exit(app.exec_())
