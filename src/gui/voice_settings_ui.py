import tkinter as tk
import customtkinter as ctk
from src.gui.dialogs.command_dialog import CommandDialog, AddCommandDialog
from src.gui.submenu import SubmenuDropdown

class VoiceSettingsUI(ctk.CTkFrame):
    def __init__(self, parent, voice_processor, profile_manager, current_settings):
        super().__init__(parent, fg_color=("#CFCFCF", "#333333"))
        self.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.voice_processor = voice_processor
        self.profile_manager = profile_manager
        self.current_settings = current_settings
        
        self._create_voice_settings_ui()
    
    def _create_voice_settings_ui(self):
        # Microphone section
        mic_section = ctk.CTkFrame(self)
        mic_section.pack(fill="x", padx=5, pady=5)
        
        mic_label = ctk.CTkLabel(mic_section, text="Microphone:")
        mic_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Get available microphones
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
        
        # Command buttons
        cmd_buttons_frame = ctk.CTkFrame(self)
        cmd_buttons_frame.pack(fill="x", padx=5, pady=5)
        
        add_cmd_btn = ctk.CTkButton(
            cmd_buttons_frame,
            text="Add Command",
            command=self.add_voice_command,
            width=100,
            height=28
        )
        add_cmd_btn.pack(fill="both", padx=5, pady=5)
        
        # Load commands
        self.load_voice_commands()
    
    def change_microphone(self, mic_name):
        try:
            current_mic = self.current_settings.get("voice_processor", {}).get("selected_microphone", "Default Microphone")
            
            print(f"Setting microphone to: {mic_name}")
            success = self.voice_processor.set_microphone(mic_name)
            
            if success:
                current_name = self.profile_manager.get_current_profile_name()
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
            self.mic_var.set(self.current_settings.get("voice_processor", {}).get("selected_microphone", "Default Microphone"))
            print(f"Error changing microphone: {e}")
    
    def load_voice_commands(self):
        if hasattr(self, 'commands_frame'):
            self.commands_frame.destroy()
        
        self.commands_frame = ctk.CTkFrame(self)
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
        
        dialog = CommandDialog(self, command_index, command_text, action_text, 
                              self.voice_processor, self.profile_manager)
    
    def add_voice_command(self):
        if not self.voice_processor:
            return
        
        dialog = AddCommandDialog(self, self.voice_processor, self.profile_manager)
        
    
    def update_from_profile(self):
        if self.voice_processor:
            self.voice_processor.on_profile_change()
            
            self.mic_var.set(self.voice_processor.selected_microphone or "Default Microphone")
            self.load_voice_commands()

    def reload_voice_command(self):
        self.current_settings = self.profile_manager.get_profile_settings()
        self.load_voice_commands()