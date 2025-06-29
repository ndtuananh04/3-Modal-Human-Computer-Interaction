import threading
import time
import json
import os
import pythoncom
from dragonfly import Grammar, CompoundRule
from dragonfly.engines.backend_sapi5.engine import Sapi5InProcEngine

class VoiceProcessor:
    def __init__(self, profile_manager):
        self.stop_flag = threading.Event()
        self.profile_manager = profile_manager
        self.thread = None
        self.engine = None
        self.grammar = None
        self.commands = []
        self.selected_microphone = None
        
    def initialize(self):
        try:
            self.engine = Sapi5InProcEngine()
            self.engine.connect()
            
            self.grammar = Grammar("voice_commands")
            
            self.load_commands_from_profile(self.profile_manager)
            
            self.configure_microphone()
            
            return True
        except Exception as e:
            print(f"Init voice processor error: {e}")
            return False
    
    def configure_microphone(self):
        if not self.engine:
            return
            
        try:
            audio_sources = self.engine.get_audio_sources()
            
            if self.selected_microphone:
                for i, (index, description, handle) in enumerate(audio_sources):
                    if description == self.selected_microphone:
                        self.engine.select_audio_source(i)
                        print(f"Đã chọn microphone: {self.selected_microphone}")
                        break
                else:
                    print("Không tìm thấy microphone đã chọn. Sử dụng microphone mặc định.")
            else:
                print("Không có microphone được chọn. Sử dụng microphone mặc định.")
        except Exception as e:
            print(f"Lỗi cấu hình microphone: {e}")
    
    def create_rules(self):
        if not self.grammar:
            return
            
        self.grammar.unload()
        command_rule = VoiceCommandRule(
            self.commands
        )
        
        self.grammar.add_rule(command_rule)
        
        self.grammar.load()
    
    def get_available_microphones(self):
        if not self.engine:
            self.engine = Sapi5InProcEngine()
            self.engine.connect()
            
        audio_sources = self.engine.get_audio_sources()
        microphones = [source[1] for source in audio_sources]
        return microphones
    
    def process_voice(self):
        pythoncom.CoInitialize() 
        
        try:
            while not self.stop_flag.is_set():
                pythoncom.PumpWaitingMessages()
                # time.sleep(0.1)
        except Exception as e:
            print(f"Processing error: {e}")
        finally:
            pythoncom.CoUninitialize()
    
    def start(self):
        if not self.thread or not self.thread.is_alive():
            if not self.engine:
                self.initialize()
                
            self.stop_flag.clear()
            self.thread = threading.Thread(target=self.process_voice)
            self.thread.daemon = True
            self.thread.start()
            print("Voice processor started")
            return True
        return False
    
    def stop(self):
        self.stop_flag.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        
        if self.grammar:
            try:
                self.grammar.unload()
            except:
                pass
        
        if self.engine:
            try:
                self.engine.disconnect()
            except:
                pass
            
        print("Voice processor stopped")
    
    def load_commands_from_profile(self, profile_manager):
        try:
            profile_settings = profile_manager.get_profile_settings()
            voice_settings = profile_settings.get("voice_processor", {})
            self.commands = voice_settings.get("commands", [])
            self.selected_microphone = voice_settings.get("selected_microphone", None)
            self.create_rules()
        except Exception as e:
            print(f"Lỗi khi tải commands từ profile: {e}")
            self.commands = []
    
    def update_profile(self, profile_manager):
        try:
            profile_name = profile_manager.get_current_profile_name()
            profile_settings = profile_manager.load_profile(profile_name)
            
            if "voice_processor" not in profile_settings:
                profile_settings["voice_processor"] = {}
                
            profile_settings["voice_processor"]["commands"] = self.commands
            profile_settings["voice_processor"]["selected_microphone"] = self.selected_microphone
            
            profile_manager.save_profile(profile_name, profile_settings)
            return True
        except Exception as e:
            print(f"Lỗi khi cập nhật profile: {e}")
            return False
    
    def set_microphone(self, microphone, profile_manager=None):
        self.selected_microphone = microphone
        self.configure_microphone()
        
        if profile_manager:
            self.update_profile(profile_manager)
        
        return True
    
    def add_command(self, command, action, profile_manager=None):
        for cmd in self.commands:
            if cmd["command"] == command:
                return False
        
        self.commands.append({
            "command": command,
            "action": action
        })
        
        if self.grammar:
            self.create_rules()
        
        if profile_manager:
            self.update_profile(profile_manager)
        
        return True
    
    def update_command(self, index, command, action, profile_manager=None):
        if index < 0 or index >= len(self.commands):
            return False
        
        self.commands[index] = {
            "command": command,
            "action": action
        }
        
        if self.grammar:
            self.create_rules()
        
        if profile_manager:
            self.update_profile(profile_manager)
        
        return True
    
    def delete_command(self, index, profile_manager=None):
        if index < 0 or index >= len(self.commands):
            return False
        
        del self.commands[index]
        
        if self.grammar:
            self.create_rules()
        
        if profile_manager:
            self.update_profile(profile_manager)
        
        return True
    
    def on_profile_change(self, profile_manager):
        self.load_commands_from_profile(profile_manager)

class VoiceCommandRule(CompoundRule):
    def __init__(self, commands):
        self.commands = commands
        
        specs = []
        for cmd in commands:
            specs.append(f'"{cmd["command"]}"')
        
        if specs:
            self.spec = " | ".join(specs)
        else:
            self.spec = '"dummy command"'
        
        super(VoiceCommandRule, self).__init__()

    def _process_recognition(self, node, extras):
        words = node.words()
        recognized_text = " ".join(words).lower()
        
        for command in self.commands:
            if command["command"].lower() == recognized_text:
                print(f"Đã nhận dạng lệnh: {command['command']}")
                
        else:
            print(f"Lệnh không được nhận dạng: {recognized_text}")