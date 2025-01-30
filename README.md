# rgbd_recorder

Record RGB streams from multiple Zed cameras with airo-mono.

## Installation

Use Anaconda:

```bash
conda env create -f environment.yaml
```

Follow the instructions of the `airo-camera-toolkit` package to ensure that you can use the Zed camera.
These instructions are available [here](https://github.com/airo-ugent/airo-mono/blob/main/airo-camera-toolkit/airo_camera_toolkit/cameras/zed/installation.md).

## Usage

Using the graphical user interface:

```bash
python -m rgbd_recorder.ui
```

Any entries you make in the fields will be stored in a `config.ini` file in the current working directory, to save
you time when you run the application again.

Using the CLI:

```bash
python -m rgbd_recorder.cli --serial-numbers $SERIAL_NUMBERS [-o $OUTPUT_DIR] [--fps $FPS] [--resolution $RESOLUTION]
```

Pass the serial numbers of your connected Zed cameras as a list of strings.
The output directory is optional and defaults to `"output"` in the current working directory.

The FPS is optional and defaults to `60`.  
The resolution is optional and defaults to `1280 720`. Valid values are:

- `2208 1242`
- `1920 1080`
- `1280 720`
- `672 376`

Not all combinations of FPS and resolution are supported. See the [Zed documentation](https://www.stereolabs.com/docs/video/camera-controls/) for more information.

For example, to record data from 2 cameras at 1080p@30fps:

```bash
python -m rgbd_recorder.cli --serial-numbers 35357320 34670760 --resolution 1920 1080 --fps 30
```

When all publishers and recorders have been created, the program will query you to enter "start" in the terminal.
This starts the recording. To stop the recording, enter "stop" in the terminal.
This will stop the recording and save the data to the output directory.

## Camera calibration

This package supports stereo camera extrinsics calibration. To perform calibration, you need:

- The serial numbers of two of the cameras
- [A ChArUcO board with the following dimensions](https://github.com/airo-ugent/airo-mono/blob/main/airo-camera-toolkit/docs/calib.io_charuco_300x220_5x7_40_31_DICT_4X4.pdf):
  - 5x7 squares
  - 40mm square size
  - 31mm marker size
  - ArUcO DICT_4x4_250 dictionary

You can use the script `stereo_calibration.py` to calibrate the cameras. This script will guide you through the calibration process.

```bash
python -m rgbd_recorder.stereo_calibration --serial-numbers $SERIAL_NUMBERS --output $OUTPUT_DIRECTORY
```

To perform calibration, take your ChArUcO board and move it around in front of the cameras.
When you have a steady pose where the board is properly visible in both cameras, press `s` to capture the image.
When you have captured enough images, press `q` to stop collecting data.
The script will then show the detected ArUcO corners on both images and collect the necessary data to perform calibration.
Press any key to loop through the images.
The script will then calibrate the cameras and save the calibration data to the output directory, while also logging it to the terminal.
The calibration data is expressed as the transformation matrix from one camera to another. The frame of the Zed camera
is defined as described [here](https://www.stereolabs.com/docs/positional-tracking/coordinate-frames#selecting-a-coordinate-system)
and shown in this image (source: above link).  
![zed_frame.png](https://docs.stereolabs.com/positional-tracking/images/zed_right_handed.jpg)

Per calibration run, the following information is written to disk:
- The transformation matrix from camera 1 to camera 2
- The intrinsics of camera 1
- The intrinsics of camera 2
- The pose of camera 1's right view with respect to the left view
- The pose of camera 2's right view with respect to the left view

You should consider one camera to be the world origin. Then, if you have more than two cameras, make sure to perform the calibration for
as many camera pairs as needed to be able to express all camera frames with respect to the world origin.
