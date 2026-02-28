import sys
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QSlider, QPushButton, QVBoxLayout, QWidget, QHBoxLayout
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt, QThread, Signal
import cv2 as cv
import processing.video_landmark
import config
import numpy as np


def np_to_qpixmap(frame: np.ndarray) -> QPixmap:
    
    rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    h, w, ch = rgb_frame.shape
    bytes_per_line = ch * w
    qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888) # type: ignore
    return QPixmap.fromImage(qimg)

def 

