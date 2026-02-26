import mediapipe as mp
from mediapipe.tasks.python.vision import drawing_utils
from mediapipe.tasks.python.vision import drawing_styles
from mediapipe.tasks.python import vision
import cv2 as cv
import numpy as np
import time
import config


BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode
saved = False
input_file_path = ""
output_file_path = ""

options = PoseLandmarkerOptions(
        base_options = BaseOptions(model_asset_path=config.model_path),
        running_mode=VisionRunningMode.VIDEO)

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

def run():
    with PoseLandmarker.create_from_options(options) as landmarker:
        cv.namedWindow("Landmarks", cv.WINDOW_KEEPRATIO)
        number_of_frames = 0
        cap = cv.VideoCapture(config.video_path)
        CAM_FPS = int(cap.get(cv.CAP_PROP_FPS))

        if(cap.isOpened()==False):
            print("Error opening video stream or file")

        while(cap.isOpened()):
            cv.namedWindow("Landmarks", cv.WINDOW_KEEPRATIO)
            ret, frame = cap.read()
            annotated_frame = np.zeros
            
            if ret:
                start_time = int(cap.get(cv.CAP_PROP_POS_MSEC))
                
                frame_resized = frame.astype(np.uint8)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_resized)
                
                
                
                pose_landmarker_result = landmarker.detect_for_video(mp_image, start_time)
                #smoothed_result = kalman_smooth.smooth_landmarks(pose_landmarker_result, frame_timestamp)
                
                
                annotated_frame = draw_landmarks_on_image(frame_resized, pose_landmarker_result)
                
                cv.imshow("Landmarks", annotated_frame)
                
                
            if cv.waitKey(1) == ord("q"):
                cap.release()
                cv.destroyAllWindows()
                print("Goodbye!")