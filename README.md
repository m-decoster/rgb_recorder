# rgbd_recorder

Record RGB and depth streams from Zed cameras with airo-mono.

## Installation

Use Anaconda:

```bash
conda env create -f environment.yaml
```

Follow the instructions of the `airo-camera-toolkit` package to ensure that you can use the Zed camera.
These instructions are available [here](https://github.com/airo-ugent/airo-mono/blob/main/airo-camera-toolkit/airo_camera_toolkit/cameras/zed/installation.md).

## Usage

Using the CLI:

```bash
python -m rgbd_recorder.cli --serial-numbers [your serial numbers here] -d [duration in seconds] -o [output directory]
```

Pass the serial numbers of your connected Zed cameras as a list of strings.

For example, to record 2 seconds of data from 2 cameras:

```bash
python -m rgbd_recorder.cli --serial-numbers 35357320 34670760 -d 2
```