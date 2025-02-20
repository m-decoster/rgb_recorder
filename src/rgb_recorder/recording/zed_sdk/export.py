import enum
import os
import sys

import cv2
import numpy as np
import pyzed.sl as sl
from loguru import logger


class OutputMode(enum.Enum):
    RGB_LEFT = 0
    RGB_RIGHT = 1
    DEPTH_LEFT = 2


def progress_bar(percent_done, bar_length=50):
    # Display a progress bar
    done_length = int(bar_length * percent_done / 100)
    bar = '=' * done_length + '-' * (bar_length - done_length)
    sys.stdout.write('[%s] %i%s\r' % (bar, percent_done, '%'))
    sys.stdout.flush()


def open_camera(init: sl.InitParameters) -> sl.Camera:
    zed = sl.Camera()
    err = zed.open(init)
    if err != sl.ERROR_CODE.SUCCESS:
        sys.stdout.write(repr(err))
        zed.close()
        exit()
    return zed


def initialize_sdk(input_file: str) -> sl.InitParameters:
    init_params = sl.InitParameters()
    init_params.set_from_svo_file(input_file)
    init_params.svo_real_time_mode = False
    init_params.coordinate_units = sl.UNIT.MILLIMETER
    return init_params


def close_camera(camera: sl.Camera):
    camera.close()


def export(input_file: str, output_file: str, output_mode: OutputMode):
    if not os.path.isfile(input_file):
        raise IOError("Input file does not exist: " + input_file)

    if os.path.isfile(output_file):
        raise IOError("Output file already exists: " + output_file)

    init = initialize_sdk(input_file)
    cam = open_camera(init)

    # Get camera properties.
    image_size = cam.get_camera_information().camera_configuration.resolution
    width = image_size.width
    height = image_size.height
    fps = max(cam.get_camera_information().camera_configuration.fps, 25)

    # Prepare side by side image container equivalent to CV_8UC4.
    svo_image_sbs_rgba = np.zeros((height, width, 4), dtype=np.uint8)

    # Prepare single image containers
    image = sl.Mat()

    # Create video writer with MPEG-4 part 2 codec
    video_writer = cv2.VideoWriter(output_file,
                                   cv2.VideoWriter_fourcc('M', '4', 'S', '2'),
                                   fps,
                                   (width, height))
    if not video_writer.isOpened():
        raise IOError("Could not open video writer for file: " + output_file)

    rt_param = sl.RuntimeParameters()
    nb_frames = cam.get_svo_number_of_frames()

    while True:
        err = cam.grab(rt_param)
        if err == sl.ERROR_CODE.SUCCESS:
            svo_position = cam.get_svo_position()

            if output_mode == OutputMode.RGB_LEFT:
                cam.retrieve_image(image, sl.VIEW.LEFT)
            elif output_mode == OutputMode.RGB_RIGHT:
                cam.retrieve_image(image, sl.VIEW.RIGHT)
            elif output_mode == OutputMode.DEPTH_LEFT:
                cam.retrieve_image(image, sl.VIEW.DEPTH)
            else:
                raise ValueError(f"Unsupported output mode: {output_mode}")

            svo_image_sbs_rgba[0:height, 0:width, :] = image.get_data()
            ocv_image_sbs_rgb = cv2.cvtColor(svo_image_sbs_rgba, cv2.COLOR_RGBA2RGB)
            video_writer.write(ocv_image_sbs_rgb)

            # Display progress
            progress_bar((svo_position + 1) / nb_frames * 100, 30)

        if err == sl.ERROR_CODE.END_OF_SVOFILE_REACHED:
            progress_bar(100, 30)
            logger.info("Reached end of file successfully.")
            break

    # Close the video writer
    video_writer.release()

    close_camera(cam)
