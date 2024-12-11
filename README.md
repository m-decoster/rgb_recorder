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

Using the graphical user interface:

```bash
python -m rgbd_recorder.ui
```

Any entries you make in the fields will be stored in a `config.ini` file in the current working directory, to save
you time when you run the application again.

Using the CLI:

```bash
python -m rgbd_recorder.cli --serial-numbers $SERIAL_NUMBERS -d $DURATION_SECONDS [-o $OUTPUT_DIR] [-m $DEPTH_MODE] [--fps $FPS] [--resolution $RESOLUTION]
```

Pass the serial numbers of your connected Zed cameras as a list of strings.
The duration of the recording is specified in seconds.
The output directory is optional and defaults to `"output"` in the current working directory.
The depth mode is optional and defaults to `"ULTRA"`. Valid values are:
- `PERFORMANCE`
- `QUALITY`
- `ULTRA`
- `NEURAL`

The FPS is optional and defaults to `60`.  
The resolution is optional and defaults to `1280 720`. Valid values are:

- `2208 1242`
- `1920 1080`
- `1280 720`
- `672 376`

Not all combinations of FPS and resolution are supported. See the [Zed documentation](https://www.stereolabs.com/docs/video/camera-controls/) for more information.

For example, to record 2 seconds of data from 2 cameras at 1080p@30fps with performance depth mode:

```bash
python -m rgbd_recorder.cli --serial-numbers 35357320 34670760 -d 2 --resolution 1920 1080 --fps 30 -m PERFORMANCE
```