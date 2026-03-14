import time

import gui
from PySide6.QtCore import QTimer, Signal, Slot, QObject, QEventLoop, QThread
from mediapipe.tasks.python.components.containers import NormalizedLandmark
from mediapipe.tasks.python.vision import drawing_utils
from mediapipe.tasks.python.vision import drawing_styles
from mediapipe.tasks.python import vision
import numpy as np
import mediapipe as mp
import cv2 as cv
import kalman_smooth as ks
from collections import deque


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
options = None


class process(QThread):
    cap = Signal(cv.VideoCapture)
    image = Signal(np.ndarray, int)
    def __init__(self, process_type):
        super().__init__()
        self.process_type = process_type
        self.received_new_frame = False
        self.running = True
        self.ret = False
        self.frame = None
        self.result = PoseLandmarker
        self.smoothed_landmarks = []
        self.CAM_FPS = 0
        self.filters = [None]
        self.running_mode = None
        self.options = PoseLandmarkerOptions(None)
        self.model = r"C:\Users\joshu\Documents\projects\idk_man_the_fucking_shotput_coach_thing\pose_landmarker_heavy.task"
        self.frame_queue = deque(maxlen=2)
        self.x = -1

    @Slot(str)
    def route(self, process_type: str):
        match process_type.lower():

            case "image":
                self.VisionRunningMode = mp.tasks.vision.RunningMode.IMAGE
                self.options = PoseLandmarkerOptions(
                    base_options = BaseOptions(model_asset_path = self.model),
                    running_mode=self.VisionRunningMode.IMAGE
                )
                self.img_path = ""
                self.x = 0
                
            case "video":
                self.VisionRunningMode = mp.tasks.vision.RunningMode.VIDEO
                self.options = PoseLandmarkerOptions(
                    base_options = BaseOptions(model_asset_path=self.model),
                    running_mode=self.VisionRunningMode.VIDEO)
                self.x = 1
                
            case "livestream":
                self.VisionRunningMode = mp.tasks.vision.RunningMode.VIDEO
                self.options = PoseLandmarkerOptions(
                    base_options = BaseOptions(model_asset_path=self.model),
                    running_mode=self.VisionRunningMode.VIDEO,
                )
                self.x = 2
    

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

    @Slot(bool, np.ndarray)
    def new_frame(self, ret, frame):
        
        self.ret = ret

        if ret and frame is not None:
            self.frame_queue.append(frame)

    @Slot(int)
    def update_fps(self, fps):
        self.CAM_FPS = fps

    @Slot(str)
    def get_img_path(self, path: str):
        self.img_path = path
        
        
    def run(self):
        self.timestamp = 0
        try:
            self.route(self.process_type)
            self.landmarker = PoseLandmarker.create_from_options(self.options)
        except AttributeError as e:
            print(f"Error in run: {e}")
            return

        self.filters = [None]
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_one_frame)
        self.timer.start(16)
        
    def process_one_frame(self):

        if self.x == 0:
            self.timer = None
            mp_image = mp.Image.create_from_file(self.img_path)
            
            pose_landmarker_result = self.landmarker.detect(mp_image)
            
            np_image = np.array(mp_image.numpy_view(), dtype=np.uint8)
            np_image = cv.cvtColor(np_image, cv.COLOR_RGB2BGR)
            annotated_image = self.draw_landmarks_on_image(np_image, pose_landmarker_result.pose_landmarks)
            
            self.image.emit(annotated_image, 1)
            
            
            return
        else:
            
        
            if not self.frame_queue:
                return
            self.frame = self.frame_queue.pop()
            
            
            if not self.ret or self.frame is None:
                return


            height, width = self.frame.shape[:2]
            target = (1920,1080) if width > height else (1080,1920)

            if (width, height) != target:
                self.frame = cv.resize(self.frame, target)

            rgb_frame = cv.cvtColor(self.frame, cv.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            self.timestamp = time.perf_counter_ns() // 10000000

            if self.x == 1:
                result = self.landmarker.detect_for_video(mp_image, self.timestamp)
                if not result.pose_landmarks:
                    self.received_new_frame = False
                    return
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
            

            
            self.image.emit(annotated_frame, self.timestamp)
            self.received_new_frame = False