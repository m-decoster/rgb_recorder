import argparse
import multiprocessing

from rgbd_recorder.record import record_videos

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--serial-numbers", nargs='+', type=str, required=True)
    parser.add_argument("-o", "--output-dir", type=str, default="output")
    parser.add_argument("-d", "--duration", type=float, required=True)

    args = parser.parse_args()

    multiprocessing.set_start_method("spawn")

    record_videos(args.serial_numbers, args.duration, args.output_dir)
