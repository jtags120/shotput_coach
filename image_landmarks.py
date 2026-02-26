import mediapipe as mp
from mediapipe.tasks.python.vision import drawing_utils
from mediapipe.tasks.python.vision import drawing_styles
from mediapipe.tasks.python import vision
import numpy as np
import cv2 as cv
import config


BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = PoseLandmarkerOptions(
    base_options = BaseOptions(model_asset_path=config.model_path),
    running_mode=VisionRunningMode.IMAGE)

def draw_landmarks_on_image(rgb_image, result):
    annotated_image = np.copy(rgb_image)

    pose_landmark_style = drawing_styles.get_default_pose_landmarks_style()
    pose_connection_style = drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=2)
        
    for landmark_list in result:
        if annotated_image is not None:    
            drawing_utils.draw_landmarks(
                image=annotated_image,
                landmark_list=landmark_list,
                connections=vision.PoseLandmarksConnections.POSE_LANDMARKS,
                landmark_drawing_spec=pose_landmark_style,
                connection_drawing_spec=pose_connection_style)

    return annotated_image

def run():
    with PoseLandmarker.create_from_options(options) as landmarker:
        image = mp.Image.create_from_file(fr"{config.image_path}")
        pose_result = landmarker.detect(image)
        pose_landmarks = pose_result.pose_landmarks
        
        np_image = image.numpy_view()  # returns RGB np array
        bgr_image = cv.cvtColor(np_image, cv.COLOR_RGB2BGR)  # convert for OpenCV display

        landmark_image = draw_landmarks_on_image(bgr_image, pose_landmarks)

        cv.imshow("Test", landmark_image)
        cv.waitKey(0)
        cv.destroyAllWindows()