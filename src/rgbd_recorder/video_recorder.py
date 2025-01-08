import multiprocessing
import os
import time
from multiprocessing import Process
from typing import Optional

import cv2
from airo_camera_toolkit.cameras.multiprocess.multiprocess_rgbd_camera import MultiprocessRGBDReceiver
from loguru import logger


class MultiprocessVideoRecorder(Process):
    """Based on airo-mono example: https://github.com/airo-ugent/airo-mono/blob/main/airo-camera-toolkit/airo_camera_toolkit/cameras/multiprocess/multiprocess_video_recorder.py"""

    def __init__(
            self,
            shared_memory_namespace: str,
            video_path: str,
            fill_missing_frames: bool = True,
    ):
        super().__init__(daemon=True)
        self._shared_memory_namespace = shared_memory_namespace
        self.shutdown_event = multiprocessing.Event()
        self.fill_missing_frames = fill_missing_frames

        self._is_recording = False

        self._video_path = video_path

    def start(self) -> None:
        super().start()

    def run(self) -> None:
        os.makedirs(os.path.dirname(self._video_path), exist_ok=False)

        receiver = MultiprocessRGBDReceiver(self._shared_memory_namespace)
        camera_fps = receiver.fps_shm_array[0]
        camera_period = 1 / camera_fps

        height, width, _ = receiver.rgb_shm_array.shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(self._video_path, fourcc, camera_fps, (width, height))

        depth_image_writer = cv2.VideoWriter(self._video_path.replace("color.mp4", "depth_image.mp4"), fourcc,
                                             camera_fps,
                                             (width, height))

        logger.info(f"Recording video to {self._video_path}")

        image_previous = receiver.get_rgb_image_as_int()
        depth_image_previous = receiver.get_depth_image()
        timestamp_prev_frame = receiver.get_current_timestamp()
        video_writer.write(cv2.cvtColor(image_previous, cv2.COLOR_RGB2BGR))
        depth_image_writer.write(depth_image_previous)
        n_consecutive_frames_dropped = 0

        cv2.namedWindow("frame", cv2.WINDOW_NORMAL)

        start_time = time.time()
        while not self.shutdown_event.is_set():
            timestamp_receiver = receiver.get_current_timestamp()

            if timestamp_receiver <= timestamp_prev_frame:
                time.sleep(0.00001)  # Prevent busy waiting
                continue

            # New frame arrived
            image_rgb_new = receiver._retrieve_rgb_image_as_int()
            depth_image_new = receiver._retrieve_depth_image()

            timestamp_difference = timestamp_receiver - timestamp_prev_frame
            missed_frames = int(timestamp_difference / camera_period) - 1

            if missed_frames > 0:
                logger.warning(f"Missed {missed_frames} frames (fill_missing_frames = {self.fill_missing_frames}).")

                if self.fill_missing_frames:
                    image_fill = cv2.cvtColor(image_previous, cv2.COLOR_RGB2BGR)
                    depth_image_fill = depth_image_previous
                    for _ in range(missed_frames):
                        video_writer.write(image_fill)
                        depth_image_writer.write(depth_image_fill)
                        n_consecutive_frames_dropped += 1

            timestamp_prev_frame = timestamp_receiver
            image_previous = image_rgb_new
            depth_image_previous = depth_image_new

            image = cv2.cvtColor(image_rgb_new, cv2.COLOR_RGB2BGR)

            image_frame = image.copy()
            recording_text = "Press [s] to start recording" if not self._is_recording else "Recording [s]"
            image_frame = cv2.putText(image_frame, recording_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            save_image_text = "Press [i] to save an image"
            image_frame = cv2.putText(image_frame, save_image_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

            cv2.imshow("frame", image_frame)
            key = cv2.waitKey(1)
            if key == ord('s'):
                if not self._is_recording:
                    self._is_recording = True
                else:
                    self._is_recording = False
                    break
            elif key == ord('i'):
                cv2.imwrite(self._video_path.replace("color.mp4", f"image_{time.time()}.png"), image)
                cv2.imwrite(self._video_path.replace("color.mp4", f"depth_image_{time.time()}.png"), depth_image_new)

            if self._is_recording:
                video_writer.write(image)
                depth_image_writer.write(depth_image_new)


        logger.info("Video recorder has detected shutdown event. Releasing video_writer.")
        video_writer.release()
        depth_image_writer.release()
        logger.info(f"Video saved to {self._video_path}")
