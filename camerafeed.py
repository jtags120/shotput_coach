import cv2 as cv
import numpy as np
import threading
import time

class video_feed:

    def __init__(self):
        self.previous_frame = np.zeros((3,3), dtype=np.uint8)
        self.timestamp = 0
        self.filming = True
        self.thread
        
    def __call__(self):
        self.getVideo()
 
    def getVideo(self):
        cap = cv.VideoCapture(0)
        
        one_morbillion = 1_000_000
        start_timestamp = float(time.perf_counter_ns()) / one_morbillion

        if not cap.isOpened():
            print("Cannot open camera")
            exit()
        while self.filming:
            
            self.timestamp = float(time.perf_counter_ns()) / one_morbillion
            ret, frame, = cap.read()
            
            
            
            
            if not ret:
                print("Can't receive frame (stream end?) Exiting.")
                break
            self.previous_frame = frame
            # cv.imshow('Livestream', frame)
            # if cv.waitKey(1) == ord('q'):
            #     break
            
        cap.release()
        cv.destroyAllWindows()
        self.filming = False
        total_time = self.timestamp - start_timestamp 
        


vid_object=video_feed()

thread = threading.Thread(target=vid_object)

thread.start()