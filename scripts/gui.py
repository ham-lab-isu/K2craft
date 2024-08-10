import tkinter as tk
from tkinter import ttk
import threading
from camera import CameraManager
from server import ServerManager
from utils import update_image, update_graphs, resize_image

class Kaw2FFFControl:
    def __init__(self, root):
        self.root = root
        self.root.title("Kaw2 FFF Control")

        # Initialize IO state dictionaries
        self.input_states = {}
        self.output_states = {}
        self.connection_state = False

        # Initialize display variable
        self.display_var = tk.StringVar(value="both")

        # Initialize camera manager
        self.camera_manager = CameraManager(self.display_var)

        # Initialize server manager
        self.server_manager = ServerManager(self)

        # Initialize GUI elements
        self.initialize_gui()

        # Start server in a separate thread
        self.server_thread = threading.Thread(target=self.server_manager.setup_server)
        self.server_thread.daemon = True
        self.server_thread.start()

    def initialize_gui(self):
        # Using grid for the entire layout
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(sticky=(tk.W, tk.E, tk.N, tk.S))

        # Set up the tab control
        self.tab_control = ttk.Notebook(self.main_frame)
        self.IO_control_tab = ttk.Frame(self.tab_control)
        self.camera_tab = ttk.Frame(self.tab_control)
        self.motor_control_tab = ttk.Frame(self.tab_control)

        # Set up camera controls
        self.setup_camera_controls()

        # Initialize IO controls
        self.create_io_controls(self.IO_control_tab, 1, 16, 0)
        self.create_io_controls(self.IO_control_tab, 2, 16, 1)

        self.tab_control.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Set up the camera display label
        self.video_label = ttk.Label(self.camera_tab)
        self.video_label.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Initialize the matplotlib graph
        self.fig, self.ax = self.camera_manager.initialize_graph()
        self.canvas = self.camera_manager.create_canvas(self.fig, self.camera_tab)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=0, column=2, rowspan=7, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Motor control UI
        self.setup_motor_control_ui()

    def setup_camera_controls(self):
        self.start_video_button = ttk.Button(self.camera_tab, text="Start Video Feed", command=self.camera_manager.start_video_feed)
        self.start_video_button.grid(row=1, column=0, pady=10, sticky=tk.W)

        self.stop_video_button = ttk.Button(self.camera_tab, text="Stop Video Feed", command=self.camera_manager.stop_video_feed)
        self.stop_video_button.grid(row=1, column=1, pady=10, sticky=tk.W)

        # Styling for radio buttons
        style = ttk.Style()
        style.configure('Big.TRadiobutton', font=('Helvetica', 12))

        # Adding a frame to group the radio buttons
        self.radio_button_frame = ttk.LabelFrame(self.camera_tab, text="Display Options", padding=(10, 5))
        self.radio_button_frame.grid(row=2, column=0, columnspan=2, pady=10, padx=10, sticky=tk.W)

        # Define the radio buttons
        for i, (text, value) in enumerate([("Lines", "lines"), ("Blobs", "blobs"), ("Colors", "color"), 
                                            ("Edges", "edges"), ("Contours", "contours"), ("Shapes", "shapes"), 
                                            ("Both", "both")]):
            ttk.Radiobutton(self.radio_button_frame, text=text, variable=self.display_var, value=value, style='Big.TRadiobutton').grid(row=i, column=0, sticky=tk.W, pady=2)

    def create_io_controls(self, parent, channel, num_pins, column):
        frame = ttk.LabelFrame(parent, text=f"Channel {channel} Controls", padding="10")
        frame.grid(row=0, column=column, sticky='nsew', padx=5, pady=5)

        for pin in range(1, num_pins + 1):
            pin_label = ttk.Label(frame, text=f"Pin {pin}: Low", background="red", width=15)
            pin_label.grid(row=pin-1, column=0, sticky='ew')

            if channel in [1, 2]:
                self.input_states[(channel, pin)] = pin_label
            else:
                if not (channel == 3 and pin == 9):
                    button = ttk.Button(frame, text="Toggle", command=lambda ch=channel, p=pin: self.toggle_output(ch, p))
                    button.grid(row=pin-1, column=1, padx=5, pady=2)
                    self.output_states[(channel, pin)] = (pin_label, button)
                else:
                    pin_label.config(text="Pin 9: High", background="green")
                    self.set_output(channel, pin, True)

    def setup_motor_control_ui(self):
        motor_frame = ttk.LabelFrame(self.motor_control_tab, text="Motor Commands", padding="10")
        motor_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ttk.Button(motor_frame, text="Start Motor", command=self.start_motor).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(motor_frame, text="Stop Motor", command=self.stop_motor).grid(row=0, column=1, padx=5, pady=5)

        self.motor_speed_var = tk.DoubleVar(value=0)
        ttk.Label(motor_frame, text="Speed:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Scale(motor_frame, from_=0, to=100, variable=self.motor_speed_var, orient="horizontal", command=self.update_motor_speed).grid(row=1, column=1, sticky="ew")

    def toggle_output(self, channel, pin):
        label, button = self.output_states[(channel, pin)]
        current_state = label.cget("text").endswith("High")
        new_state = not current_state
        self.set_output(channel, pin, new_state)
        label.config(text=f"Pin {pin}: {'High' if new_state else 'Low'}", background="green" if new_state else "red")
        button.config(text="Toggle Off" if new_state else "Toggle On")

    def set_output(self, channel, pin, state):
        command = f"SET_OUTPUT:{channel}:{pin}:{1 if state else 0}"
        self.server_manager.send_data(command + "\n")
        print(f"Command sent: {command}")

    def start_motor(self):
        print("This button has not yet been implemented.")

    def stop_motor(self):
        print("Stopping motor...")
        print("This button has not yet been implemented.")

    def update_motor_speed(self, event):
        speed = self.motor_speed_var.get()
        print(f"Setting motor speed to {speed}")

    def on_closing(self):
        print("Shutting down server...")
        self.server_manager.shutdown_server()
        self.root.destroy()
