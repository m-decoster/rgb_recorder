# rgb_recorder

Record RGB streams from multiple Zed cameras with airo-mono.

## Installation

Use Anaconda:

```bash
conda env create -f environment.yaml
```

Follow the instructions of the `airo-camera-toolkit` package to ensure that you can use the Zed camera.
These instructions are
available [here](https://github.com/airo-ugent/airo-mono/blob/main/airo-camera-toolkit/airo_camera_toolkit/cameras/zed/installation.md).

## Usage

All you need to do is run

```bash
python -m rgb_recorder.recording.zed_sdk.ui
```

and then click "Start". When you want to stop the recording, click "Stop" and wait until all videos have been exported
to MP4 files. This can take some time, be patient.

You can check the terminal for debugging and other output.

There will be four output files per connected camera:

- `<serial_number>.svo2`: The raw Zed SVO2 file. This can be opened in the `ZED_Explorer` application.
- `<serial_number>_color.mp4`: The left and right RGB views.
- `<serial_number>_depth.mp4`: The left RGB and depth views.

### Legacy

**The below instructions refer to an older version of the package, which works fine under Ubuntu but not under Windows.
**

Using the graphical user interface:

```bash
python -m rgb_recorder.recording.ui
```

Any entries you make in the fields will be stored in a `config.ini` file in the current working directory, to save
you time when you run the application again.

Using the CLI:

```bash
python -m rgb_recorder.recording.cli --serial-numbers $SERIAL_NUMBERS [-o $OUTPUT_DIR] [--fps $FPS] [--resolution $RESOLUTION]
```

Pass the serial numbers of your connected Zed cameras as a list of strings.
The output directory is optional and defaults to `"output"` in the current working directory.

The FPS is optional and defaults to `60`.  
The resolution is optional and defaults to `1280 720`. Valid values are:

- `2208 1242`
- `1920 1080`
- `1280 720`
- `672 376`

Not all combinations of FPS and resolution are supported. See
the [Zed documentation](https://www.stereolabs.com/docs/video/camera-controls/) for more information.

For example, to record data from 2 cameras at 1080p@30fps:

```bash
python -m rgb_recorder.recording.cli --serial-numbers 35357320 34670760 --resolution 1920 1080 --fps 30
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

You can use the `calibration` package to calibrate the cameras. This script will guide you through the calibration
process.

```bash
python -m rgb_recorder.calibration.cli --serial-numbers $SERIAL_NUMBERS --output $OUTPUT_DIRECTORY
```

A user interface is also provided:

```bash
python -m rgb_recorder.calibration.ui
```

To perform calibration, take your ChArUcO board and move it around in front of the cameras.
When you have a steady pose where the board is properly visible in both cameras, press `s` to capture the image.
When you have captured enough images, press `q` to stop collecting data.
The script will then show the detected ArUcO corners on both images and collect the necessary data to perform
calibration.
Press any key to loop through the images.
The script will then calibrate the cameras and save the calibration data to the output directory, while also logging it
to the terminal.
The calibration data is expressed as the transformation matrix from one camera to another. The frame of the Zed camera
is defined as
described [here](https://www.stereolabs.com/docs/positional-tracking/coordinate-frames#selecting-a-coordinate-system)
and shown in this image (source: above link).  
![zed_frame.png](https://docs.stereolabs.com/positional-tracking/images/zed_right_handed.jpg)

Per calibration run, the following information is written to disk:

- The transformation matrix from camera 1 to camera 2
- The intrinsics of camera 1
- The intrinsics of camera 2
- The pose of camera 1's right view with respect to the left view
- The pose of camera 2's right view with respect to the left view

You should consider one camera to be the world origin. Then, if you have more than two cameras, make sure to perform the
calibration for
as many camera pairs as needed to be able to express all camera frames with respect to the world origin.
