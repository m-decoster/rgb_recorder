import argparse
import datetime
import json
import os
import sys

import cv2
import numpy as np
from airo_camera_toolkit.calibration.fiducial_markers import AIRO_DEFAULT_ARUCO_DICT, \
    AIRO_DEFAULT_CHARUCO_BOARD, detect_aruco_markers, detect_charuco_corners
from airo_camera_toolkit.cameras.zed.zed import Zed
from airo_camera_toolkit.utils.image_converter import ImageConverter
from airo_dataset_tools.data_parsers.camera_intrinsics import CameraIntrinsics
from airo_dataset_tools.data_parsers.pose import Pose
from loguru import logger


def main(args):
    camera_1 = Zed(serial_number="31733653")
    camera_2 = Zed(serial_number="34670760")

    camera_frames_1 = []  # TODO images from camera 1
    camera_frames_2 = []  # TODO images from camera 2 (synchronized)

    # Capture multiple images from both cameras.
    cv2.namedWindow("frame1", cv2.WINDOW_NORMAL)
    cv2.namedWindow("frame2", cv2.WINDOW_NORMAL)

    logger.info("Press [s] to save a sample, [q] to quit.")

    MIN_NUM_SAMPLES = 3
    num_samples = 0
    while True:
        frame1 = camera_1.get_rgb_image_as_int()
        frame2 = camera_2.get_rgb_image_as_int()

        frame1_cv = ImageConverter.from_numpy_int_format(frame1).image_in_opencv_format
        frame2_cv = ImageConverter.from_numpy_int_format(frame2).image_in_opencv_format

        cv2.imshow("frame1", frame1_cv)
        cv2.imshow("frame2", frame2_cv)

        key = cv2.waitKey(1)
        if key == ord('s'):
            camera_frames_1.append(frame1_cv)
            camera_frames_2.append(frame2_cv)

            num_samples += 1
            logger.info(f"Collected {num_samples} (minimum: {MIN_NUM_SAMPLES}) samples.")
        if key == ord('q'):
            break

    if num_samples < MIN_NUM_SAMPLES:
        logger.error(f"Not enough samples collected. Need at least {MIN_NUM_SAMPLES} Exiting...")
        sys.exit(1)

    object_points = []
    image_points_1 = []
    image_points_2 = []

    logger.info("Showing collected samples... Press any key to advance to the next image.")
    for frame1, frame2 in zip(camera_frames_1, camera_frames_2):
        aruco_f1 = detect_aruco_markers(frame1, AIRO_DEFAULT_ARUCO_DICT)
        aruco_f2 = detect_aruco_markers(frame2, AIRO_DEFAULT_ARUCO_DICT)

        if aruco_f1 is None or aruco_f2 is None:
            logger.warning("No aruco markers found in one of the frames. Skipping...")
            continue

        charuco_corners_f1 = detect_charuco_corners(frame1, aruco_f1, AIRO_DEFAULT_CHARUCO_BOARD)
        charuco_corners_f2 = detect_charuco_corners(frame2, aruco_f2, AIRO_DEFAULT_CHARUCO_BOARD)

        if charuco_corners_f1 is None or charuco_corners_f2 is None:
            logger.warning("No charuco corners found in one of the frames. Skipping...")
            continue

        frame1_charuco = cv2.aruco.drawDetectedCornersCharuco(frame1.copy(), np.array(charuco_corners_f1.corners),
                                                              np.array(charuco_corners_f1.ids), (255, 255, 0))
        frame2_charuco = cv2.aruco.drawDetectedCornersCharuco(frame2.copy(), np.array(charuco_corners_f2.corners),
                                                              np.array(charuco_corners_f2.ids), (255, 255, 0))

        cv2.imshow("frame1", frame1_charuco)
        cv2.imshow("frame2", frame2_charuco)

        # Check which corner IDs were detected by both cameras, and keep only those.
        common_ids = np.array(sorted(list(set(charuco_corners_f1.ids.squeeze().tolist()).intersection(
            set(charuco_corners_f2.ids.squeeze().tolist())))))
        common_corners_1 = np.stack([charuco_corners_f1.corners[i] for i in range(len(charuco_corners_f1.ids)) if
                                     charuco_corners_f1.ids[i, 0] in common_ids])
        common_corners_2 = np.stack([charuco_corners_f2.corners[i] for i in range(len(charuco_corners_f2.ids)) if
                                     charuco_corners_f2.ids[i, 0] in common_ids])

        obj_points, imagep_1 = cv2.aruco.getBoardObjectAndImagePoints(AIRO_DEFAULT_CHARUCO_BOARD, common_corners_1,
                                                                      common_ids)
        _obj_points, imagep_2 = cv2.aruco.getBoardObjectAndImagePoints(AIRO_DEFAULT_CHARUCO_BOARD, common_corners_2,
                                                                       common_ids)

        object_points.append(obj_points)
        image_points_1.append(imagep_1)
        image_points_2.append(imagep_2)

        cv2.waitKey(0)

    camera_matrix_1 = camera_1.intrinsics_matrix()
    camera_matrix_2 = camera_2.intrinsics_matrix()

    width, height = camera_1.resolution

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.0001)

    print("Obj points")
    print(object_points)
    print("Image points 1")
    print(image_points_1)
    print("Image points 2")
    print(image_points_2)

    rmse, _, _, _, _, R_C1_C2, T_C1_C2, _, _ = cv2.stereoCalibrate(object_points, image_points_1, image_points_2,
                                                                   camera_matrix_1, None,
                                                                   camera_matrix_2, None, (width, height),
                                                                   criteria=criteria,
                                                                   flags=cv2.CALIB_FIX_INTRINSIC)

    logger.info(f"Calibration output:\nRMSE={rmse}\nR_C1_C2={R_C1_C2}\nT_C1_C2={T_C1_C2}")

    X_C1_C2 = np.eye(4)
    X_C1_C2[:3, :3] = R_C1_C2
    X_C1_C2[:3, 3] = T_C1_C2.squeeze()

    output_dir = args.output_dir + f"_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    os.makedirs(output_dir)
    output_file = os.path.join(output_dir,
                               "camera_{0}_to_camera_{1}.json".format(camera_2.serial_number, camera_1.serial_number))
    with open(output_file, "w") as f:
        json.dump(Pose.from_homogeneous_matrix(X_C1_C2).model_dump(), f, indent=4)
    logger.info(f"Wrote calibration data to {output_file}.")

    # Save also the intrinsics, and the extrinsics of individual cameras' sensors.
    save_camera_intrinsics(camera_1, output_dir)
    save_camera_pose_right_in_left_view(camera_1, output_dir)
    save_camera_intrinsics(camera_2, output_dir)
    save_camera_pose_right_in_left_view(camera_2, output_dir)


def save_camera_pose_right_in_left_view(camera_1, output_dir):
    camera_1_right_in_left_file = os.path.join(output_dir, f"pose_right_in_left_view_{camera_1.serial_number}.json")
    with open(camera_1_right_in_left_file, "w") as f:
        json.dump(Pose.from_homogeneous_matrix(camera_1.pose_of_right_view_in_left_view).model_dump(), f, indent=4)


def save_camera_intrinsics(camera_1, output_dir):
    intrinsics_file = os.path.join(output_dir, f"intrinsics_{camera_1.serial_number}.json")
    resolution = camera_1.resolution
    intrinsics = camera_1.intrinsics_matrix()
    camera_intrinsics = CameraIntrinsics.from_matrix_and_resolution(intrinsics, resolution)
    with open(intrinsics_file, "w") as f:
        json.dump(camera_intrinsics.model_dump(exclude_none=True), f, indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-o", "--output-dir", type=str, default="calibration_data")

    args = parser.parse_args()

    main(args)
