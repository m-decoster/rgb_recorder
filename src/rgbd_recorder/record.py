import datetime
import os
from multiprocessing import Barrier
from typing import List

from airo_camera_toolkit.cameras.multiprocess.multiprocess_rgbd_camera import MultiprocessRGBDPublisher
from airo_camera_toolkit.cameras.zed.zed import Zed
from pyzed import sl

from rgbd_recorder.video_recorder import MultiprocessVideoRecorder


def create_output_directory(output_dir: str) -> str:
    output_dir = output_dir
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d/%H-%M-%S")
    video_name = f"{timestamp}/color.mp4"
    video_path = os.path.join(output_dir, video_name)
    video_path = os.path.abspath(video_path)
    return video_path


def record_videos(serial_numbers: List[str], duration: float, output_dir: str, depth_mode: sl.DEPTH_MODE, fps: int, resolution: tuple[int, int]) -> None:
    # Initialize the camera publishers.
    publishers = []
    for serial_number in serial_numbers:
        publisher = MultiprocessRGBDPublisher(Zed, camera_kwargs=dict(resolution=resolution,
                                                                      serial_number=serial_number, fps=fps,
                                                                      depth_mode=depth_mode),
                                              shared_memory_namespace=serial_number)
        publishers.append(publisher)

    # Start the publishers.
    for publisher in publishers:
        publisher.start()
    video_path = create_output_directory(output_dir)

    # Barrier to synchronize recording start.
    barrier = Barrier(len(serial_numbers))

    # Initialize the camera subscribers (video recorders).
    recorders = []
    for serial_number in serial_numbers:
        recorder = MultiprocessVideoRecorder(serial_number, duration,
                                             video_path.replace("color.mp4", f"{serial_number}/color.mp4"),
                                             multi_recorder_barrier=barrier)
        recorders.append(recorder)

    # Start the recorders.
    for recorder in recorders:
        recorder.start()

    # Wait for all recorders to finish.
    for recorder in recorders:
        recorder.join()

    # Stop the camera publishers.
    for publisher in publishers:
        publisher.stop()
