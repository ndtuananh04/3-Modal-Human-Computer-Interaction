import threading
import time
import json
import os
import pythoncom
import pyautogui
from dragonfly import Grammar, CompoundRule
from dragonfly.engines.backend_sapi5.engine import Sapi5InProcEngine

class VoiceProcessor:
    def __init__(self, profile_manager, mouse_controller, blendshape_processor=None):
        self.available_microphones = []
        self.stop_flag = threading.Event()
        self.profile_manager = profile_manager
        self.mouse_controller = mouse_controller
        self.blendshape_processor = blendshape_processor
        self.thread = None
        self.engine = None
        self.grammar = None
        self.commands = []
        self.selected_microphone = None
        self.available_microphones = []
        self.actions = {
            "mouse": [
                "mouse_click", 
                "mouse_right_click", 
                "mouse_middle_click",
                "mouse_double_click",
                "scroll_up", 
                "scroll_down"
            ],
            "basic_keys": [
                "key_space", 
                "key_enter", 
                "key_tab", 
                "key_escape", 
                "key_backspace", 
                "key_delete"
            ],
            "arrow_keys": [
                "key_up", 
                "key_down", 
                "key_left", 
                "key_right"
            ],
            "number_keys": [
                "key_0", "key_1", "key_2", "key_3", "key_4", 
                "key_5", "key_6", "key_7", "key_8", "key_9"
            ],
            "letter_keys": [
                "key_a", "key_b", "key_c", "key_d", "key_e", "key_f", "key_g",
                "key_h", "key_i", "key_j", "key_k", "key_l", "key_m", "key_n",
                "key_o", "key_p", "key_q", "key_r", "key_s", "key_t", "key_u",
                "key_v", "key_w", "key_x", "key_y", "key_z"
            ],
            "function_keys": [
                "key_f1", "key_f2", "key_f3", "key_f4", "key_f5", "key_f6",
                "key_f7", "key_f8", "key_f9", "key_f10", "key_f11", "key_f12"
            ],
            "hotkeys_system": [
                "hotkey_ctrl+c",        
                "hotkey_ctrl+v",        
                "hotkey_ctrl+x",       
                "hotkey_ctrl+z",        
                "hotkey_ctrl+y",        
                "hotkey_ctrl+s",        
                "hotkey_ctrl+a",        
                "hotkey_ctrl+f",        
                "hotkey_ctrl+h",        
                "hotkey_ctrl+n",       
                "hotkey_ctrl+o",        
                "hotkey_ctrl+p",        
                "hotkey_ctrl+w",        
                "hotkey_ctrl+q",         
                "hotkey_alt+f4",        
                "hotkey_alt+tab",      
                "hotkey_win+d",          
                "hotkey_win+l",          
                "hotkey_win+r",       
            ],
            "modifiers": [
                "increase_mouse_speed",
                "decrease_mouse_speed"
            ]
        }

        self.initialize()
        
    def initialize(self):
        try:
            print("Initializing voice processor...")
            self.engine = Sapi5InProcEngine()
            self.engine.connect()

            self.available_microphones = self.get_available_microphones()
            
            self.load_commands_from_profile(self.profile_manager)

            self.grammar = Grammar("voice_commands")
            # self.create_rules()
            
            self.configure_microphone()
            
            return True
        except Exception as e:
            print(f"Init voice processor error: {e}")
            return False
    
    def configure_microphone(self):
        if not self.engine:
            print("engine is not initialized")
            return
 
        try:
            audio_sources = self.engine.get_audio_sources()
            print(f"Available audio sources: {audio_sources}")
            if self.selected_microphone:
                for i, (index, description, handle) in enumerate(audio_sources):
                    if description == self.selected_microphone:
                        self.engine.select_audio_source(i)
                        print(f"Choose microphone: {self.selected_microphone}")
                        break
                    else:
                        print("Microphone not found, default.")
            else:
                print("No microphone selected, using default.")
        except Exception as e:
            print(f"Microphone configure error: {e}")
    
    def create_rules(self):
        if not self.grammar:
            return
        
        if self.grammar.loaded:
            self.grammar.unload()

        for rule in list(self.grammar.rules):
            self.grammar.remove_rule(rule)

        command_rule = VoiceCommandRule(self.commands, self.mouse_controller, self.actions, self.blendshape_processor)
        self.grammar.add_rule(command_rule)
        
        self.grammar.load()
    
    def get_available_microphones(self):
        if not self.engine:
            self.engine = Sapi5InProcEngine()
            self.engine.connect()
            
        audio_sources = self.engine.get_audio_sources()
        microphones = [source[1] for source in audio_sources]
        self.available_microphones = microphones
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
        if self.thread and self.thread.is_alive():
            print("Voice processor already running")
            return False
        
        if self.grammar and not self.grammar.loaded:
            try:
                self.create_rules() 
            except Exception as e:
                print(f"Error loading grammar: {e}")
                import traceback
                traceback.print_exc()

        try:
            self.stop_flag.clear()
            self.thread = threading.Thread(target=self.process_voice)
            self.thread.daemon = True
            self.thread.start()
            print("Voice processor started")
            return True
        except Exception as e:
            print(f"Error starting voice processor: {e}")
            return False
    
    def stop(self):
        try:
            self.stop_flag.set()
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=1)
            print("Voice processor stopped")

            if self.grammar and self.grammar.loaded:
                try:
                    self.grammar.unload()
                    print("Grammar unloaded")
                except Exception as e:
                    print(f"Error unloading grammar: {e}")
            return True
        except Exception as e:
            print(f"Error stopping voice processor: {e}")
            return False
    
    def load_commands_from_profile(self, profile_manager):
        try:
            profile_settings = profile_manager.get_profile_settings()
            voice_settings = profile_settings.get("voice_processor", {})
            self.commands = voice_settings.get("commands", [])
            self.selected_microphone = voice_settings.get("selected_microphone", None)

            if not self.commands:
                    self.commands = [
                        {"command": "click", "action": "mouse_click"},
                        {"command": "double click", "action": "mouse_double_click"},
                        {"command": "scroll up", "action": "scroll_up"},
                        {"command": "scroll down", "action": "scroll_down"}
                    ]
                    self.update_profile(profile_manager)
            return True
        except Exception as e:
            print(f"Lỗi khi tải commands từ profile: {e}")
            self.commands = []
            return False
    
    def update_profile(self, profile_manager=None):
        try:
            profile_name = self.profile_manager.get_current_profile_name()
            profile_settings = self.profile_manager.load_profile(profile_name)
            
            if "voice_processor" not in profile_settings:
                profile_settings["voice_processor"] = {}
                
            profile_settings["voice_processor"]["commands"] = self.commands
            profile_settings["voice_processor"]["selected_microphone"] = self.selected_microphone
            
            self.profile_manager.save_profile(profile_name, profile_settings)
            return True
        except Exception as e:
            print(f"Profile update error: {e}")
            return False
    
    def set_microphone(self, microphone):
        try:
            self.selected_microphone = microphone
            self.configure_microphone()

            self.update_profile()
            
            return True
        except Exception as e:
            print(f"Error setting microphone: {e}")
            return False
    
    def add_command(self, command, action):
        for cmd in self.commands:
                if cmd.get("command", "") == command:
                    print(f"Command '{command}' already exists")
                    return False
        
        self.commands.append({
            "command": command,
            "action": action
        })
        
        if self.grammar:
            self.create_rules()
        
        self.update_profile()
        
        return True
    
    def update_command(self, index, command, action):
        if index < 0 or index >= len(self.commands):
            return False

        self.commands[index] = {
            "command": command,
            "action": action
        }

        if self.grammar:
            self.create_rules()
        
        self.update_profile()
            
        return True
    
    def delete_command(self, index, profile_manager=None):
        if index < 0 or index >= len(self.commands):
            return False
        
        del self.commands[index]
        
        if self.grammar:
            self.create_rules()
        
        self.update_profile()
        
        return True

    def on_profile_change(self):
        self.load_commands_from_profile(self.profile_manager)
        self.configure_microphone()
        if self.grammar:
            self.create_rules()
        
    def get_available_actions(self, category=None):
        if category and category in self.actions:
            return self.actions[category]
        elif category:
            return []  
        else:
            return self.actions
        
    def set_blendshape_processor(self, blendshape_processor):
        self.blendshape_processor = blendshape_processor


