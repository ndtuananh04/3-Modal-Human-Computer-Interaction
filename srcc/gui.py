import tkinter as tk
import customtkinter as ctk
import cv2
import PIL.Image, PIL.ImageTk
import time
import os
from srcc.pipeline import Pipeline

class GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hands-Free Computer Interaction")
        # self.root.geometry("890x500")
        self.root.resizable(False, False)
        
        self.pipeline = Pipeline()
        if not self.pipeline.is_started:
            self.pipeline.start()

        self.face_processor = self.pipeline.get_face_processor()
        self.mouse_controller = self.pipeline.get_mouse_controller()

        self.profile_manager = self.pipeline.get_profile_manager()
        self.current_settings = self.profile_manager.get_profile_settings()
        
        main_container = ctk.CTkFrame(self.root)
        main_container.pack(fill="both", expand=True, padx=5, pady=12)
        main_container.grid_columnconfigure(0, weight=3)  
        main_container.grid_columnconfigure(1, weight=2)  

        #left frame
        left_frame = ctk.CTkFrame(main_container)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.video_frame = ctk.CTkFrame(left_frame, width=640, height=480)
        self.video_frame.pack(padx=0, pady=5)

        self.canvas = ctk.CTkCanvas(self.video_frame)
        self.canvas.pack(fill="both", expand=True, padx=5, pady=5)

        control_frame = ctk.CTkFrame(left_frame)
        control_frame.pack(padx=0, pady=5)

        self.mouse_active = False 
        self.mouse_button = ctk.CTkButton(
            control_frame, 
            text="Mouse Control: OFF", 
            command=self.toggle_mouse_control,
            width=15,
            height=1
        )
        self.mouse_button.pack(pady=5)

        #right frame
        right_frame = ctk.CTkFrame(main_container, width=350, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=5)

        profile_section = ctk.CTkFrame(right_frame, fg_color=("#CFCFCF", "#333333")) 
        profile_section.grid(row=0, column=0, sticky="new", padx=10, pady=5)

        # profile_selection = ctk.CTkFrame(profile_section)
        # profile_selection.pack(fill="x", pady=5)

        profile_label = ctk.CTkLabel(profile_section, text="Profile:")
        profile_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.profiles = self.profile_manager.list_profiles()
        self.profile_var = tk.StringVar(value=self.profile_manager.get_current_profile_name())

        self.profile_dropdown = ctk.CTkOptionMenu(
            profile_section,
            values=self.profiles,
            variable=self.profile_var,
            command=self.on_profile_change,
            width=150
        )
        self.profile_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="e")

        # button_frame = ctk.CTkFrame(profile_section)
        # button_frame.pack(fill="x", pady=(0, 5))
        # button_frame.columnconfigure(0, weight=1)
        # button_frame.columnconfigure(1, weight=1)
        # button_frame.columnconfigure(2, weight=1)

        self.save_profile_btn = ctk.CTkButton(
            profile_section,
            text="Save",
            command=self.save_current_profile,
            width=65,
            height=24,
            # fg_color="#4CAF50",  # Màu xanh lá
            # hover_color="#45a049"
        )
        self.save_profile_btn.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.add_profile_btn = ctk.CTkButton(
            profile_section,
            text="Add",
            command=self.create_new_profile,
            width=50,
            height=24
        )
        self.add_profile_btn.grid(row=1, column=1, padx=5, pady=5)

        self.delete_profile_btn = ctk.CTkButton(
            profile_section,
            text="Delete",
            command=self.delete_current_profile,
            width=50,
            height=24,
        )
        self.delete_profile_btn.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        #settings
        settings_frame = ctk.CTkFrame(right_frame)
        settings_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        mouse_settings = ctk.CTkFrame(settings_frame)
        mouse_settings.pack(fill="x", pady=5)
        #velocity

        velocity_label = ctk.CTkLabel(mouse_settings, text="Mouse Speed:")
        velocity_label.pack(anchor="w", padx=10, pady= (10, 0))

        self.velocity_var = ctk.IntVar(
            value=self.current_settings.get("mouse_controller", {}).get("velocity_scale"))
        self.velocity_slider = ctk.CTkSlider(
            mouse_settings, from_=5, to=30, variable=self.velocity_var, number_of_steps=25,
            command=self.update_velocity_scale
        )
        self.velocity_slider.pack(fill="x", padx=10, pady=(5, 0))
        self.velocity_value = ctk.CTkLabel(mouse_settings, text=f"{self.velocity_var.get():.1f}")
        self.velocity_value.pack(anchor="e", padx=10, pady=(0, 5))

        #mincutoff
        mincutoff_label = ctk.CTkLabel(mouse_settings, text="Mincutoff:")
        mincutoff_label.pack(anchor="w", padx=10, pady=(10, 0))

        self.mincutoff_var = ctk.DoubleVar(
            value=self.current_settings.get("mouse_controller", {}).get("mincutoff"))
        self.mincutoff_slider = ctk.CTkSlider(
            mouse_settings, from_=0.3, to=1, variable=self.mincutoff_var, number_of_steps = 7,
            command=self.update_mincutoff
        )
        self.mincutoff_slider.pack(fill="x", padx=10, pady=(5, 0))
        self.mincutoff_value = ctk.CTkLabel(mouse_settings, text=f"{self.mincutoff_var.get():.1f}")
        self.mincutoff_value.pack(anchor="e", padx=10, pady=(5, 0))

        #beta
        beta_label = ctk.CTkLabel(mouse_settings, text="Beta:")
        beta_label.pack(anchor="w", padx=10, pady=(10, 0))

        self.beta_var = ctk.DoubleVar(
            value=self.current_settings.get("mouse_controller", {}).get("beta"))
        self.beta_slider = ctk.CTkSlider(
            mouse_settings, from_=0.01, to=0.2, variable=self.beta_var, number_of_steps = 20,
            command=self.update_beta
        )
        self.beta_slider.pack(fill="x", padx=10, pady=(5, 0))
        self.beta_value = ctk.CTkLabel(mouse_settings, text=f"{self.beta_var.get():.2f}")
        self.beta_value.pack(anchor="e", padx=10, pady=(0, 5))

        self.update_interval = 10
        self.update_frame()
    
    def on_profile_change(self, profile_name):
            try:
                self.current_settings = self.profile_manager.load_profile(profile_name)
                mc_settings = self.current_settings.get("mouse_controller", {})
                
                self.velocity_var.set(mc_settings.get("velocity_scale"))
                self.mincutoff_var.set(mc_settings.get("mincutoff"))
                self.beta_var.set(mc_settings.get("beta"))
                
                self.mouse_controller.velocity_scale = mc_settings.get("velocity_scale")
                self.mouse_controller.mincutoff = mc_settings.get("mincutoff")
                self.mouse_controller.beta = mc_settings.get("beta")
                    
            except Exception as e:
                print(f"Error loading profile: {e}")


    def save_current_profile(self):
        current_name = self.profile_var.get()
        
        updated_settings = {
            "mouse_controller": {
                "velocity_scale": self.velocity_var.get(),
                "mincutoff": self.mincutoff_var.get(),
                "beta": self.beta_var.get()
            }
        }

        try:
            self.profile_manager.update_profile_settings(updated_settings, current_name)
            print(f"Profile '{current_name}' saved successfully")
        except Exception as e:
            print(f"Error saving profile: {e}")

    def create_new_profile(self):
        dialog = ctk.CTkInputDialog(text="Enter new profile name:", title="New Profile")
        new_name = dialog.get_input()
        
        if new_name:
            new_settings = {
                "mouse_controller": {
                    "velocity_scale": self.velocity_var.get(),
                    "mincutoff": self.mincutoff_var.get(),
                    "beta": self.beta_var.get()
                }
            }

            self.profile_manager.save_profile(new_name, new_settings)

            self.profiles = self.profile_manager.list_profiles()
            self.profile_dropdown.configure(values=self.profiles)
            self.profile_dropdown.set(new_name)

    def delete_current_profile(self):
        current_name = self.profile_var.get()
        
        if current_name == "default":
            print("Cannot delete default profile")
            return
        
        self.profile_manager.delete_profile(current_name)
        
        self.profiles = self.profile_manager.list_profiles()
        self.profile_dropdown.configure(values=self.profiles)
        self.profile_dropdown.set("default")
        
        self.on_profile_change("default")
                
    def update_velocity_scale(self, value):
        self.velocity_value.configure(text=f"{float(value):.1f}")
        self.mouse_controller.velocity_scale = float(value)

    def update_mincutoff(self, value):
        self.mincutoff_value.configure(text=f"{float(value):.2f}")
        self.mouse_controller.mincutoff = float(value)
        self.mouse_controller.reset()

    def update_beta(self, value):
        self.beta_value.configure(text=f"{float(value):.2f}")
        self.mouse_controller.beta = float(value)
        self.mouse_controller.reset()

    def toggle_mouse_control(self):
        self.mouse_active = not self.mouse_active
        
        if self.mouse_active:
            self.mouse_controller.start_tracking()
            self.mouse_button.configure(text="Mouse Control: ON", bg="green")
        else:
            self.mouse_controller.stop_tracking()
            self.mouse_button.configure(text="Mouse Control: OFF", bg="red")

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