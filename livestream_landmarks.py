import mediapipe as mp
from mediapipe.tasks.python.vision import drawing_utils
from mediapipe.tasks.python.vision import drawing_styles
from mediapipe.tasks.python import vision
import numpy as np
import camerafeed
import cv2 as cv
import datetime
import config
#import kalman_smooth

    
BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
PoseLandmarkerResult = mp.tasks.vision.PoseLandmarkerResult
VisionRunningMode = mp.tasks.vision.RunningMode

latest_frame = None
recording = False

    
def callback(result: PoseLandmarkerResult, output_image: mp.Image, timestamp_ms: int): # type: ignore
    global latest_frame 
    
    rgb_image = output_image.numpy_view()
    annotated_image = draw_landmarks_on_image(rgb_image, result)
    latest_frame = cv.cvtColor(annotated_image, cv.COLOR_RGB2BGR)
        
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
    
def run(recording: bool):        
    options = PoseLandmarkerOptions(
        base_options = BaseOptions(model_asset_path=config.model_path),
        running_mode=VisionRunningMode.LIVE_STREAM,
        result_callback=callback,
        )
    
    vid_object = camerafeed.vid_object
    vid_object.recording = recording
    with PoseLandmarker.create_from_options(options) as landmarker:
        temp_i = -1
        try:
            cv.namedWindow("Test", cv.WINDOW_KEEPRATIO)

            vid_object.filming = True
            vid_object.thread.start()
            print("Press Q to end the stream!")
                
            while vid_object.filming:
                
                if(vid_object.i == 0):
                    continue
                
                i = vid_object.i - 1
                
                footage = vid_object.footage
                frame_info = footage.get(i)
                
                if frame_info is not None and (temp_i != i):
                    
                    frame = frame_info[0]
                    
                    frame_timestamp_ms = frame_info[1]
                    
                    timestamp = datetime.datetime.now()
                    format_timestamp = (timestamp.strftime('%Y-%m-%d %H:%M:%S'))
                    font = cv.FONT_HERSHEY_SIMPLEX
                    scale = 1.0
                    color = (255, 255, 255)
                    thickness = 1
        
                    height, width, _ = frame.shape
                    aspect_ratio = vid_object.aspect_ratio
                    height = int(round((width / aspect_ratio), 0))

                    (text_width, text_height), baseline = cv.getTextSize(format_timestamp,
                                                            font,
                                                            scale,
                                                            thickness)
                    x_offset = int(width * 0.05)
                    y_offset = int(height * 0.05)
                
                    org_x = int(width - text_width - x_offset)
                    org_y = int(height - y_offset)
        
                    cv.rectangle(
                        frame,
                        (org_x - 2, org_y - text_height - 2),
                        (org_x + text_width + 2, org_y + baseline + 2),
                        (0, 0, 0),
                        thickness = -1)
        
                    cv.putText(frame,
                            format_timestamp,
                            (org_x, org_y),
                            font,
                            scale,
                            color,
                            thickness)
                    
                    rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                    landmarker.detect_async(mp_image, frame_timestamp_ms)
                    
                    
                    if latest_frame is not None:
                        vid_object.out.write(latest_frame)
                        cv.imshow("Test", latest_frame)
                    
                temp_i = i
                
                if cv.waitKey(1) == ord('q'):
                    cv.destroyAllWindows()
                    vid_object.filming = False
                    vid_object.thread.join()
                    quit()
                
        except KeyboardInterrupt:
            vid_object.filming = False
        vid_object.thread.join()