import argparse
import multiprocessing

from pyzed import sl

from rgbd_recorder.record import record_videos

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--serial-numbers", nargs='+', type=str, required=True)
    parser.add_argument("-o", "--output-dir", type=str, default="output")
    parser.add_argument("-d", "--duration", type=float, required=True)
    parser.add_argument("-m", "--depth-mode", type=str, default="ULTRA")
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--resolution", nargs=2, type=int, default=[1280, 720])

    args = parser.parse_args()

    multiprocessing.set_start_method("spawn")

    depth_mode = getattr(sl.DEPTH_MODE, args.depth_mode)
    resolution = tuple(args.resolution)

    record_videos(args.serial_numbers, args.duration, args.output_dir, depth_mode, args.fps, resolution)
