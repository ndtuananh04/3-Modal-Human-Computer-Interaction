import tkinter as tk
import customtkinter as ctk
import json
import os
# from srcc.gui.dialogs.blendshape_dialog import BlendshapeDialog

class BlendshapeSettingsUI(ctk.CTkFrame):
    def __init__(self, parent, face_processor, profile_manager, current_settings):
        super().__init__(parent, fg_color=("#CFCFCF", "#333333"))
        self.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.face_processor = face_processor
        self.profile_manager = profile_manager
        self.current_settings = current_settings
        
        self.available_blendshapes = [
            "browInnerUp", "browDownLeft", "browDownRight",
                "eyeBlinkLeft", "eyeBlinkRight",
                "mouthLeft", "mouthRight", "mouthSmileLeft", "mouthSmileRight",
                "mouthFunnel", "mouthRollLower", "mouthRollUpper", "jawOpen"
        ]
        
        self.basic_actions = [
            "mouse_click", "mouse_right_click", "mouse_double_click"
        ]
        
        self.key_actions = []
        common_keys = [
            "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
            "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "space", "enter", "tab", "esc", "backspace",
            "up", "down", "left", "right"
        ]
        for key in common_keys:
            self.key_actions.append(f"key_{key}")