import configparser
import multiprocessing
import os
import sys
import tkinter as tk
import tkinter.scrolledtext as scrolledtext

from datetime import datetime
from threading import Thread, Barrier, Event
from tkinter import messagebox

from loguru import logger

from rgb_recorder.recording.zed_sdk.export import export, OutputMode
from rgb_recorder.recording.zed_sdk.record import record_video

config = configparser.ConfigParser()
config_file = os.path.join(os.getcwd(), "svo_config.ini")


def load_config():
    if config.read(config_file):
        serial_numbers_entry.insert(0, config.get('Settings', 'serial_numbers', fallback=''))
        output_dir_entry.insert(0, config.get('Settings', 'output_dir', fallback='output'))


def save_config():
    config['Settings'] = {
        'serial_numbers': serial_numbers_entry.get(),
        'output_dir': output_dir_entry.get()
    }
    with open(config_file, 'w') as configfile:
        config.write(configfile)


start_button = None
stop_button = None
status_label = None
should_stop = Event()
svo_filenames = []


def should_stop_fn() -> bool:
    global should_stop
    return should_stop.is_set()


def create_output_file(output_dir: str, serial_number: str, timestamp: str) -> str:
    video_name = f"{timestamp}_{serial_number}.svo2"
    video_dir = os.path.join(output_dir, timestamp)
    os.makedirs(video_dir, exist_ok=True)
    video_path = os.path.join(video_dir, video_name)
    return video_path


def start():
    global start_button
    global stop_button
    global status_label
    global should_stop
    global svo_filenames

    should_stop.clear()
    svo_filenames = []

    serial_numbers = serial_numbers_entry.get().split()
    output_dir = output_dir_entry.get()

    if not serial_numbers:
        messagebox.showerror("Error", "Serial numbers are required.")
        return
    if not output_dir:
        messagebox.showerror("Error", "Output directory is required.")
        return

    logger.info(f"Starting {len(serial_numbers)} recording threads...")
    threads = []
    recording_barrier = Barrier(len(serial_numbers))
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    for serial_number in serial_numbers:
        video_path = create_output_file(output_dir, serial_number, timestamp)
        svo_filenames.append(video_path)
        t = Thread(target=record_video, args=(serial_number, video_path, should_stop_fn, recording_barrier))
        t.start()
        threads.append(t)

    # Disable start_button, enable stop_button
    start_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)

    # Set status label
    status_label.config(text="Recording... Do not close this window. Click 'Stop' to save recording.")


def stop():
    global start_button
    global stop_button
    global status_label
    global should_stop
    global svo_filenames

    stop_button.config(state=tk.DISABLED)

    logger.info("Stop button clicked. Stopping all camera recordings...")
    should_stop.set()

    start_button.config(state=tk.NORMAL)

    logger.info("Exporting video data...")
    status_label.config(text="Exporting... Do not close this window.")

    for svo_filename in svo_filenames:
        # Get extension.
        _, ext = os.path.splitext(svo_filename)

        logger.info(f"Exporting SVO file {svo_filename} to RGB videos... (1/2)")
        export(svo_filename, svo_filename.replace(ext, "_rgb_left.mp4"), OutputMode.RGB_LEFT)
        logger.info(f"Exporting SVO file {svo_filename} to RGB videos... (2/2)")
        export(svo_filename, svo_filename.replace(ext, "_rgb_right.mp4"), OutputMode.RGB_RIGHT)
        logger.info(f"Exporting SVO file {svo_filename} to depth video... (1/1)")
        export(svo_filename, svo_filename.replace(ext, "_depth.mp4"), OutputMode.DEPTH_LEFT)

    logger.info("Ready to record.")
    status_label.config(text="Ready to record.")

    save_config()


if __name__ == '__main__':
    multiprocessing.set_start_method('spawn')

    app = tk.Tk()
    app.title("RGB Recorder")

    tk.Label(app, text="Serial Numbers (space-separated):").grid(row=0, column=0, sticky=tk.W)
    serial_numbers_entry = tk.Entry(app, width=50)
    serial_numbers_entry.grid(row=0, column=1)

    tk.Label(app, text="Output Directory:").grid(row=1, column=0, sticky=tk.W)
    output_dir_entry = tk.Entry(app, width=50)
    output_dir_entry.grid(row=1, column=1)

    start_button = tk.Button(app, text="Start", command=start)
    start_button.grid(row=2, column=0, columnspan=1)
    stop_button = tk.Button(app, text="Stop and export", command=stop)
    stop_button.grid(row=2, column=1, columnspan=1)
    stop_button.config(state=tk.DISABLED)

    status_label = tk.Label(app, text="")
    status_label.grid(row=3, column=0, columnspan=2)
    status_label.config(text="Ready to record.")

    load_config()
    app.mainloop()
