#old version of gui


import tkinter as tk
import customtkinter as ctk
import cv2
import PIL.Image, PIL.ImageTk
import time
import os
from srcc.pipeline import Pipeline

class GUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Hands-Free Computer Interaction")
        self.resizable(False, False)
        
        self.pipeline = Pipeline()
        if not self.pipeline.is_started:
            self.pipeline.start()

        self.face_processor = self.pipeline.get_face_processor()
        self.mouse_controller = self.pipeline.get_mouse_controller()

        self.profile_manager = self.pipeline.get_profile_manager()
        self.current_settings = self.profile_manager.get_profile_settings()
        
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=5, pady=12)
        # main_container.grid_columnconfigure(0, weight=3)  
        # main_container.grid_columnconfigure(1, weight=2)  

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

        self.voice_active = False 
        self.voice_button = ctk.CTkButton(
            control_frame, 
            text="Voice Command: OFF", 
            command=self.toggle_voice_command,
            width=15,
            height=1
        )
        self.voice_button.pack(pady=5)

        #right frame
        right_frame = ctk.CTkFrame(main_container, width=370, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=5)
        right_frame.grid_columnconfigure(0, weight=1) 
        right_frame.grid_propagate(False)

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
        # settings_frame = ctk.CTkFrame(right_frame)
        # settings_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        settings_frame = ctk.CTkTabview(right_frame)
        settings_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        tab1 = settings_frame.add("Mouse")
        tab2 = settings_frame.add("Voice")

        #tab1
        mouse_settings = ctk.CTkFrame(tab1, fg_color=("#CFCFCF", "#333333"))
        mouse_settings.pack(fill="both", expand=True, padx=5, pady=5)
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

        #tab2
        self.voice_settings = ctk.CTkFrame(tab2, fg_color=("#CFCFCF", "#333333"))
        self.voice_settings.pack(fill="both", expand=True, padx=5, pady=5)

        self.voice_processor = self.pipeline.get_voice_processor()

        mic_section = ctk.CTkFrame(self.voice_settings)
        mic_section.pack(fill="x", padx=5, pady=5)

        mic_label = ctk.CTkLabel(mic_section, text="Microphone:")
        mic_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        mic_list = ["Default Microphone"]
        try:
            available_mics = self.voice_processor.available_microphones
            if available_mics and len(available_mics) > 0:
                mic_list = available_mics
        except Exception as e:
            print(f"Error getting microphones: {e}")

        current_mic = self.voice_processor.selected_microphone or mic_list[0]

        self.mic_var = tk.StringVar(value=current_mic)
        self.mic_dropdown = ctk.CTkOptionMenu(
            mic_section,
            values=mic_list,
            variable=self.mic_var,
            command=self.change_microphone,
            width=200
        )
        self.mic_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="e")

        cmd_buttons_frame = ctk.CTkFrame(self.voice_settings)
        cmd_buttons_frame.pack(fill="x", padx=5, pady=5)

        add_cmd_btn = ctk.CTkButton(
            cmd_buttons_frame,
            text="Add Command",
            command=self.add_voice_command,
            width=100,
            height=28
        )
        add_cmd_btn.pack(fill="both", padx=5, pady=5)
        
        self.load_voice_commands()

        if self.voice_processor and self.voice_processor.thread and self.voice_processor.thread.is_alive():
            self.voice_active = True
            self.voice_button.configure(text="Voice Control: ON")
    
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

                if self.voice_processor:
                    self.voice_processor.on_profile_change()
                    
                    self.mic_var.set(self.voice_processor.selected_microphone or "Default Microphone")
                    self.load_voice_commands()
                    
            except Exception as e:
                print(f"Error loading profile: {e}")


    def save_current_profile(self):
        current_name = self.profile_var.get()
        
        updated_settings = {
            "mouse_controller": {
                "velocity_scale": self.velocity_var.get(),
                "mincutoff": self.mincutoff_var.get(),
                "beta": self.beta_var.get()
            },
            "voice_processor": {
                "selected_microphone": self.mic_var.get()
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

    def change_microphone(self, mic_name):
        try:
            current_mic = self.current_settings.get("voice_processor", {}).get("selected_microphone", "Default Microphone")
            
            print(f"Setting microphone to: {mic_name}")
            success = self.voice_processor.set_microphone(mic_name)
            
            if success:
                current_name = self.profile_var.get()
                profile_settings = self.profile_manager.load_profile(current_name)
                
                if "voice_processor" not in profile_settings:
                    profile_settings["voice_processor"] = {}
                
                profile_settings["voice_processor"]["selected_microphone"] = mic_name
                
                self.profile_manager.save_profile(current_name, profile_settings)
                
                self.current_settings = profile_settings
                
                print(f"Changed microphone to: {mic_name}")
            else:
                self.mic_var.set(current_mic)
                print(f"Failed to change microphone to: {mic_name}")
                
        except Exception as e:
            # Nếu có lỗi, cũng khôi phục UI
            self.mic_var.set(self.current_settings.get("voice_processor", {}).get("selected_microphone", "Default Microphone"))
            print(f"Error changing microphone: {e}")

    def load_voice_commands(self):
        if hasattr(self, 'commands_frame'):
            self.commands_frame.destroy()
        
        self.commands_frame = ctk.CTkFrame(self.voice_settings)
        self.commands_frame.pack(fill="both", expand=True, padx=5, pady=(10, 5))
        
        cmd_title = ctk.CTkLabel(self.commands_frame, text="Voice Commands:")
        cmd_title.pack(anchor="w", padx=10, pady=5)
        
        commands = self.voice_processor.commands if self.voice_processor else []
        
        if not commands:
            no_cmd_label = ctk.CTkLabel(self.commands_frame, text="No commands defined", text_color="gray")
            no_cmd_label.pack(pady=10)
        else:
            cmd_scroll = ctk.CTkScrollableFrame(self.commands_frame, height=150)
            cmd_scroll.pack(fill="x", padx=10, pady=5)
            
            for i, cmd in enumerate(commands):
                cmd_frame = ctk.CTkFrame(cmd_scroll)
                cmd_frame.pack(fill="x", pady=2)

                cmd_frame.command_index = i
                cmd_frame.bind("<Double-1>", lambda e: self.show_command_options(e.widget.command_index))

                command_text = cmd.get("command", "")
                action_text = cmd.get("action", "")
                
                cmd_label = ctk.CTkLabel(cmd_frame, text=f"{command_text}", width=180, anchor="w")
                cmd_label.pack(side="left", padx=(5, 10), pady=5)
                cmd_label.bind("<Double-1>", lambda e, idx=i: self.show_command_options(idx))
                
                action_label = ctk.CTkLabel(cmd_frame, text=f"→ {action_text}", anchor="w")
                action_label.pack(side="left", fill="x", expand=True, padx=5, pady=5)
                action_label.bind("<Double-1>", lambda e, idx=i: self.show_command_options(idx))

    def show_command_options(self, command_index):
        commands = self.current_settings.get("voice_processor", {}).get("commands", [])
        if command_index < 0 or command_index >= len(commands):
            return
        
        cmd = commands[command_index]
        command_text = cmd.get("command", "")
        action_text = cmd.get("action", "")
        
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Edit Voice Command")
        dialog.geometry("400x180")
        dialog.grab_set()
        
        frame = ctk.CTkFrame(dialog)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        cmd_label = ctk.CTkLabel(frame, text="Command:")
        cmd_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        cmd_var = tk.StringVar(value=command_text)
        cmd_entry = ctk.CTkEntry(frame, textvariable=cmd_var, width=250)
        cmd_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        cmd_entry.focus()
        
        action_label = ctk.CTkLabel(frame, text="Action:")
        action_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        action_var = tk.StringVar(value=action_text)
        action_entry = ctk.CTkEntry(frame, textvariable=action_var, width=250)
        action_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=15, sticky="ew")
        
        def save_changes():
            command = cmd_var.get().strip()
            action = action_var.get().strip()
            
            if not command or not action:
                print("Command and action cannot be empty")
                return
            print(command_index)
            print(command, action)
            success = self.voice_processor.update_command(command_index, command, action)
            if success:
                self.current_settings = self.profile_manager.get_profile_settings()
                self.load_voice_commands()
                dialog.destroy()
            else:
                print("Failed to update command")
        
        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save",
            command=save_changes,
            width=80
        )
        save_btn.pack(side="left", padx=10)
        
        # Delete button
        def delete_command():
            # Hiển thị dialog xác nhận xóa
            confirm = ctk.CTkToplevel(dialog)
            confirm.title("Confirm Delete")
            confirm.geometry("300x120")
            confirm.grab_set()
            
            conf_frame = ctk.CTkFrame(confirm)
            conf_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            question = f'Delete command "{command_text}"?'
            msg = ctk.CTkLabel(conf_frame, text=question)
            msg.pack(pady=10)
            
            conf_btn_frame = ctk.CTkFrame(conf_frame, fg_color="transparent")
            conf_btn_frame.pack(pady=10)
            
            def confirm_delete():
                success = self.voice_processor.delete_command(command_index)
                if success:
                    self.current_settings = self.profile_manager.get_profile_settings()
                    self.load_voice_commands()
                    confirm.destroy()
                    dialog.destroy()
            
            yes_btn = ctk.CTkButton(
                conf_btn_frame,
                text="Yes",
                command=confirm_delete,
                width=60,
                fg_color="#FF5555",
                hover_color="#DD4444"
            )
            yes_btn.pack(side="left", padx=10)

            no_btn = ctk.CTkButton(
                conf_btn_frame,
                text="No",
                command=confirm.destroy,
                width=60
            )
            no_btn.pack(side="left", padx=10)
        
        delete_btn = ctk.CTkButton(
            btn_frame,
            text="Delete",
            command=delete_command,
            width=80,
            fg_color="#FF5555",
            hover_color="#DD4444"
        )
        delete_btn.pack(side="left", padx=10)
        
        # Close button
        close_btn = ctk.CTkButton(
            btn_frame,
            text="Close",
            command=dialog.destroy,
            width=80
        )
        close_btn.pack(side="left", padx=10)

    def add_voice_command(self):
        if not self.voice_processor:
            return
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Voice Command")
        dialog.geometry("400x200")
        dialog.grab_set()
        
        frame = ctk.CTkFrame(dialog)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        cmd_label = ctk.CTkLabel(frame, text="Command phrase:")
        cmd_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        cmd_var = tk.StringVar()
        cmd_entry = ctk.CTkEntry(frame, textvariable=cmd_var, width=250)
        cmd_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        action_label = ctk.CTkLabel(frame, text="Action:")
        action_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        action_var = tk.StringVar()
        action_entry = ctk.CTkEntry(frame, textvariable=action_var, width=250)
        action_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=10, sticky="ew")
        
        def save_command():
            command = cmd_var.get().strip()
            action = action_var.get().strip()
            
            if not command or not action:
                return
                
            success = self.voice_processor.add_command(command, action)
            if success:
                self.current_settings = self.profile_manager.get_profile_settings()
                self.load_voice_commands()
                dialog.destroy()
        
        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save",
            command=save_command,
            width=80
        )
        save_btn.pack(side="left")
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            width=80
        )
        cancel_btn.pack(side="left", padx=(0, 10))
        

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