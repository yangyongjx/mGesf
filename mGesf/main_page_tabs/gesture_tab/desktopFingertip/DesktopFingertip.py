from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTabWidget
from mGesf.main_page_tabs.gesture_tab.desktopFingertip.Recording import Recording
from mGesf.main_page_tabs.gesture_tab.desktopFingertip.Train import Train
from mGesf.main_page_tabs.gesture_tab.desktopFingertip.Detection import Detection
import config
from PyQt5.QtWidgets import QWidget, QHBoxLayout

from utils.GUI_gesture_tab import setup_operation_tabs
from utils.GUI_main_window import init_container


class DesktopFingertip(QWidget):
    def __init__(self):
        super().__init__()
        self.main_page = QHBoxLayout(self)

        # self.operation_block = init_container(parent=self.main_page, vertical=False)
        # setup_operation_tabs(self.operation_block)

        self.setLayout(self.main_page)
        self.show()



