import tkinter as tk
import customtkinter as ctk
import PIL.Image, PIL.ImageTk
import cv2
from srcc.pipeline import Pipeline
from srcc.gui.profile_manager_ui import ProfileManagerUI
from srcc.gui.mouse_settings_ui import MouseSettingsUI
from srcc.gui.voice_settings_ui import VoiceSettingsUI
from srcc.gui.blendshape_settings_ui import BlendshapeSettingsUI

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
        self.blendshape_processor = self.pipeline.get_blendshape_processor()
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
        control_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        control_frame.pack(fill="x", padx=0, pady=5)
        
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)
        control_frame.columnconfigure(2, weight=1)

        # Mouse control button
        self.mouse_active = False 
        self.mouse_button = ctk.CTkButton(
            control_frame, 
            text="Mouse Control: OFF", 
            command=self.toggle_mouse_control,
            width=150,
            height=26
        )
        self.mouse_button.grid(row=0, column=0, padx=5, pady=5)
        
        # Blendshape control button
        self.blendshape_active = False
        self.blendshape_button = ctk.CTkButton(
            control_frame, 
            text="Blendshape Control: OFF", 
            command=self.toggle_blendshape_control,
            width=150,
            height=26
        )
        self.blendshape_button.grid(row=0, column=1, padx=5, pady=5)

        # Voice control button
        self.voice_active = False 
        self.voice_button = ctk.CTkButton(
            control_frame, 
            text="Voice Command: OFF", 
            command=self.toggle_voice_command,
            width=150,
            height=26
        )
        self.voice_button.grid(row=0, column=2, padx=5, pady=5)
        
        if self.voice_processor and self.voice_processor.thread and self.voice_processor.thread.is_alive():
            self.voice_active = True
            self.voice_button.configure(text="Voice Control: ON")
    
    def _create_right_frame(self, parent):
        right_frame = ctk.CTkFrame(parent, width=410, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=5)
        right_frame.grid_columnconfigure(0, weight=1) 
        right_frame.grid_propagate(False)
        
        profile_container = ctk.CTkFrame(right_frame, fg_color="transparent")
        profile_container.grid(row=0, column=0, sticky="new", padx=50, pady=0)
        profile_container.grid_columnconfigure(0, weight=1)

        # Create profile section
        self.profile_ui = ProfileManagerUI(
            profile_container, 
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

        # Tab Blendshape
        tab2 = settings_frame.add("Blendshape")
        self.blendshape_settings = BlendshapeSettingsUI(
            tab2, 
            self.blendshape_processor, 
            self.profile_manager,
            self.current_settings
        )
        
        # Tab Voice
        tab3 = settings_frame.add("Voice")
        self.voice_settings = VoiceSettingsUI(
            tab3, 
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

    def toggle_blendshape_control(self):
        self.blendshape_active = not self.blendshape_active
        
        if self.blendshape_active:
            self.blendshape_processor.enable()
            self.blendshape_button.configure(text="Blendshape Control: ON")
            print("Blendshape control activated")
        else:
            self.blendshape_processor.disable()
            self.blendshape_processor.cleanup()
            self.blendshape_button.configure(text="Blendshape Control: OFF")
            print("Blendshape control deactivated")

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
            self.blendshape_processor.on_profile_change()
                
        except Exception as e:
            print(f"Error loading profile: {e}")
    
    def update_frame(self):
        frame = self.face_processor.get_processed_frame()
        frame = cv2.flip(frame, 1) if frame is not None else None
        if frame is not None:
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            
            self.canvas.config(width=frame.shape[1], height=frame.shape[0])
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        self.after(self.update_interval, self.update_frame)
    
    def __del__(self):
        if hasattr(self, 'camera_thread') and self.camera_thread:
            self.camera_thread.stop_flag.set()

    def on_closing(self):
        if hasattr(self, 'blendshape_processor'):
            self.blendshape_processor.cleanup()