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
