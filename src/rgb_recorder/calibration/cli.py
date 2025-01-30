import argparse

from rgb_recorder.calibration.stereo_calibration import calibrate

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("serial_number_1", type=str, help="Serial number of the first camera.")
    parser.add_argument("serial_number_2", type=str, help="Serial number of the second camera.")
    parser.add_argument("-o", "--output-dir", type=str, default="calibration_data", help="Output directory.")

    args = parser.parse_args()

    calibrate(args)
