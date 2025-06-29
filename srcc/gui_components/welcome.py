import customtkinter as ctk
import os
import sys

class WelcomeScreen(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Hands-Free Computer Interaction")
        self.geometry("800x500")
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        main_frame = ctk.CTkFrame(self, corner_radius=0)
        main_frame.pack(fill="both", expand=True)
        
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Hands-Free Computer Interaction", 
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.pack(pady=40)
        
        self.start_button = ctk.CTkButton(
            main_frame,
            text="Start Application",
            font=ctk.CTkFont(size=18),
            height=50,
            width=250,
            fg_color="#2266EE",
            hover_color="#1155DD",
            command=self.start_main_interface
        )
        self.start_button.pack(pady=30)
        self.main_app = None
        
    def start_main_interface(self):
        from srcc.gui import GUI
        self.withdraw()
        main_window = ctk.CTk()
        self.main_app = GUI(main_window)
        main_window.protocol("WM_DELETE_WINDOW", self.on_main_closing)
        main_window.mainloop()
    
    def on_main_closing(self):
        if hasattr(self, 'main_app') and self.main_app:
            self.main_app.on_closing()
        sys.exit(0)