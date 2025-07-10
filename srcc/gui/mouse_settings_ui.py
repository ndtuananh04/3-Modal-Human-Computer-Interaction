import tkinter as tk
import customtkinter as ctk

class MouseSettingsUI(ctk.CTkFrame):
    
    def __init__(self, parent, current_settings, mouse_controller):
        super().__init__(parent, fg_color=("#CFCFCF", "#333333"))
        self.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.current_settings = current_settings
        self.mouse_controller = mouse_controller
        self.face_processor = None
        self.profile_manager = None
        
        self._create_mouse_settings_ui()
    
    def set_face_processor(self, face_processor):
        self.face_processor = face_processor
        
        if hasattr(self.face_processor, 'set_mode_change_callback'):
            self.face_processor.set_mode_change_callback(self._on_mode_changed)
    
    def set_profile_manager(self, profile_manager):
        self.profile_manager = profile_manager
    
    def _create_mouse_settings_ui(self):
        mode_section = ctk.CTkFrame(self)
        mode_section.pack(fill="x", padx=10, pady=(8, 8))
        
        mode_frame = ctk.CTkFrame(mode_section, fg_color="transparent")
        mode_frame.pack(fill="x", padx=8, pady=8)
        
        self.mode_description_label = ctk.CTkLabel(
            mode_frame, 
            text="Mode: LIVE_STREAM (Smooth)", 
            font=ctk.CTkFont(size=12)
        )
        self.mode_description_label.pack(side="left")
        
        # Small toggle button
        self.mode_toggle_btn = ctk.CTkButton(
            mode_frame,
            text="Switch",
            command=self._toggle_processing_mode,
            width=60,
            height=24,
            font=ctk.CTkFont(size=11)
        )
        self.mode_toggle_btn.pack(side="right")
        
        # Mouse Settings Section
        velocity_label = ctk.CTkLabel(self, text="Mouse Speed:")
        velocity_label.pack(anchor="w", padx=10, pady=(2, 0))
        
        self.velocity_var = ctk.IntVar(
            value=self.current_settings.get("mouse_controller", {}).get("velocity_scale"))
        self.velocity_slider = ctk.CTkSlider(
            self, from_=5, to=30, variable=self.velocity_var, number_of_steps=25,
            command=self.update_velocity_scale
        )
        self.velocity_slider.pack(fill="x", padx=10, pady=(5, 0))
        self.velocity_value = ctk.CTkLabel(self, text=f"{self.velocity_var.get():.1f}")
        self.velocity_value.pack(anchor="e", padx=10, pady=(0, 5))
        
        # Mincutoff setting
        mincutoff_label = ctk.CTkLabel(self, text="Mincutoff:")
        mincutoff_label.pack(anchor="w", padx=10, pady=(2, 0))
        
        self.mincutoff_var = ctk.DoubleVar(
            value=self.current_settings.get("mouse_controller", {}).get("mincutoff"))
        self.mincutoff_slider = ctk.CTkSlider(
            self, from_=0.3, to=1, variable=self.mincutoff_var, number_of_steps=7,
            command=self.update_mincutoff
        )
        self.mincutoff_slider.pack(fill="x", padx=10, pady=(5, 0))
        self.mincutoff_value = ctk.CTkLabel(self, text=f"{self.mincutoff_var.get():.2f}")
        self.mincutoff_value.pack(anchor="e", padx=10, pady=(5, 0))
        
        # Beta setting
        beta_label = ctk.CTkLabel(self, text="Beta:")
        beta_label.pack(anchor="w", padx=10, pady=(2, 0))
        
        self.beta_var = ctk.DoubleVar(
            value=self.current_settings.get("mouse_controller", {}).get("beta"))
        self.beta_slider = ctk.CTkSlider(
            self, from_=0.01, to=0.2, variable=self.beta_var, number_of_steps=20,
            command=self.update_beta
        )
        self.beta_slider.pack(fill="x", padx=10, pady=(5, 0))
        self.beta_value = ctk.CTkLabel(self, text=f"{self.beta_var.get():.2f}")
        self.beta_value.pack(anchor="e", padx=10, pady=(0, 5))
        
        self._update_mode_display()
    
    def _toggle_processing_mode(self):
        if not self.face_processor:
            print("Face processor not available")
            return
        
        self.mode_toggle_btn.configure(state="disabled", text="...")
        
        def switch_mode():
            success = self.face_processor.toggle_mode()
            
            if success:
                new_mode = self.face_processor.get_current_mode()
                self._save_mode_to_profile(new_mode)
            
            self.after(0, lambda: self._on_mode_switch_complete(success))
        
        import threading
        switch_thread = threading.Thread(target=switch_mode)
        switch_thread.start()
    
    def _on_mode_switch_complete(self, success):
        self.mode_toggle_btn.configure(state="normal", text="Switch")
        
        if success:
            self._update_mode_display()
            new_mode = self.face_processor.get_current_mode() if self.face_processor else "Unknown"
            print(f"Successfully switched to {new_mode} mode")
        else:
            print("Failed to switch mode")
    
    def _on_mode_changed(self, mode_name, success):
        self.after(0, lambda: self._update_mode_display())
    
    def _update_mode_display(self):
        if not self.face_processor:
            return
            
        current_mode = self.face_processor.get_current_mode()
        if current_mode == "LIVE_STREAM":
            self.mode_description_label.configure(text="Mode: Live Stream (Smooth)")
        else:
            self.mode_description_label.configure(text="Mode: Image (Rapid)")
        
    
    def _save_mode_to_profile(self, mode):
        try:
            if self.profile_manager:
                current_profile = self.profile_manager.get_current_profile_name()
                settings = self.profile_manager.get_profile_settings()
 
                if "face_processing" not in settings:
                    settings["face_processing"] = {}
                settings["face_processing"]["mode"] = mode

                self.profile_manager.save_profile(current_profile, settings)
                print(f"Saved processing mode '{mode}' to profile '{current_profile}'")
                
        except Exception as e:
            print(f"Error saving mode to profile: {e}")
    
    def update_velocity_scale(self, value):
        self.velocity_value.configure(text=f"{float(value):.1f}")
        self.mouse_controller.velocity_scale = float(value)

        self._save_mouse_setting("velocity_scale", float(value))
    
    def update_mincutoff(self, value):
        self.mincutoff_value.configure(text=f"{float(value):.2f}")
        self.mouse_controller.mincutoff = float(value)
        self.mouse_controller.reset()

        self._save_mouse_setting("mincutoff", float(value))
    
    def update_beta(self, value):
        self.beta_value.configure(text=f"{float(value):.2f}")
        self.mouse_controller.beta = float(value)
        self.mouse_controller.reset()
        
        self._save_mouse_setting("beta", float(value))
    
    def _save_mouse_setting(self, setting_name, value):
        try:
            if self.profile_manager:
                current_profile = self.profile_manager.get_current_profile_name()
                settings = self.profile_manager.get_profile_settings()
                
                if "mouse_controller" not in settings:
                    settings["mouse_controller"] = {}
                settings["mouse_controller"][setting_name] = value
                
                self.profile_manager.save_profile(current_profile, settings)
                
        except Exception as e:
            print(f"Error saving mouse setting to profile: {e}")
    
    def update_from_profile(self, settings):
        mc_settings = settings.get("mouse_controller", {})
        
        self.velocity_var.set(mc_settings.get("velocity_scale"))
        self.mincutoff_var.set(mc_settings.get("mincutoff"))
        self.beta_var.set(mc_settings.get("beta"))
        
        self.velocity_value.configure(text=f"{float(self.velocity_var.get()):.1f}")
        self.mincutoff_value.configure(text=f"{float(self.mincutoff_var.get()):.2f}")
        self.beta_value.configure(text=f"{float(self.beta_var.get()):.2f}")
        
        # Update processing mode nếu có
        face_settings = settings.get("face_processing", {})
        saved_mode = face_settings.get("mode", "LIVE_STREAM")
        
        if self.face_processor:
            current_mode = self.face_processor.get_current_mode()
            if current_mode != saved_mode:
                # Switch to saved mode
                print(f"Switching to saved mode: {saved_mode}")
                if saved_mode == "LIVE_STREAM":
                    if not self.face_processor.is_live_stream_mode:
                        self.face_processor.toggle_mode()
                else:
                    if self.face_processor.is_live_stream_mode:
                        self.face_processor.toggle_mode()
            
            self._update_mode_display()