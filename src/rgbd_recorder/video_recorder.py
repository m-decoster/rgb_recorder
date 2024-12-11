import gzip
import multiprocessing
import os
import time
from multiprocessing import Process
from typing import Optional

import cv2
import numpy as np
from airo_camera_toolkit.cameras.multiprocess.multiprocess_rgbd_camera import MultiprocessRGBDReceiver
from airo_typing import PointCloud
from loguru import logger


class NumpyWriter:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data = []

    def write(self, data: np.ndarray):
        self.data.append(data)

    def save(self):
        f = gzip.GzipFile(self.file_path, "w")
        np.save(file=f, arr=np.stack(self.data))
        f.close()

        logger.info(f"Saved data to {self.file_path}")


class PointCloudWriter:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data = {
            "points": [],
            "colors": []
        }

    def write(self, pcd: PointCloud):
        self.data["points"].append(pcd.points)
        self.data["colors"].append(pcd.colors)

    def save(self):
        self.data["points"] = np.stack(self.data["points"])
        self.data["colors"] = np.stack(self.data["colors"])

        f = gzip.GzipFile(self.file_path.replace('pcd.npy.gz', 'pcd_points.npy.gz'), "w")
        np.save(file=f, arr=self.data["points"])
        f.close()

        f = gzip.GzipFile(self.file_path.replace('pcd.npy.gz', 'pcd_colors.npy.gz'), "w")
        np.save(file=f, arr=self.data["colors"])
        f.close()

        logger.info(f"Saved data to {self.file_path}")


class MultiprocessVideoRecorder(Process):
    """Based on airo-mono example: https://github.com/airo-ugent/airo-mono/blob/main/airo-camera-toolkit/airo_camera_toolkit/cameras/multiprocess/multiprocess_video_recorder.py"""
    def __init__(
            self,
            shared_memory_namespace: str,
            duration_seconds: float,
            video_path: str,
            fill_missing_frames: bool = True,
            multi_recorder_barrier: Optional[multiprocessing.Barrier] = None,
    ):
        super().__init__(daemon=True)
        self._shared_memory_namespace = shared_memory_namespace
        self.shutdown_event = multiprocessing.Event()
        self.fill_missing_frames = fill_missing_frames
        self.duration = duration_seconds
        self._multi_recorder_barrier = multi_recorder_barrier

        self._video_path = video_path

    def start(self) -> None:
        super().start()

    def run(self) -> None:
        if self._multi_recorder_barrier is not None:
            logger.info("Waiting for barrier")
            self._multi_recorder_barrier.wait()
            logger.info("Barrier released")

        os.makedirs(os.path.dirname(self._video_path), exist_ok=False)

        receiver = MultiprocessRGBDReceiver(self._shared_memory_namespace)
        camera_fps = receiver.fps_shm_array[0]
        camera_period = 1 / camera_fps

        height, width, _ = receiver.rgb_shm_array.shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(self._video_path, fourcc, camera_fps, (width, height))

        depth_map_writer = NumpyWriter(self._video_path.replace("color.mp4", "depth_map.npy.gz"))
        depth_image_writer = cv2.VideoWriter(self._video_path.replace("color.mp4", "depth_image.mp4"), fourcc,
                                             camera_fps,
                                             (width, height))
        pcd_writer = PointCloudWriter(self._video_path.replace("color.mp4", "pcd.npy.gz"))

        logger.info(f"Recording video to {self._video_path}")

        image_previous = receiver.get_rgb_image_as_int()
        depth_map_previous = receiver.get_depth_map()
        depth_image_previous = receiver.get_depth_image()
        pcd_previous = receiver.get_colored_point_cloud()
        timestamp_prev_frame = receiver.get_current_timestamp()
        video_writer.write(cv2.cvtColor(image_previous, cv2.COLOR_RGB2BGR))
        depth_map_writer.write(depth_map_previous)
        depth_image_writer.write(depth_image_previous)
        pcd_writer.write(pcd_previous)
        n_consecutive_frames_dropped = 0

        start_time = time.time()
        while not self.shutdown_event.is_set():
            timestamp_receiver = receiver.get_current_timestamp()

            if timestamp_receiver <= timestamp_prev_frame:
                time.sleep(0.00001)  # Prevent busy waiting
                continue

            # New frame arrived
            image_rgb_new = receiver._retrieve_rgb_image_as_int()
            depth_map_new = receiver._retrieve_depth_map()
            depth_image_new = receiver._retrieve_depth_image()
            pcd_new = receiver._retrieve_colored_point_cloud()

            timestamp_difference = timestamp_receiver - timestamp_prev_frame
            missed_frames = int(timestamp_difference / camera_period) - 1

            if missed_frames > 0:
                logger.warning(f"Missed {missed_frames} frames (fill_missing_frames = {self.fill_missing_frames}).")

                if self.fill_missing_frames:
                    image_fill = cv2.cvtColor(image_previous, cv2.COLOR_RGB2BGR)
                    depth_map_fill = depth_map_previous
                    depth_image_fill = depth_image_previous
                    pcd_fill = pcd_previous
                    for _ in range(missed_frames):
                        video_writer.write(image_fill)
                        depth_map_writer.write(depth_map_fill)
                        depth_image_writer.write(depth_image_fill)
                        pcd_writer.write(pcd_fill)
                        n_consecutive_frames_dropped += 1

            timestamp_prev_frame = timestamp_receiver
            image_previous = image_rgb_new
            depth_map_previous = depth_map_new
            depth_image_previous = depth_image_new
            pcd_previous = pcd_new

            image = cv2.cvtColor(image_rgb_new, cv2.COLOR_RGB2BGR)

            video_writer.write(image)
            depth_map_writer.write(depth_map_new)
            depth_image_writer.write(depth_image_new)
            pcd_writer.write(pcd_new)

            if time.time() - start_time > self.duration:
                break

        logger.info("Video recorder has detected shutdown event. Releasing video_writer.")
        video_writer.release()
        logger.info("Writing depth map. This can take a lot of time! Be patient.")
        depth_map_writer.save()
        logger.info("Writing point cloud. This can take a lot of time! Be patient.")
        pcd_writer.save()
        logger.info(f"Video saved to {self._video_path}")
