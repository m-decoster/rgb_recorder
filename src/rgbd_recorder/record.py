import datetime
import os

from airo_camera_toolkit.cameras.multiprocess.multiprocess_rgbd_camera import MultiprocessRGBDPublisher
from airo_camera_toolkit.cameras.realsense.realsense import Realsense

from rgbd_recorder.video_recorder import MultiprocessVideoRecorder


def create_output_directory(output_dir: str) -> str:
    output_dir = output_dir
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d/%H-%M-%S")
    video_name = f"{timestamp}/color.mp4"
    video_path = os.path.join(output_dir, video_name)
    video_path = os.path.abspath(video_path)
    return video_path


def record_videos(output_dir: str) -> None:
    # Initialize the camera publishers.
    publisher = MultiprocessRGBDPublisher(Realsense, shared_memory_namespace="camera")

    # Start the publishers.
    publisher.start()
    video_path = create_output_directory(output_dir)

    # Initialize the camera subscribers (video recorders).
    recorder = MultiprocessVideoRecorder("camera", video_path)

    # Start recording.
    recorder.start()
    recorder.join()

    # Stop publishing camera data once the recorder is finished.
    publisher.stop()
