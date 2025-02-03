from threading import Barrier
from typing import Callable

import pyzed.sl as sl
from loguru import logger


class Camera:
    def __init__(self, camera: sl.Camera):
        self.camera = camera
        self.runtime = sl.RuntimeParameters()
        self.frames_recorded = 0

    def grab(self) -> bool:
        return self.camera.grab(self.runtime) == sl.ERROR_CODE.SUCCESS


def initialize_sdk(camera_serial_number: str) -> sl.InitParameters:
    init = sl.InitParameters()
    init.camera_resolution = sl.RESOLUTION.HD2K
    init.camera_fps = 15
    init.set_from_serial_number(int(camera_serial_number))
    # init.depth_mode = sl.DEPTH_MODE.NONE  # Set configuration parameters for the ZED
    return init


def open_camera(init: sl.InitParameters, output_filename: str) -> sl.Camera:
    cam = sl.Camera()
    status = cam.open(init)
    if not status:
        raise RuntimeError("Could not open camera.")
    recording_param = sl.RecordingParameters(output_filename,
                                             sl.SVO_COMPRESSION_MODE.H264)  # Enable recording with the filename specified in argument
    err = cam.enable_recording(recording_param)
    if err != sl.ERROR_CODE.SUCCESS:
        raise RuntimeError("Could not enable recording.")
    return cam


def close_camera(camera: sl.Camera):
    camera.disable_recording()
    camera.close()


def record_video(camera_serial_number: str, filename: str, should_stop_fn: Callable[[], bool], start_barrier: Barrier):
    if not filename.endswith(".svo") and not filename.endswith(".svo2"):
        raise ValueError("Filename should be a .svo file but is not : ", filename)

    logger.info(f"Initializing SDK for camera with SN={camera_serial_number}...")
    init = initialize_sdk(camera_serial_number)
    cam = open_camera(init, filename)

    camera = Camera(cam)

    logger.info("Waiting for other cameras to get ready...")
    start_barrier.wait()  # Wait until all cameras are ready to start recording.
    logger.info("All cameras are ready, starting recording...")
    while not should_stop_fn():
        if camera.grab():
            camera.frames_recorded += 1
            print("Frame count: " + str(camera.frames_recorded), end="\r")

    logger.info(f"Recording stopped, closing camera with SN={camera_serial_number}...")
    close_camera(cam)
