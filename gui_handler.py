import sys
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget, QDialog, QLineEdit
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt, Signal, Slot, QThread
import numpy as np
import cv2 as cv
import processing.processing as processing

## Function to convert a NumPy array to QPixmap (for showing an image)
def np_to_qpixmap(frame: np.ndarray):
    if(frame is not None):
        rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)  # type: ignore
        return QPixmap.fromImage(qimg)


class RecordingWindow(QDialog):
    is_recording = Signal(bool, str)
    
    def __init__(self):
        super().__init__()
        
        self.recording = False
        self.setWindowTitle("Recording")
        self.setGeometry(300, 300, 300, 200)

        recording_button = QPushButton("Would you like to save this livestream?", self)
        recording_button.clicked.connect(self.start_recording)  
        
        
        self.save_path = QLineEdit(self)
        self.save_path.setText("Where would you like to save this?" +  "(.mp4)")
        self.save_path.returnPressed.connect(self.on_submit)
        
        
        layout = QVBoxLayout(self)
        layout.addWidget(recording_button)
        layout.addWidget(self.save_path)
        
    def start_recording(self):
        self.recording = True
       
    def on_submit(self):
        self.is_recording.emit(self.recording, self.save_path.text()) 
        self.accept() 
        

class saving_window(QDialog):
    to_save = Signal(list)
    def __init__(self):
        super().__init__()
        
        self.saving = False
        
        self.setWindowTitle("Do you want to save the modified media?")
        recording_button = QPushButton("Would you like to record/save this footage?", self)
        recording_button.clicked.connect(self.start_recording)  
        
        
        self.save_path = QLineEdit(self)
        self.save_path.setText("Where would you like to save this?" +  "(.mp4)")
        self.save_path.returnPressed.connect(self.on_submit)
    
    def start_recording(self):
        self.saving = True
    
    def on_submit(self):
        self.to_save.emit(self.saving, self.save_path)
        self.accept()
        
        

class MainWindow(QMainWindow):
    is_recording = Signal(list)
    def __init__(self,annotated_frame: np.ndarray = None):  # type: ignore
        super().__init__()
        
        self.setWindowTitle("Landmark Viewer")
        self.setGeometry(100, 100, 800, 600)
        
        self.annotated_frame = annotated_frame
        self.frames = []
        self.timestamps = []
        
        layout = QVBoxLayout()
        
        image = QPushButton("Image", self)
        image.clicked.connect(lambda: self.route_processing("Image"))
        layout.addWidget(image)
        
        video = QPushButton("Video", self)
        video.clicked.connect(lambda: self.route_processing("Video"))
        layout.addWidget(video)
        
        stream = QPushButton("Livestream", self)
        stream.clicked.connect(lambda: self.route_processing("Livestream"))
        layout.addWidget(stream)
            
        self.label = QLabel(self)
        if annotated_frame is not None:
            self.label.setPixmap((np_to_qpixmap(self.annotated_frame)))
        
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
            
        
            
        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
    @Slot()
    def route_processing(self, process_type: str):
        self.process_type = process_type.lower()
        
        self.open_saving_window()
        if(self.process_type == "livestream"):
            self.open_recording_window()
            self.cap = cv.VideoCapture(0)
            
        self.worker = processing.process(process_type)
        self.worker.image.connect(self.update_frame)
        self.saving_window.to_save.connect(self.save_video)
        self.worker.image.connect(self.maybe_save_frame) 
         
        self.worker.start()        

    def open_recording_window(self):
        recording_window = RecordingWindow()
        recording_window.is_recording.connect(self.set_recording)
        recording_window.exec()
        
    #Window to prompt saving of any/all annotated media
    def open_saving_window(self):
        self.saving_window = saving_window()
        self.saving_window.to_save.connect(self.save_video)
        self.saving_window.exec()
    
    
    ##Livestream
    @Slot(list)
    def set_recording(self, list):
        self.recording = list[0]
        self.save_path = list[1]
    
    #General media  
    @Slot(bool, str)
    def save_video(self, saving: bool, path: str):
        self.saving = saving
        self.path = path
        
    
    def maybe_save_frame(self, frame: np.ndarray, timestamp:int = 0):
        if(self.saving):    
                self.frames.append(frame)
                self.timestamps.append(timestamp)    
        
            
    @Slot(np.ndarray, int)        
    def update_frame(self, frame:np.ndarray, timestamp:int):
        self.timestamp = timestamp
        self.label.setPixmap(np_to_qpixmap(frame))
        self.maybe_save_frame(frame, timestamp)
        
        

def run(self):
    app = QApplication(sys.argv)
    window = MainWindow() 
    window.show() 
    sys.exit(app.exec())