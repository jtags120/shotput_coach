import time
import threading
from mediapipe.tasks.python.components.containers import NormalizedLandmark
from mediapipe.tasks.python.vision import drawing_utils
from mediapipe.tasks.python.vision import drawing_styles
from mediapipe.tasks.python import vision
import numpy as np
import mediapipe as mp
import cv2 as cv
import kalman_smooth as ks
import queue


###Mix batch processing, thread pooling, and an initial 5 second buffer.
##Ensure batch_size and max_threads are memory and resource efficient.
#Use exponential increase in batch size and a max_threads for efficiency.
#Only for video and livestream tbh
# self.frames[end_start:]
# While self.frames is not empty:



BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode


class process(threading.Thread):
    def __init__(self, path: str):
        super().__init__()
        self.path = path
        self.running = True
        self.frame = None
        self.result = None
        self.smoothed_landmarks = []
        self.filters = [None]
        self.model = r"C:\Users\joshu\Documents\projects\shotput_coach\pose_landmarker_heavy.task"
        self.options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=self.model),
        running_mode=mp.tasks.vision.RunningMode.VIDEO)
        self.frame_queue = queue.Queue()
        self.output_queue = queue.Queue()

    def draw_landmarks_on_image(self, rgb_image, landmark_list):

        annotated_image = np.copy(rgb_image)

        pose_landmark_style = drawing_styles.get_default_pose_landmarks_style()
        pose_connection_style = drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=2)

        for pose_landmarks in landmark_list:
            drawing_utils.draw_landmarks(
                image=annotated_image,
                landmark_list=pose_landmarks,
                connections=vision.PoseLandmarksConnections.POSE_LANDMARKS,
                landmark_drawing_spec=pose_landmark_style,
                connection_drawing_spec=pose_connection_style)

        return annotated_image

    def new_frame(self, ret, frame, fps):
        self.CAM_FPS = fps

        if ret and frame is not None:
            self.frame_queue.put(frame)
    
    def stop(self):
        self.running = False
        
    def run(self):
        self.timestamp = 0
        try:
            self.landmarker = PoseLandmarker.create_from_options(self.options)
        except AttributeError as e:
            print(f"Error in run: {e}")
            return

        self.filters = [None]
        
        while self.process_one_frame():
            pass
        
    def process_one_frame(self):
        
        self.frame = self.frame_queue.get()
        if self.frame is None:
            return False

        height, width = self.frame.shape[:2]
        target = (1920,1080) if width > height else (1080,1920)

        if (width, height) != target:
            self.frame = cv.resize(self.frame, target)

        self.output_dimensions = (width, height)
        
        rgb_frame = cv.cvtColor(self.frame, cv.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        self.timestamp = time.perf_counter_ns() // 10000000

        
        result = self.landmarker.detect_for_video(mp_image, self.timestamp)
            
        if not result.pose_landmarks:
            return self.running
                
        self.result = result.pose_landmarks[0]

        if self.result and len(self.result) > 0:
                
            if self.filters[0] is None:
                self.filters = ks.make_filters(self.result, self.CAM_FPS)

            landmarks = self.result
            smoothed = ks.smooth_landmarks(landmarks, self.filters)
                
            self.smoothed_landmarks = [
                NormalizedLandmark(x=f.x[0], y=f.x[1], z=f.x[2], visibility=landmarks[i].visibility)
                for i, f in enumerate(smoothed)
            ]

        annotated_frame = self.draw_landmarks_on_image(self.frame, [self.smoothed_landmarks])
            
        world_time = time.time()
        self.output_queue.put((annotated_frame, self.timestamp, world_time))

        return self.running