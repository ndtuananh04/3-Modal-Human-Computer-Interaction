import tkinter as tk
import cv2
import PIL.Image, PIL.ImageTk
import time
from srcc.pipeline import Pipeline

class GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hands-Free Computer Interaction")
        self.root.geometry("670x700")
        
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.video_frame = tk.Frame(main_frame, bg="black", width=640, height=480)
        self.video_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.video_frame.pack_propagate(False)

        self.canvas = tk.Canvas(self.video_frame, bg="white")
        self.canvas.pack(side= tk.LEFT, fill=tk.BOTH, expand=True)

        control_frame = tk.Frame(main_frame)
        control_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        self.mouse_active = False 
        self.mouse_button = tk.Button(
            control_frame, 
            text="Mouse Control: OFF", 
            command=self.toggle_mouse_control,
            bg="red",
            fg="white",
            font=("Arial", 12, "bold"),
            width=15,
            height=1
        )
        self.mouse_button.pack(pady=5)

        self.pipeline = Pipeline()
        if not self.pipeline.is_started:
            self.pipeline.start()

        self.face_processor = self.pipeline.get_face_processor()
        self.mouse_controller = 1
        self.update_interval = 10
        self.update_frame()
    
    def toggle_mouse_control(self):
        if self.mouse_controller:
            self.mouse_active = not self.mouse_active
            
            if self.mouse_active:
                self.pipeline.mouse_controller.start_tracking()
                self.mouse_button.config(text="Mouse Control: ON", bg="green")
            else:
                self.pipeline.mouse_controller.stop_tracking()
                self.mouse_button.config(text="Mouse Control: OFF", bg="red")

    def update_frame(self):
        frame = self.face_processor.get_processed_frame()
        if frame is not None:
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            
            self.canvas.config(width=frame.shape[1], height=frame.shape[0])
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        self.root.after(self.update_interval, self.update_frame)
    
    def __del__(self):
        if hasattr(self, 'camera_thread') and self.camera_thread:
            self.camera_thread.stop_flag.set()