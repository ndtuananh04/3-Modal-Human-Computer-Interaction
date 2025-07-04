import tkinter as tk
import customtkinter as ctk

class MouseSettingsUI(ctk.CTkFrame):
    
    def __init__(self, parent, current_settings, mouse_controller):
        super().__init__(parent, fg_color=("#CFCFCF", "#333333"))
        self.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.current_settings = current_settings
        self.mouse_controller = mouse_controller
        
        self._create_mouse_settings_ui()
    
    def _create_mouse_settings_ui(self):
        velocity_label = ctk.CTkLabel(self, text="Mouse Speed:")
        velocity_label.pack(anchor="w", padx=10, pady=(10, 0))
        
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
        mincutoff_label.pack(anchor="w", padx=10, pady=(10, 0))
        
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
        beta_label.pack(anchor="w", padx=10, pady=(10, 0))
        
        self.beta_var = ctk.DoubleVar(
            value=self.current_settings.get("mouse_controller", {}).get("beta"))
        self.beta_slider = ctk.CTkSlider(
            self, from_=0.01, to=0.2, variable=self.beta_var, number_of_steps=20,
            command=self.update_beta
        )
        self.beta_slider.pack(fill="x", padx=10, pady=(5, 0))
        self.beta_value = ctk.CTkLabel(self, text=f"{self.beta_var.get():.2f}")
        self.beta_value.pack(anchor="e", padx=10, pady=(0, 5))
    
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
    
    def update_from_profile(self, settings):
        mc_settings = settings.get("mouse_controller", {})
        
        self.velocity_var.set(mc_settings.get("velocity_scale"))
        self.mincutoff_var.set(mc_settings.get("mincutoff"))
        self.beta_var.set(mc_settings.get("beta"))
        
        # Update values display
        self.velocity_value.configure(text=f"{float(self.velocity_var.get()):.1f}")
        self.mincutoff_value.configure(text=f"{float(self.mincutoff_var.get()):.2f}")
        self.beta_value.configure(text=f"{float(self.beta_var.get()):.2f}")