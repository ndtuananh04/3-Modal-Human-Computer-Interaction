import tkinter as tk
import customtkinter as ctk
import PIL.Image, PIL.ImageTk
import time
import os

from srcc.pipeline import Pipeline
from srcc.gui.profile_manager_ui import ProfileManagerUI
from srcc.gui.mouse_settings_ui import MouseSettingsUI
from srcc.gui.voice_settings_ui import VoiceSettingsUI

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.root = self
            
        self.title("Hands-Free Computer Interaction")
        self.resizable(False, False)
        
        self.pipeline = Pipeline()
        if not self.pipeline.is_started:
            self.pipeline.start()

        self.face_processor = self.pipeline.get_face_processor()
        self.mouse_controller = self.pipeline.get_mouse_controller()
        self.voice_processor = self.pipeline.get_voice_processor()
        self.profile_manager = self.pipeline.get_profile_manager()
        self.current_settings = self.profile_manager.get_profile_settings()

        self._create_main_layout()
        
        self.update_interval = 10
        self.update_frame()
    
    def _create_main_layout(self):
        # Main container
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=5, pady=12)
        
        self._create_left_frame(main_container)
        
        self._create_right_frame(main_container)
    
    def _create_left_frame(self, parent):
        left_frame = ctk.CTkFrame(parent)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Video frame
        self.video_frame = ctk.CTkFrame(left_frame, width=640, height=480)
        self.video_frame.pack(padx=0, pady=5)
        
        self.canvas = ctk.CTkCanvas(self.video_frame)
        self.canvas.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Control frame with buttons
        control_frame = ctk.CTkFrame(left_frame)
        control_frame.pack(padx=0, pady=5)
        
        # Mouse control button
        self.mouse_active = False 
        self.mouse_button = ctk.CTkButton(
            control_frame, 
            text="Mouse Control: OFF", 
            command=self.toggle_mouse_control,
            width=15,
            height=1
        )
        self.mouse_button.pack(pady=5)
        
        # Voice control button
        self.voice_active = False 
        self.voice_button = ctk.CTkButton(
            control_frame, 
            text="Voice Command: OFF", 
            command=self.toggle_voice_command,
            width=15,
            height=1
        )
        self.voice_button.pack(pady=5)
        
        if self.voice_processor and self.voice_processor.thread and self.voice_processor.thread.is_alive():
            self.voice_active = True
            self.voice_button.configure(text="Voice Control: ON")
    
    def _create_right_frame(self, parent):
        right_frame = ctk.CTkFrame(parent, width=370, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=5)
        right_frame.grid_columnconfigure(0, weight=1) 
        right_frame.grid_propagate(False)
        
        # Create profile section
        self.profile_ui = ProfileManagerUI(
            right_frame, 
            self.profile_manager,
            self.mouse_controller,
            self.voice_processor,
            self.on_profile_change
        )
        self.profile_ui.grid(row=0, column=0, sticky="new", padx=10, pady=5)
        
        # Create settings tabview
        settings_frame = ctk.CTkTabview(right_frame)
        settings_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # Tab Mouse
        tab1 = settings_frame.add("Mouse")
        self.mouse_settings = MouseSettingsUI(
            tab1, 
            self.current_settings, 
            self.mouse_controller
        )
        
        # Tab Voice
        tab2 = settings_frame.add("Voice")
        self.voice_settings = VoiceSettingsUI(
            tab2, 
            self.voice_processor,
            self.profile_manager,
            self.current_settings
        )
    
    def toggle_mouse_control(self):
        self.mouse_active = not self.mouse_active
        
        if self.mouse_active:
            self.mouse_controller.start_tracking()
            self.mouse_button.configure(text="Mouse Control: ON")
        else:
            self.mouse_controller.stop_tracking()
            self.mouse_button.configure(text="Mouse Control: OFF")
    
    def toggle_voice_command(self):
        self.voice_active = not self.voice_active
        
        if self.voice_active:
            success = self.voice_processor.start()
            if success:
                self.voice_button.configure(text="Voice Control: ON")
                print("Voice control activated")
            else:
                self.voice_active = False
                print("Failed to start voice control")
        else:
            self.voice_processor.stop()
            self.voice_button.configure(text="Voice Control: OFF")
            print("Voice control deactivated")
    
    def on_profile_change(self, profile_name):
        try:
            self.current_settings = self.profile_manager.load_profile(profile_name)
            
            # Update mouse settings UI
            self.mouse_settings.update_from_profile(self.current_settings)
            
            # Update voice settings UI
            self.voice_settings.update_from_profile()
                
        except Exception as e:
            print(f"Error loading profile: {e}")
    
    def update_frame(self):
        frame = self.face_processor.get_processed_frame()
        if frame is not None:
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            
            self.canvas.config(width=frame.shape[1], height=frame.shape[0])
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        self.after(self.update_interval, self.update_frame)
    
    def __del__(self):
        if hasattr(self, 'camera_thread') and self.camera_thread:
            self.camera_thread.stop_flag.set()