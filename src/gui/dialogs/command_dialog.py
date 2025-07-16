import tkinter as tk
import customtkinter as ctk
from src.gui.submenu import SubmenuDropdown

class CommandDialog:
    def __init__(self, parent, command_index, command_text, action_text, voice_processor, profile_manager):
        self.parent = parent
        self.command_index = command_index
        self.voice_processor = voice_processor
        self.profile_manager = profile_manager
        self.actions = voice_processor.get_available_actions()
        
        self._create_dialog(command_text, action_text)
    
    def _create_dialog(self, command_text, action_text):
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("Edit Voice Command")
        self.dialog.geometry("400x180")
        self.dialog.grab_set()
        
        frame = ctk.CTkFrame(self.dialog)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Command input
        cmd_label = ctk.CTkLabel(frame, text="Command:")
        cmd_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.cmd_var = tk.StringVar(value=command_text)
        cmd_entry = ctk.CTkEntry(frame, textvariable=self.cmd_var, width=250)
        cmd_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        cmd_entry.focus()
        
        # Action input
        action_label = ctk.CTkLabel(frame, text="Action:")
        action_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        self.action_var = action_text
        
        action_dropdown = SubmenuDropdown(
            frame,
            self.actions,
            self.action_var,
            callback=lambda action: setattr(self, 'action_var', action)
        )
        action_dropdown.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Buttons
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=15, sticky="ew")
        
        # Save button
        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save",
            command=self._save_changes,
            width=80
        )
        save_btn.pack(side="left", padx=10)
        
        # Delete button
        delete_btn = ctk.CTkButton(
            btn_frame,
            text="Delete",
            command=self._delete_command,
            width=80,
            fg_color="#FF5555",
            hover_color="#DD4444"
        )
        delete_btn.pack(side="left", padx=10)
        
        # Close button
        close_btn = ctk.CTkButton(
            btn_frame,
            text="Close",
            command=self.dialog.destroy,
            width=80
        )
        close_btn.pack(side="left", padx=10)
    
    def _save_changes(self):
        command = self.cmd_var.get().strip()
        action = self.action_var
        
        if not command or not action:
            print("Command and action cannot be empty")
            return
        
        success = self.voice_processor.update_command(self.command_index, command, action)
        if success:
            self.parent.reload_voice_command()
            self.dialog.destroy()
        else:
            print("Failed to update command")
    
    def _delete_command(self):
        # Show confirmation dialog
        confirm = ctk.CTkToplevel(self.dialog)
        confirm.title("Confirm Delete")
        confirm.geometry("300x120")
        confirm.grab_set()
        
        conf_frame = ctk.CTkFrame(confirm)
        conf_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        question = f'Delete command "{self.cmd_var.get()}"?'
        msg = ctk.CTkLabel(conf_frame, text=question)
        msg.pack(pady=10)
        
        conf_btn_frame = ctk.CTkFrame(conf_frame, fg_color="transparent")
        conf_btn_frame.pack(pady=10)
        
        # Yes button
        yes_btn = ctk.CTkButton(
            conf_btn_frame,
            text="Yes",
            command=self._confirm_delete,
            width=60,
            fg_color="#FF5555",
            hover_color="#DD4444"
        )
        yes_btn.pack(side="left", padx=10)
        
        # No button
        no_btn = ctk.CTkButton(
            conf_btn_frame,
            text="No",
            command=confirm.destroy,
            width=60
        )
        no_btn.pack(side="left", padx=10)
    
    def _confirm_delete(self):
        success = self.voice_processor.delete_command(self.command_index)
        if success:
            self.parent.reload_voice_command()
            self.dialog.destroy()


class AddCommandDialog:
    
    def __init__(self, parent, voice_processor, profile_manager):
        self.parent = parent
        self.voice_processor = voice_processor
        self.profile_manager = profile_manager
        self.actions = voice_processor.get_available_actions()
        self._create_dialog()
    
    def _create_dialog(self):
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("Add Voice Command")
        self.dialog.geometry("380x180")
        self.dialog.grab_set()
        
        frame = ctk.CTkFrame(self.dialog)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Command input
        cmd_label = ctk.CTkLabel(frame, text="Phrase:")
        cmd_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.cmd_var = tk.StringVar()
        cmd_entry = ctk.CTkEntry(frame, textvariable=self.cmd_var, width=250)
        cmd_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        cmd_entry.focus()
        
        # Action input
        action_label = ctk.CTkLabel(frame, text="Action:")
        action_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
    
        self.action_var = ""
        
        action_dropdown = SubmenuDropdown(
            frame,
            self.actions,
            self.action_var,
            callback=lambda action: setattr(self, 'action_var', action)
        )
        action_dropdown.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Buttons
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=10, sticky="ew")
        
        # Save button
        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save",
            command=self._save_command,
            width=80
        )
        save_btn.pack(side="left")
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.dialog.destroy,
            width=80
        )
        cancel_btn.pack(side="left", padx=(10, 0))
    
    def _save_command(self):
        command = self.cmd_var.get().strip()
        action = self.action_var
        
        if not command or not action:
            return
            
        success = self.voice_processor.add_command(command, action)
        if success:
            self.parent.reload_voice_command()
            self.dialog.destroy()