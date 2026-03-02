import gui_handler
import processing.processing as processing
from PySide6.QtCore import Slot, Signal, QThread, QObject
from PySide6.QtWidgets import QApplication
import cv2 as cv
import sys
import processing.camerafeed as camera

class Main(QObject):
    data = Signal(camera.video_feed)
    def __init__(self):
        self.process_type = ""
        self.cap = None
        self.main_window = gui_handler.MainWindow()
        self.main_window.type.connect(self.set_process)
        self.main_window.file_path.connect(self.set_capture) # type: ignore
        
    @Slot(str)
    def set_process(self, process_type: str):
        self.process_type = process_type
        self.processor = processing.process(process_type)
        
        
    def set_capture(self, path: str):
        self.cap = None
        if self.process_type == "video":
            self.cap = cv.VideoCapture(path)
        elif self.process_type == "livestream":    
            self.vid_object = camera.video_feed()
            self.video_thread = QThread()
            self.vid_object.moveToThread(self.video_thread)
            
        
    def run(self):
        app = QApplication(sys.argv)
        worker = processing.process(self.process_type, self.cap) # type: ignore
        self.data.connect(worker.get_vid_object)
        
        worker_thread = QThread()
        worker.moveToThread(worker_thread)
        gui = self.main_window
        
        worker_thread.started.connect(worker.run)
        worker.image.connect(gui.update_frame)
        worker_thread.start()
        main = Main()
        main.main_window.show() 
        sys.exit(app.exec())
        
    
if __name__ == "__main__":
    main = Main()
    main.run()