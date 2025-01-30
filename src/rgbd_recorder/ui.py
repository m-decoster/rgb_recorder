import configparser
import multiprocessing
import tkinter as tk
from multiprocessing import Barrier
from tkinter import messagebox

from rgbd_recorder.record import create_publishers, start_publishers, create_output_directory, create_recorders, \
    start_recorders, shutdown_publishers, shutdown_recorders

config = configparser.ConfigParser()
config_file = 'config.ini'


def load_config():
    if config.read(config_file):
        serial_numbers_entry.insert(0, config.get('Settings', 'serial_numbers', fallback=''))
        output_dir_entry.insert(0, config.get('Settings', 'output_dir', fallback='output'))
        fps_entry.insert(0, config.get('Settings', 'fps', fallback='60'))
        resolution_var.set(config.get('Settings', 'resolution', fallback='1280 720'))


def save_config():
    config['Settings'] = {
        'serial_numbers': serial_numbers_entry.get(),
        'output_dir': output_dir_entry.get(),
        'fps': fps_entry.get(),
        'resolution': resolution_var.get()
    }
    with open(config_file, 'w') as configfile:
        config.write(configfile)


publishers = []
recorders = []
start_button = None
stop_button = None
status_label = None


def start():
    global publishers
    global recorders
    global start_button
    global stop_button
    global status_label

    serial_numbers = serial_numbers_entry.get().split()
    output_dir = output_dir_entry.get()
    fps = int(fps_entry.get())
    resolution = tuple(int(x) for x in resolution_var.get().split(' '))

    if not serial_numbers:
        messagebox.showerror("Error", "Serial numbers are required.")
        return

    publishers = create_publishers(fps, resolution, serial_numbers)
    start_publishers(publishers)

    video_path = create_output_directory(output_dir)

    # Barrier to synchronize recording start.
    barrier = Barrier(len(serial_numbers))  # One per camera, plus one for this process.

    recorders = create_recorders(barrier, serial_numbers, video_path)
    start_recorders(recorders)

    # Disable start_button, enable stop_button
    start_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)

    # Set status label
    status_label.config(text="Recording... Do not close this window. Press 'Stop' to save recording.")


def stop():
    global recorders
    global publishers
    global start_button
    global stop_button
    global status_label

    shutdown_recorders(recorders)
    shutdown_publishers(publishers)

    # Enable start_button, disable stop_button
    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)

    # Clear status label
    status_label.config(text="")


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

    tk.Label(app, text="Duration (seconds):").grid(row=2, column=0, sticky=tk.W)
    duration_entry = tk.Entry(app, width=50)
    duration_entry.grid(row=2, column=1)

    tk.Label(app, text="FPS:").grid(row=4, column=0, sticky=tk.W)
    fps_entry = tk.Entry(app, width=50)
    fps_entry.grid(row=4, column=1)

    tk.Label(app, text="Resolution (width height):").grid(row=5, column=0, sticky=tk.W)
    resolution_var = tk.StringVar(value="1280 720")
    resolution_entry = tk.Entry(app, textvariable=resolution_var, width=50)
    resolution_entry.grid(row=5, column=1)

    start_button = tk.Button(app, text="Start", command=start)
    start_button.grid(row=6, column=0, columnspan=1)
    stop_button = tk.Button(app, text="Stop", command=stop)
    stop_button.grid(row=6, column=1, columnspan=1)
    stop_button.config(state=tk.DISABLED)

    status_label = tk.Label(app, text="")
    status_label.grid(row=7, column=0, columnspan=2)

    load_config()
    app.mainloop()
