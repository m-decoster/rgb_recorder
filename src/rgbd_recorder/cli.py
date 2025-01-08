import argparse
import multiprocessing

from pyzed import sl

from rgbd_recorder.record import record_videos

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-o", "--output-dir", type=str, default="output")

    args = parser.parse_args()

    multiprocessing.set_start_method("spawn")

    record_videos(args.output_dir)
