import cv2 as cv
import numpy as np
import time
from datetime import datetime
import gui_handler
from PySide6.QtCore import Slot, QThread

class video_feed(QThread):

    def __init__(self):
        self.filming = False
        self.footage = {}
        self.fps = 0
        self.i = 0
        self.aspect_ratio = 0.0
        self.realtime_fps = 0.0
        self.recording = False
        self.out = cv.VideoWriter()
    
    Slot(list)
    def update_recording(self, recording, file_path):
        self.recording = recording
        self.file_path = file_path
    
    def __call__(self):
        self.getVideo()
 
    
    def getVideo(self):
        ONE_MORBILLION = 1_000_000
        cap = cv.VideoCapture(0)
        width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
        self.CAM_FPS = int(cap.get(cv.CAP_PROP_FPS))
        
        self.recording_window = gui_handler.RecordingWindow()
        self.recording_window.is_recording.connect(self.update_recording)  
        if(self.recording is True):
            out = cv.VideoWriter(self.file_path,
                                 cv.VideoWriter.fourcc('M', 'P', '4', 'V'),
                                 20,
                                 (width, height))
    
        start_timestamp = time.perf_counter_ns() // ONE_MORBILLION
        
        if not cap.isOpened():
            print("Cannot open camera")
            exit()
        
        self.aspect_ratio = width / height
        
        while self.filming:
            
            timestamp = time.perf_counter_ns() // ONE_MORBILLION
            world_clock = datetime.now()
            
            ret, frame, = cap.read()
            
            if not ret:
                print("Can't receive frame (stream end?) Exiting.")
                break
            
            if(self.recording is True):
                out.write(frame)
            self.footage[self.i] = [frame, timestamp, world_clock]
           
            self.i += 1
            
        cap.release()
        cv.destroyAllWindows()
        
        self.filming = False
        end_timestamp = int(time.perf_counter_ns())
        
        #Something for fps
        footage_keys = self.footage.keys()
        self.num_of_frame = len(footage_keys)
        end_timestamp = end_timestamp / ONE_MORBILLION 
        total_time = end_timestamp - start_timestamp
        
        self.realtime_fps = self.num_of_frame / total_time