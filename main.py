
from collections import deque

import processing
from PySide6.QtCore import Slot, Signal, QThread, QObject
from PySide6.QtWidgets import QApplication
import cv2 as cv
import sys
import numpy as np
import gui

class Main(QObject):
    data = Signal(cv.VideoCapture)
    frame_transfer = Signal(np.ndarray, int)
    img_path = Signal(str)
    def __init__(self):
        super().__init__()
        self.process_type = ""
        
        self.cap = None
        
    def fetch(self, mode, file, output, save_annotated, save_raw, raw_stream):
        self.process_type = mode
        self.path = file
        if save_annotated:
            self.output = output
        if save_raw:
            self.raw_stream = raw_stream
        
        
    @Slot(str)
    def set_process(self, process_type: str):
        self.process_type = process_type
        
        
    def run(self):
        self.gui = gui.GUI(self)
        self.gui.show()
   
    def start_processing_threads(self):
        self.worker = processing.process(self.process_type)
        print(self.process_type)
        if self.process_type != "image":
            self.capture_worker = Capture(self.process_type, self.path)
            self.capture_worker.total_frames.connect(self.gui.processing_screen.set_total_frames)
            self.camera_thread = QThread()
        else:
            self.gui.input_screen.image_path.connect(self.worker.get_img_path)
        self.worker_thread = QThread()
        
        self.worker.moveToThread(self.worker_thread)
        
        if self.process_type != "image":
            self.capture_worker.moveToThread(self.camera_thread)
            self.capture_worker.capture_signal.connect(self.worker.new_frame)
            self.capture_worker.fps.connect(self.worker.update_fps)
            
        self.worker.image.connect(self.gui.processing_screen.display_frame)
        
            
        self.worker_thread.started.connect(self.worker.run)
        if self.process_type != "image":
            self.camera_thread.started.connect(self.capture_worker.run)
        
            self.camera_thread.start()
        self.worker_thread.start()
        print("threads started")   
        
    @Slot(np.ndarray, int)
    def  captureFrame(self):
        self.worker.image.connect(self.updateFrame)
    
    def updateFrame(self, data: np.ndarray, timestamp: int):
        self.frame_transfer.emit(data, timestamp)   

class Capture(QThread):
    capture_signal = Signal(bool, np.ndarray, int)
    fps = Signal(int)
    total_frames = Signal(int)
    running = Signal(bool)
    seek_signal = Signal(int)
    
    def __init__(self, mode: str, video_path: str):
        super().__init__()
        
        self.mode = mode
        self.video_path = video_path
        self.cap = None

        if self.mode == "video":
            self.cap = cv.VideoCapture(self.video_path)
            total = int(self.cap.get(cv.CAP_PROP_FRAME_COUNT))
            self.total_frames.emit(total)
            
        elif self.mode == "livestream":
            self.cap = cv.VideoCapture(0)
        if self.cap:    
            self.seek_signal.connect(self.seek)
    
    @Slot(int)
    def seek(self, frame_number):
        self.pending_seek = frame_number
    
    @Slot()
    def run(self):
        self.pending_seek = None
        if self.cap is None:
            return

        if not self.cap.isOpened():
            print(f"Failed to open capture: {self.video_path or 'camera'}")
            return
        
        self.frame_buffer = deque(maxlen=50000)
        
        total = int(self.cap.get(cv.CAP_PROP_FRAME_COUNT))
        self.total_frames.emit(total)
        self.running.emit(True)
        
        current_frame = 0
        
        while self.cap.isOpened():
            fps = int(self.cap.get(cv.CAP_PROP_FPS))
            self.fps.emit(fps)
            
            if self.pending_seek is not None:
                self.cap.set(cv.CAP_PROP_POS_FRAMES, self.pending_seek)
                self.current_frame = self.pending_seek
                self.pending_seek = None
                
            ret, frame = self.cap.read()
            if ret:
                current_frame += 1
                self.frame_buffer.append(frame)
                self.capture_signal.emit(ret, frame, current_frame)
            import time
            time.sleep(1.0 / fps)
    
if __name__ == "__main__":
    qapp = QApplication(sys.argv)
    main = Main()
    main.run()
    
    sys.exit(qapp.exec())