class VoiceCommandRule(CompoundRule):
    def __init__(self, commands, mouse_controller=None, actions=None, blendshape_processor=None):
        self.commands = commands
        self.mouse_controller = mouse_controller
        self.blendshape_processor = blendshape_processor
        self.actions = actions
        
        specs = []
        for cmd in commands:
            cmd_text = cmd.get("command", "")
            if cmd_text:
                specs.append(f'"{cmd_text}"')
        
        if specs:
            self.spec = " | ".join(specs)
        else:
            self.spec = '"dummy command"'
        
        super(VoiceCommandRule, self).__init__()

    def _process_recognition(self, node, extras):
        words = node.words()
        recognized_text = " ".join(words).lower()
        recognized_text = recognized_text.replace('"', '')
        
        for command in self.commands:
            if command.get("command", "").lower() == recognized_text:
                action = command.get("action", "")
                print(f"Command recognized: {command['command']} -> {command['action']}")
                
                if not self.blendshape_processor.is_mouth_recently_open():
                    print("Voice command blocked: Mouth not open in recent 50 frames")
                    return
                self.execute_action(action)
                return action
                
        print(f"Command not recognized: {recognized_text}")
        return None
        
    def execute_action(self, action):
        print(f"Executing action: {action}")
        
        try:
            if action in self.actions["mouse"]:
                if action == "mouse_click":
                    pyautogui.click()
                elif action == "mouse_right_click":
                    pyautogui.click(button='right')
                elif action == "mouse_middle_click":
                    pyautogui.click(button="middle")
                elif action == "mouse_double_click":
                    pyautogui.doubleClick()
                elif action in ["scroll_up", "scroll_down"]:
                    pass 
                
            elif action == "increase_mouse_speed":
                return self.mouse_controller.increase_speed()
                    
            elif action == "decrease_mouse_speed":
                return self.mouse_controller.decrease_speed()
                    
            elif action.startswith("key_"):
                key = action[4:] 
                pyautogui.press(key)
                print(f"Pressed key: {key}")
                return True
            
            elif action.startswith("hotkey_"):
                keys = action[7:].split('+')  
                pyautogui.hotkey(*keys)
                print(f"Pressed hotkey: {'+'.join(keys)}")
                return True
                
            else:
                print(f"Unknown action: {action}")
                return False
                
        except Exception as e:
            print(f"Error executing action {action}: {e}")
            import traceback
            traceback.print_exc()
            return False
