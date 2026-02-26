
# Pose Landmark Detection

A Python application for detecting and visualizing human pose landmarks using MediaPipe. Supports image, video, and live stream processing.

## Features

- **Image Processing**: Detect pose landmarks in static images
- **Video Processing**: Analyze pose landmarks in video files
- **Live Stream**: Real-time pose detection from webcam with optional recording
- **Visualization**: Draw pose landmarks and connections on output

## Requirements

- Python 3.8+
- MediaPipe
- OpenCV (cv2)
- NumPy

## Setup

1. Download the MediaPipe pose landmarker model file
2. Update the model path in `config.py`:
    ```python
    model_path = "path/to/pose_landmarker_heavy.task"
    ```

## Usage

Run the main application:
```bash
python main.py
```

Select processing mode:
- **Image**: Process a single image
- **Video**: Analyze a video file
- **Stream**: Live camera feed with optional recording

## Project Structure

- `main.py` - Entry point and user menu
- `image_landmarks.py` - Image processing module
- `video_landmark.py` - Video processing module
- `livestream_landmarks.py` - Live stream processing module
- `camerafeed.py` - Camera feed management
- `config.py` - Configuration settings

## Controls

- Press `Q` to quit during video or stream playback
