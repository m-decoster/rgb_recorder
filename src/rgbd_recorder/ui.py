import subprocess
import threading
import time
import tkinter as tk
from tkinter import messagebox
import configparser

config = configparser.ConfigParser()
config_file = 'config.ini'

def load_config():
    if config.read(config_file):
        serial_numbers_entry.insert(0, config.get('Settings', 'serial_numbers', fallback=''))
        output_dir_entry.insert(0, config.get('Settings', 'output_dir', fallback='output'))
        duration_entry.insert(0, config.get('Settings', 'duration', fallback=''))
        depth_mode_var.set(config.get('Settings', 'depth_mode', fallback='ULTRA'))
        fps_entry.insert(0, config.get('Settings', 'fps', fallback='60'))
        resolution_var.set(config.get('Settings', 'resolution', fallback='1280 720'))

def save_config():
    config['Settings'] = {
        'serial_numbers': serial_numbers_entry.get(),
        'output_dir': output_dir_entry.get(),
        'duration': duration_entry.get(),
        'depth_mode': depth_mode_var.get(),
        'fps': fps_entry.get(),
        'resolution': resolution_var.get()
    }
    with open(config_file, 'w') as configfile:
        config.write(configfile)

def run_script():
    serial_numbers = serial_numbers_entry.get().split()
    output_dir = output_dir_entry.get()
    duration = float(duration_entry.get())
    depth_mode = depth_mode_var.get()
    fps = fps_entry.get()
    resolution = resolution_var.get()

    if not serial_numbers or not duration:
        messagebox.showerror("Error", "Serial numbers and duration are required.")
        return

    command = [
        "python", "-m", "rgbd_recorder.cli",
        "--serial-numbers", *serial_numbers,
        "-o", output_dir,
        "-d", str(duration),
        "-m", depth_mode,
        "--fps", fps,
        "--resolution", *resolution.split()
    ]

    status_label.config(text=f"Recording in progress.")
    save_config()
    subprocess.run(command)
    status_label.config(text=f"Output is saved to: {output_dir}. You can close this window.")

if __name__ == '__main__':
    app = tk.Tk()
    app.title("RGBD Recorder")

    tk.Label(app, text="Serial Numbers (space-separated):").grid(row=0, column=0, sticky=tk.W)
    serial_numbers_entry = tk.Entry(app, width=50)
    serial_numbers_entry.grid(row=0, column=1)

    tk.Label(app, text="Output Directory:").grid(row=1, column=0, sticky=tk.W)
    output_dir_entry = tk.Entry(app, width=50)
    output_dir_entry.grid(row=1, column=1)
    output_dir_entry.insert(0, "output")

    tk.Label(app, text="Duration (seconds):").grid(row=2, column=0, sticky=tk.W)
    duration_entry = tk.Entry(app, width=50)
    duration_entry.grid(row=2, column=1)

    tk.Label(app, text="Depth Mode:").grid(row=3, column=0, sticky=tk.W)
    depth_mode_var = tk.StringVar(value="ULTRA")
    depth_mode_menu = tk.OptionMenu(app, depth_mode_var, "PERFORMANCE", "QUALITY", "ULTRA", "NEURAL")
    depth_mode_menu.grid(row=3, column=1, sticky=tk.W)

    tk.Label(app, text="FPS:").grid(row=4, column=0, sticky=tk.W)
    fps_entry = tk.Entry(app, width=50)
    fps_entry.grid(row=4, column=1)
    output_dir_entry.insert(0, "60")

    tk.Label(app, text="Resolution (width height):").grid(row=5, column=0, sticky=tk.W)
    resolution_var = tk.StringVar(value="1280 720")
    resolution_entry = tk.Entry(app, textvariable=resolution_var, width=50)
    resolution_entry.grid(row=5, column=1)

    tk.Button(app, text="Run", command=run_script).grid(row=6, column=0, columnspan=2)

    status_label = tk.Label(app, text="")
    status_label.grid(row=7, column=0, columnspan=2)

    load_config()
    app.mainloop()