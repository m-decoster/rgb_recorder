import datetime
import os
from multiprocessing import Barrier
from typing import List

from airo_camera_toolkit.cameras.zed.zed import Zed
from pyzed import sl

from rgb_recorder.recording.video_recorder import MultiprocessVideoRecorder
from rgb_recorder.recording.zed_multiprocessing import ZedPublisher


def create_output_directory(output_dir: str) -> str:
    output_dir = output_dir
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d/%H-%M-%S")
    video_name = f"{timestamp}/color.mp4"
    video_path = os.path.join(output_dir, video_name)
    return video_path


def record_videos(serial_numbers: List[str], output_dir: str, fps: int,
                  resolution: tuple[int, int]) -> None:
    publishers = create_publishers(fps, resolution, serial_numbers)
    start_publishers(publishers)

    video_path = create_output_file(output_dir)

    # Barrier to synchronize recording start.
    barrier = Barrier(len(serial_numbers) + 1)  # One per camera, plus one for this process.

    recorders = create_recorders(barrier, serial_numbers, video_path)
    start_recorders(recorders)

    read_user_input(barrier)

    shutdown_recorders(recorders)
    shutdown_publishers(publishers)


def shutdown_publishers(publishers):
    # Stop the camera publishers.
    for publisher in publishers:
        publisher.stop()


def shutdown_recorders(recorders):
    # Wait for all recorders to finish.
    for recorder in recorders:
        recorder.shutdown_event.set()
    for recorder in recorders:
        recorder.join()


def read_user_input(barrier):
    do_stop = False
    started = False
    while not do_stop:
        if not started:
            response = input("Enter 'start' to start recording: ")
            if response == "start":
                started = True
                # Release the barrier to start recording (assuming all recorders are ready).
                barrier.wait()
        else:
            response = input("Enter 'stop' to stop recording: ")
            if response == "stop":
                do_stop = True


def start_recorders(recorders):
    # Start the recorders.
    for recorder in recorders:
        recorder.start()


def create_recorders(barrier, serial_numbers, video_path):
    # Initialize the camera subscribers (video recorders).
    recorders = []
    for serial_number in serial_numbers:
        recorder = MultiprocessVideoRecorder(serial_number,
                                             video_path.replace("color.mp4", f"{serial_number}/color.mp4"),
                                             multi_recorder_barrier=barrier)
        recorders.append(recorder)
    return recorders


def start_publishers(publishers):
    # Start the publishers.
    for publisher in publishers:
        publisher.start()


def create_publishers(fps, resolution, serial_numbers):
    # Initialize the camera publishers.
    publishers = []
    for serial_number in serial_numbers:
        publisher = ZedPublisher(Zed, camera_kwargs=dict(resolution=resolution,
                                                         serial_number=serial_number,
                                                         fps=fps,
                                                         depth_mode=sl.DEPTH_MODE.NONE),
                                 shared_memory_namespace=serial_number)
        publishers.append(publisher)
    return publishers
