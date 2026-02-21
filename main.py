import mediapipe as mp
from mediapipe.tasks.python.vision import drawing_utils
from mediapipe.tasks.python.vision import drawing_styles
from mediapipe.tasks.python import vision
import numpy as np
import camerafeed
import cv2 as cv

#This is mainly following the tutorial Google has on MediaPipe. Made a few 
#changes to ensure proper types were received by specific methods

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
PoseLandmarkerResult = mp.tasks.vision.PoseLandmarkerResult
VisionRunningMode = mp.tasks.vision.RunningMode
latest_frame = None

def print_result(result: PoseLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    global latest_frame
    
    rgb_image = output_image.numpy_view()
    annotated_image = draw_landmarks_on_image(rgb_image, result)
    latest_frame = cv.cvtColor(annotated_image, cv.COLOR_RGB2BGR)
    
    
    
    #print('pose landmarker result: {}'.format(result))
    
options = PoseLandmarkerOptions(
    base_options = BaseOptions(model_asset_path=r"C:\Users\joshu\Documents\idk_man_the_fucking_shotput_coach_thing\pose_landmarker_heavy.task"),
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=print_result)

def draw_landmarks_on_image(rgb_image, result):
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

vid_object = camerafeed.vid_object

with PoseLandmarker.create_from_options(options) as landmarker:
   
    while True:
        if(vid_object.filming is False):
            break
        frame_timestamp_ms = vid_object.
        frame = vid_object.previous_frame
       
        if frame is not None and frame.ndim == 3:
            
            rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            landmarker.detect_async(mp_image, frame_timestamp_ms)
            
        
        if latest_frame is not None:
            cv.imshow("Test", latest_frame)
        
        if cv.waitKey(1) == ord('q'):
            vid_object.filming = False
            quit()
    cv.destroyAllWindows()
