import argparse
import multiprocessing

from pyzed import sl

from rgbd_recorder.record import record_videos

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--serial-numbers", nargs='+', type=str, required=True)
    parser.add_argument("-o", "--output-dir", type=str, default="output")
    parser.add_argument("-d", "--duration", type=float, required=True)
    parser.add_argument("--fps", help="Supported resolutions: [15, 30, 60]", type=int, default=15)
    parser.add_argument("--resolution", help="Supported resolutions: [(2208, 1242), (1920, 1080), (1280, 720), (672, 376)]", nargs=2, type=int, default=[2208, 1242])

    args = parser.parse_args()

    multiprocessing.set_start_method("spawn")

    resolution = tuple(args.resolution)

    record_videos(args.serial_numbers, args.duration, args.output_dir, args.fps, resolution)
