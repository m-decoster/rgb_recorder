import multiprocessing
import os
import time
from multiprocessing import Process
from typing import Optional

import cv2
from loguru import logger

from rgb_recorder.recording.zed_multiprocessing import ZedReceiver


class MultiprocessVideoRecorder(Process):
    """Based on airo-mono example: https://github.com/airo-ugent/airo-mono/blob/main/airo-camera-toolkit/airo_camera_toolkit/cameras/multiprocess/multiprocess_video_recorder.py"""

    def __init__(
            self,
            shared_memory_namespace: str,
            video_path: str,
            fill_missing_frames: bool = True,
            multi_recorder_barrier: Optional[multiprocessing.Barrier] = None,
    ):
        super().__init__(daemon=True)
        self._shared_memory_namespace = shared_memory_namespace
        self.shutdown_event = multiprocessing.Event()
        self.fill_missing_frames = fill_missing_frames
        self._multi_recorder_barrier = multi_recorder_barrier

        self._video_path_left = video_path.replace(".mp4", "_left.mp4")
        self._video_path_right = video_path.replace(".mp4", "_right.mp4")

    def start(self) -> None:
        super().start()

    def run(self) -> None:
        if self._multi_recorder_barrier is not None:
            logger.info("Waiting for barrier")
            self._multi_recorder_barrier.wait()
            logger.info("Barrier released")

        os.makedirs(os.path.dirname(self._video_path_left), exist_ok=False)

        receiver = ZedReceiver(self._shared_memory_namespace)
        camera_fps = receiver.fps_shm_array[0]
        camera_period = 1 / camera_fps

        height, width, _ = receiver.rgb_left_shm_array.shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer_left = cv2.VideoWriter(self._video_path_left, fourcc, camera_fps, (width, height))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer_right = cv2.VideoWriter(self._video_path_right, fourcc, camera_fps, (width, height))

        logger.info(f"Recording videos to {self._video_path_left} and {self._video_path_right}")

        image_previous_left, image_previous_right = receiver.get_rgb_image_as_int()
        timestamp_prev_frame = receiver.get_current_timestamp()
        video_writer_left.write(cv2.cvtColor(image_previous_left, cv2.COLOR_RGB2BGR))
        video_writer_right.write(cv2.cvtColor(image_previous_right, cv2.COLOR_RGB2BGR))
        n_consecutive_frames_dropped = 0

        while not self.shutdown_event.is_set():
            timestamp_receiver = receiver.get_current_timestamp()

            if timestamp_receiver <= timestamp_prev_frame:
                time.sleep(0.00001)  # Prevent busy waiting
                continue

            # New frame arrived
            image_rgb_new_left, image_rgb_new_right = receiver._retrieve_rgb_image_as_int()

            timestamp_difference = timestamp_receiver - timestamp_prev_frame
            missed_frames = int(timestamp_difference / camera_period) - 1

            if missed_frames > 0:
                logger.warning(f"Missed {missed_frames} frames (fill_missing_frames = {self.fill_missing_frames}).")

                if self.fill_missing_frames:
                    image_fill_left = cv2.cvtColor(image_previous_left, cv2.COLOR_RGB2BGR)
                    image_fill_right = cv2.cvtColor(image_previous_right, cv2.COLOR_RGB2BGR)
                    for _ in range(missed_frames):
                        video_writer_left.write(image_fill_left)
                        video_writer_right.write(image_fill_right)
                        n_consecutive_frames_dropped += 1

            timestamp_prev_frame = timestamp_receiver
            image_previous_left = image_rgb_new_left
            image_previous_right = image_rgb_new_right

            image_left = cv2.cvtColor(image_rgb_new_left, cv2.COLOR_RGB2BGR)
            image_right = cv2.cvtColor(image_rgb_new_right, cv2.COLOR_RGB2BGR)

            video_writer_left.write(image_left)
            video_writer_right.write(image_right)

        logger.info("Video recorder has detected shutdown event. Releasing video_writer_[left,right].")
        video_writer_left.release()
        video_writer_right.release()
        logger.info(f"Videos saved to {self._video_path_left} and {self._video_path_right}")
