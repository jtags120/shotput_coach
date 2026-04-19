import processing
import threading
import queue
import cv2 as cv
import os
import subprocess

class Main():
    def __init__(self, file, output):
        self.path = file
        self.output = output

    def run(self):
        self.start_processing_threads()
   
    def start_processing_threads(self):
        self.worker = processing.process(self.path)
        
        self.capture_worker = Capture(self.path, self.worker)
        self.capture_worker.start()
        self.worker.start()
        self.worker.join()
        self.capture_worker.join()
        
        output_path = os.path.join(self.output, 'output.mp4')
        temp_path = os.path.join(self.output, "temp.mp4")
        
        fourcc = cv.VideoWriter.fourcc(*'mp4v')
        writer = cv.VideoWriter(temp_path, fourcc, self.capture_worker.fps, self.worker.output_dimensions)
       
        

        while not self.worker.output_queue.empty():
            self.frame, self.timestamp, self.wall_clock = self.worker.output_queue.get()

            writer.write(self.frame)

        writer.release()
        
        subprocess.run([
            "ffmpeg", "-i", temp_path,
            "-vcodec", "libx264",
            "-f", "mp4",
            output_path
        ])
        
        os.remove(os.path.join(temp_path, "temp.mp4"))
        
class Capture(threading.Thread):
    
    def __init__(self, video_path, worker, mode="video"):
        super().__init__()
        self.frame_queue = queue.Queue()
        self.mode = mode
        self.video_path = video_path
        self.cap = None
        self.worker = worker

        if self.mode == "video":
            self.cap = cv.VideoCapture(self.video_path)
            
        elif self.mode == "livestream":
            self.cap = cv.VideoCapture(0)

            
    def run(self):
        
        if self.cap is None:
            return

        if not self.cap.isOpened():
            print(f"Failed to open capture: {self.video_path or 'camera'}")
            return
        

        self.fps = int(self.cap.get(cv.CAP_PROP_FPS))
        while self.cap.isOpened():
                
            ret, frame = self.cap.read()
            if not ret:
                break
            self.worker.new_frame(ret, frame, self.fps)
                
        self.worker.frame_queue.put(None)
    
if __name__ == "__main__":
    main = Main(r"C:\Users\joshu\Videos\shotput\output.mp4", r"C:\Users\joshu\Videos\shotput")
    main.run()
