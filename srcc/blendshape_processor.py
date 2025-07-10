import time
import pyautogui

class BlendshapeProcessor:    
    def __init__(self, profile_manager=None):
        self.profile_manager = profile_manager
        
        self.default_threshold = 0.5
        self.bindings = []
        self.priority_order = []
        
        self.active_key = None 
        self.active_action = None

        self.is_enabled = False

        self.blendshapes = [
            "browInnerUp", "browDownLeft",
            "mouthLeft", "mouthRight", "mouthSmileLeft", 
            "mouthFunnel", "mouthRollLower", "jawOpen", "mouthShrugLower"
            # "eyeBlinkLeft", "eyeBlinkRight"
        ]

        self.priority_order = ["mouthShrugLower", "browDownLeft", "mouthLeft", "mouthRight",
                               "mouthRollLower", "mouthFunnel", "mouthSmileLeft", "jawOpen", "browInnerUp"]

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
            ]
        }

        if profile_manager:
            self.load_from_profile()
    
    def load_from_profile(self):
        profile_settings = self.profile_manager.get_profile_settings()
        bs_settings = profile_settings.get("blendshape_bindings", {})

        if not bs_settings:
            profile_settings["blendshape_bindings"] = {
                "bindings": [
                    {"blendshape": "jawOpen", "action": "mouse_click", "threshold": 0.5},
                    {"blendshape": "eyeBlinkLeft", "action": "key_left", "threshold": 0.7},
                    {"blendshape": "eyeBlinkRight", "action": "key_right", "threshold": 0.7}
                ],
                "priority_order": ["jawOpen", "eyeBlinkLeft", "eyeBlinkRight"],
                "threshold": 0.5,
                "cooldown": 0.01
            }
            self.update_profile(self.profile_manager)
        
        self.bindings = bs_settings.get("bindings", [])
        self.priority_order = bs_settings.get("priority_order", [])
        self.default_threshold = bs_settings.get("threshold", 0.5)
        self.cooldown = bs_settings.get("cooldown", 0.5)

    def enable(self):
        self.is_enabled = True
        
    def disable(self):
        self.is_enabled = False
        if self.active_key:
            self._release_key()

    def update_profile(self, profile_manager):
        try:
            profile_name = self.profile_manager.get_current_profile_name()
            profile_settings = self.profile_manager.load_profile(profile_name)
            
            if "blendshape_bindings" not in profile_settings:
                profile_settings["blendshape_bindings"] = {}
                
            profile_settings['blendshape_bindings']['bindings'] = self.bindings
            profile_settings['blendshape_bindings']['priority_order'] = self.priority_order
            profile_settings['blendshape_bindings']['threshold'] = self.default_threshold
            profile_settings['blendshape_bindings']['cooldown'] = self.cooldown
            
            self.profile_manager.save_profile(profile_name, profile_settings)
            return True
        except Exception as e:
            print(f"Profile update error: {e}")
            return False
        
    def save_to_profile(self):
        if not self.profile_manager:
            return
            
        try:
            profile_name = self.profile_manager.get_current_profile_name()
            profile_settings = self.profile_manager.load_profile(profile_name)
            
            if "blendshape_bindings" not in profile_settings:
                profile_settings["blendshape_bindings"] = {}
                
            profile_settings["blendshape_bindings"]["bindings"] = self.bindings
            profile_settings["blendshape_bindings"]["priority_order"] = self.priority_order
            profile_settings["blendshape_bindings"]["threshold"] = self.default_threshold
            profile_settings["blendshape_bindings"]["cooldown"] = self.cooldown
            
            self.profile_manager.save_profile(profile_name, profile_settings)
            print("Saved blendshape settings to profile")
        except Exception as e:
            print(f"Error saving blendshape settings: {e}")
    
    def update_blendshape(self, blendshapes):
        self.current_blendshapes = blendshapes

        if not self.is_enabled:
            if self.active_key:
                self._release_key()
            return None, 0

        if not blendshapes:
            if self.active_key:
                self._release_key()
            return None, 0
        
        action, value = self.process_blendshapes(blendshapes)

        if self.active_action == "scroll_up":
            pyautogui.scroll(5 )  
        elif self.active_action == "scroll_down":
            pyautogui.scroll(5)

        return action, value

    def process_blendshapes(self, blendshapes):
        if not blendshapes:
            if self.active_key:
                self._release_key()
            return None, 0
        
        current_time = time.time()
        blendshape_values = {}
        
        for blendshape in blendshapes:
            name = blendshape.category_name
            value = blendshape.score
            blendshape_values[name] = value
        
        if self.active_key:
            if (self.active_key not in blendshape_values or 
                blendshape_values[self.active_key] < self._get_threshold(self.active_key)):
                self._release_key()
            else:
                return self.active_action, blendshape_values.get(self.active_key, 0)
        
        if not self.active_key:
            candidates = []
            
            for name, value in blendshape_values.items():
                binding = self._find_binding(name)
                if binding and value >= binding.get("threshold", self.default_threshold):
                    candidates.append({
                        "name": name,
                        "value": value,
                        "action": binding["action"],
                        "priority": self._get_priority(name)
                    })
            
            if candidates:
                candidates.sort(key=lambda x: x["priority"])
                selected = candidates[0]

                

                self._press_key(selected["name"], selected["action"])
                self.last_action = selected["action"]
                self.last_action_time = current_time
                
                return selected["action"], selected["value"]
        
        return None, 0
    
    def _find_binding(self, blendshape_name):
        for binding in self.bindings:
            if binding["blendshape"] == blendshape_name:
                return binding
        return None

    def _get_threshold(self, blendshape_name):
        binding = self._find_binding(blendshape_name)
        if binding:
            return binding.get("threshold", self.default_threshold)
        return self.default_threshold
    
    def _get_priority(self, blendshape_name):
        if blendshape_name in self.priority_order:
            return self.priority_order.index(blendshape_name)
        return float('inf') 
    
    def get_blendshape_value(self, blendshape_name):
        if hasattr(self, 'current_blendshapes') and self.current_blendshapes:
            for blendshape in self.current_blendshapes:
                if blendshape.category_name == blendshape_name:
                    return blendshape.score
        return 0.0

    def _press_key(self, blendshape_name, action):
        self.active_key = blendshape_name
        self.active_action = action
        
        try:
            if action in self.actions["mouse"]:
                if action in ["mouse_click", "mouse_left_click"]:
                    pyautogui.mouseDown(button="left")
                elif action == "mouse_right_click":
                    pyautogui.mouseDown(button="right")
                elif action == "mouse_middle_click":
                    pyautogui.mouseDown(button="middle")
                elif action in ["scroll_up", "scroll_down"]:
                    pass 
                    
            elif action.startswith("key_"):
                key = action[4:]  
                pyautogui.keyDown(key)
                
            print(f"Key Down: {blendshape_name} -> {action}")
        except Exception as e:
            print(f"Error pressing key: {e}")
            self.active_key = None
            self.active_action = None

    def _release_key(self):
        if not self.active_key or not self.active_action:
            return
            
        try:
            action = self.active_action
            
            if action in self.actions["mouse"]:
                if action in ["mouse_click", "mouse_left_click"]:
                    pyautogui.mouseUp(button="left")
                elif action == "mouse_right_click":
                    pyautogui.mouseUp(button="right")
                elif action == "mouse_middle_click":
                    pyautogui.mouseUp(button="middle")
                elif action in ["scroll_up", "scroll_down"]:
                    pass
                    
            elif action.startswith("key_"):
                key = action[4:] 
                pyautogui.keyUp(key)
                
            print(f"Key Up: {self.active_key} -> {action}")
        except Exception as e:
            print(f"Error releasing key: {e}")
        finally:
            self.active_key = None
            self.active_action = None

    def on_profile_change(self):
        self.load_from_profile()

    def get_available_blendshapes(self):
        return self.blendshapes
    
    def get_available_actions(self, category=None):
        if category and category in self.actions:
            return self.actions[category]
        elif category:
            return []  
        else:
            return self.actions
        
    def get_action_category(self, action):
        for category, actions in self.actions.items():
            if action in actions:
                return category
        return None
    
    def add_binding(self, blendshape, action, threshold=None):
        if threshold is None:
            threshold = self.default_threshold
            
        for binding in self.bindings:
            if binding["blendshape"] == blendshape:
                binding["action"] = action
                binding["threshold"] = threshold
                self.save_to_profile()
                return True
        
        self.bindings.append({
            "blendshape": blendshape,
            "action": action,
            "threshold": threshold
        })
        
        # if blendshape not in self.priority_order:
        #     self.priority_order.append(blendshape)
            
        self.save_to_profile()
        return True
    
    def remove_binding(self, blendshape):
        for i, binding in enumerate(self.bindings):
            if binding["blendshape"] == blendshape:
                self.bindings.pop(i)
                
                if blendshape in self.priority_order:
                    self.priority_order.remove(blendshape)
                    
                self.save_to_profile()
                return True
        
        return False
    
    def set_cooldown(self, cooldown):
        self.cooldown = max(0.0001, min(2.0, cooldown))
        self.save_to_profile()

    def set_bindings(self, bindings):
        self.bindings = bindings
        self.save_to_profile()
    
    def cleanup(self):
        if self.active_key:
            self._release_key()