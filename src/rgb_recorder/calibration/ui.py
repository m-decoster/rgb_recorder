import tkinter as tk
from tkinter import messagebox
import configparser
from rgb_recorder.calibration.stereo_calibration import open_cameras, compute_calibration, save_calibration_output

config = configparser.ConfigParser()
config_file = '../config_calibration.ini'

def load_config():
    if config.read(config_file):
        left_camera_entry.insert(0, config.get('Settings', 'left_camera', fallback=''))
        right_camera_entry.insert(0, config.get('Settings', 'right_camera', fallback=''))
        output_dir_entry.insert(0, config.get('Settings', 'output_dir', fallback='output'))

def save_config():
    config['Settings'] = {
        'left_camera': left_camera_entry.get(),
        'right_camera': right_camera_entry.get(),
        'output_dir': output_dir_entry.get(),
    }
    with open(config_file, 'w') as configfile:
        config.write(configfile)

def start_calibration():
    left_camera = left_camera_entry.get()
    right_camera = right_camera_entry.get()
    output_dir = output_dir_entry.get()

    if not left_camera or not right_camera:
        messagebox.showerror("Error", "Both camera serial numbers are required.")
        return

    camera_1, camera_2 = open_cameras(left_camera, right_camera)
    X_C1_C2 = compute_calibration(camera_1, camera_2)
    save_calibration_output(X_C1_C2, camera_1, camera_2, output_dir)

    messagebox.showinfo("Success", "Stereo calibration completed successfully.")

    save_config()

if __name__ == '__main__':
    app = tk.Tk()
    app.title("Stereo Calibration")

    tk.Label(app, text="Left Camera Serial Number:").grid(row=0, column=0, sticky=tk.W)
    left_camera_entry = tk.Entry(app, width=50)
    left_camera_entry.grid(row=0, column=1)

    tk.Label(app, text="Right Camera Serial Number:").grid(row=1, column=0, sticky=tk.W)
    right_camera_entry = tk.Entry(app, width=50)
    right_camera_entry.grid(row=1, column=1)

    tk.Label(app, text="Output Directory:").grid(row=2, column=0, sticky=tk.W)
    output_dir_entry = tk.Entry(app, width=50)
    output_dir_entry.grid(row=2, column=1)

    start_button = tk.Button(app, text="Start Calibration", command=start_calibration)
    start_button.grid(row=3, column=0, columnspan=2)

    load_config()
    app.mainloop()