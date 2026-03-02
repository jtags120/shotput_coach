from PySide6.QtCore import QThread, Signal, Slot
from mediapipe.tasks.python.vision import drawing_utils
from mediapipe.tasks.python.vision import drawing_styles
from mediapipe.tasks.python import vision
import numpy as np
import mediapipe as mp
import config
import cv2 as cv
import processing.camerafeed as camerafeed
import processing.kalman_smooth
import gui_handler

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
    image = Signal(np.ndarray, int)
    def __init__(self, process_type: str):
        super().__init__()
        self.frames = []
        self.process_type = process_type
        self.recording = False
        
        self.route()

    def route(self):
        match self.process_type.lower():
            
            case "image":
                VisionRunningMode = mp.tasks.vision.RunningMode.IMAGE
                self.options = None
                self.x = 0
            case "video":
                VisionRunningMode = mp.tasks.vision.RunningMode
                self.options = PoseLandmarkerOptions(
                    base_options = BaseOptions(model_asset_path=config.model_path),
                    running_mode=VisionRunningMode.VIDEO)
                self.x = 1
            case "livestream":
                PoseLandmarkerResult = mp.tasks.vision.PoseLandmarkerResult
                VisionRunningMode = mp.tasks.vision.RunningMode.LIVE_STREAM
                self.options = PoseLandmarkerOptions(
                    base_options = BaseOptions(model_asset_path=config.model_path),
                    running_mode=VisionRunningMode.LIVE_STREAM,
                    result_callback=self.callback,
                )
                lil_guy = gui_handler.RecordingWindow()
                lil_guy.is_recording.connect(self.set_recording)
                self.x = 2
                
    def callback(self, result: PoseLandmarkerResult, output_image: mp.Image): # type: ignore
        global latest_frame 
    
        rgb_image = output_image.numpy_view()
        annotated_image = self.draw_landmarks_on_image(rgb_image, result)
        latest_frame = cv.cvtColor(annotated_image, cv.COLOR_RGB2BGR)
    
    @Slot(list)
    def set_recording(self, data: list):
        self.recording, self.file_path = data
                                                  
    def draw_landmarks_on_image(self, rgb_image, result):
        pose_landmarks_list = result.pose_landmarks
        annotated_image = np.copy(rgb_image)

        pose_landmark_style = drawing_styles.get_default_pose_landmarks_style()
        pose_connection_style = drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=2)

        for pose_landmarks in pose_landmarks_list:
            drawing_utils.draw_landmarks(
                image=annotated_image,
                landmark_list=pose_landmarks,
                connections=vision.PoseLandmarksConnections.POSE_LANDMARKS,
                landmark_drawing_spec=pose_landmark_style,
                connection_drawing_spec=pose_connection_style)

        return annotated_image
    
    
    def run(self):
        try:
            landmarker = PoseLandmarker.create_from_options(self.options)
            self.process(landmarker)
        except Exception as e:
            import traceback
            traceback.print_exc()
        return 
    
    @Slot(camerafeed.video_feed)
    def get_vid_object(self, vid_object: camerafeed.video_feed):
        self.vid_object = vid_object
    
    
            
            
    def process(self, landmarker, cap = cv.VideoCapture()):
        
        #Image
        if(self.x==0):
            image = mp.Image.create_from_file("")
            pose_result = landmarker.detect(image)
            pose_landmarks = pose_result.pose_landmarks
            
            np_image = image.numpy_view()

            annotated_image = self.draw_landmarks_on_image(np_image, pose_landmarks)
            
            return annotated_image
        
        
        
        ##Landmarker line(not really but its helping me conceptualize)
        try:
            self.cap = cap
            print("video path:", config.video_path)
            self.CAM_FPS = int(self.cap.get(cv.CAP_PROP_FPS))
            self.total_frames = int(self.cap.get(cv.CAP_PROP_FRAME_COUNT))
            print(f"FPS: {self.CAM_FPS}, total frames: {self.total_frames}")
            
            if(self.x == 2):
                vid_object.filming = True
                vid_object.thread.start()        
        
            if not cap.isOpened():
                return
            filters = processing.kalman_smooth.make_filters(result.pose_landmarks[0], self.CAM_FPS)
            while cap.isOpened():
                
                   
                ret, frame = cap.read()
                   
                if not ret or frame is None:
                    break
                start_time = int(cap.get(cv.CAP_PROP_POS_MSEC))
                    
                height, width = frame.shape[:2]
                if width > height:
                    frame = cv.resize(frame, (1920, 1080))
                else:
                    frame = cv.resize(frame, (1080, 1920))
                        
                rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

                if(self.x == 1):
                    result = landmarker.detect_for_video(mp_image, start_time)
                elif(self.x == 2):
                    result = landmarker.detect_async(mp_image, start_time)    
                    
                if  len(result.pose_landmarks) > 0:
                    landmarks = result.pose_landmarks[0]
                   
                    smoothed = processing.kalman_smooth.smooth_landmarks(landmarks, filters)
                                        
                    for i, filter in enumerate(smoothed):
                        landmarks[i].x = filter.x[0]
                        landmarks[i].y = filter.x[1]
                        landmarks[i].z = filter.x[2]
                else:
                    continue
                    
                annotated_frame = self.draw_landmarks_on_image(frame, result)

                    
                self.image.emit(annotated_frame, start_time)
                                
        except KeyboardInterrupt:
            if(self.x == 2):
                vid_object.filming = False
                vid_object.thread.join()
        
        
        
        
        
        
        
        
        

            
    