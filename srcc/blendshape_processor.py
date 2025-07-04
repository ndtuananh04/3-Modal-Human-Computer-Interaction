# import time
# import pyautogui

# class BlendshapeController:
#     def __init__(self, profile_manager=None, mouse_controller=None):
#         self.profile_manager = profile_manager
#         self.mouse_controller = mouse_controller
        
#         self.default_threshold = 0.5
#         self.cooldown = 0.5
#         self.bindings = []
#         self.priority_order = []
        
#         self.last_action = None
#         self.last_action_time = 0
#         self.active_blendshapes = {}
        
#         self.load_from_profile()
    
#     def load_from_profile(self):
#         if not self.profile_manager:
#             return
        
#         profile_settings = self.profile_manager.get_profile_settings()
#         bs_settings = profile_settings.get("blendshape_bindings", {})
        
#         self.bindings = bs_settings.get("bindings", [])
#         self.priority_order = bs_settings.get("priority_order", [])
#         self.default_threshold = bs_settings.get("threshold", 0.5)
#         self.cooldown = bs_settings.get("cooldown", 0.5)
    
#     def process_blendshapes(self, blendshapes):
#         """
#         Process blendshapes and return action to execute
        
#         Args:
#             blendshapes: List of blendshape objects from MediaPipe face mesh
            
#         Returns:
#             tuple: (action, value) or (None, 0) if no action should be performed
#         """
#         if not blendshapes:
#             return None, 0
        
#         # Convert to dictionary for easier access
#         current_time = time.time()
#         blendshape_dict = {}
        
#         for blendshape in blendshapes:
#             name = blendshape.category_name
#             value = blendshape.score
#             blendshape_dict[name] = value
            
#             # Track active blendshapes that exceed their threshold
#             for binding in self.bindings:
#                 if binding["blendshape"] == name:
#                     threshold = binding.get("threshold", self.default_threshold)
#                     if value >= threshold:
#                         self.active_blendshapes[name] = {
#                             "value": value,
#                             "action": binding["action"],
#                             "time": current_time
#                         }
#                     elif name in self.active_blendshapes:
#                         # Remove if no longer active
#                         del self.active_blendshapes[name]
        
#         # Check cooldown
#         if self.last_action and (current_time - self.last_action_time) < self.cooldown:
#             return None, 0
        
#         # Find highest priority active blendshape
#         selected_action = None
#         selected_value = 0
#         selected_priority = float('inf')
        
#         for bs_name, data in self.active_blendshapes.items():
#             # Find priority of this blendshape
#             priority = float('inf')
#             if bs_name in self.priority_order:
#                 priority = self.priority_order.index(bs_name)
            
#             # Select if higher priority (lower index)
#             if priority < selected_priority:
#                 selected_priority = priority
#                 selected_action = data["action"]
#                 selected_value = data["value"]
        
#         if selected_action:
#             self.last_action = selected_action
#             self.last_action_time = current_time
            
#         return selected_action, selected_value
    
#     def execute_action(self, action):
#         """
#         Execute the specified action
        
#         Args:
#             action: String identifier for the action
            
#         Returns:
#             bool: True if action was executed successfully
#         """
#         if not action:
#             return False
            
#         try:
#             # Mouse actions
#             if action == "mouse_click":
#                 pyautogui.click()
#                 return True
                
#             elif action == "mouse_right_click":
#                 pyautogui.rightClick()
#                 return True
                
#             elif action == "mouse_double_click":
#                 pyautogui.doubleClick()
#                 return True
                
#             elif action == "scroll_up":
#                 pyautogui.scroll(10)
#                 return True
                
#             elif action == "scroll_down":
#                 pyautogui.scroll(-10)
#                 return True
                
#             # Mouse speed actions
#             elif action == "increase_mouse_speed":
#                 if self.mouse_controller:
#                     current = self.mouse_controller.velocity_scale
#                     self.mouse_controller.velocity_scale = min(30, current + 2)
#                     print(f"Increased mouse speed to {self.mouse_controller.velocity_scale}")
#                 return True
                
#             elif action == "decrease_mouse_speed":
#                 if self.mouse_controller:
#                     current = self.mouse_controller.velocity_scale
#                     self.mouse_controller.velocity_scale = max(5, current - 2)
#                     print(f"Decreased mouse speed to {self.mouse_controller.velocity_scale}")
#                 return True
                
#             # Keyboard actions
#             elif action.startswith("key_"):
#                 key = action[4:]
#                 pyautogui.press(key)
#                 print(f"Pressed key: {key}")
#                 return True
            
#             # Hotkey actions
#             elif action.startswith("hotkey_"):
#                 keys = action[7:].split('+')
#                 pyautogui.hotkey(*keys)
#                 print(f"Pressed hotkey: {'+'.join(keys)}")
#                 return True
                
#             else:
#                 print(f"Unknown action: {action}")
#                 return False
                
#         except Exception as e:
#             print(f"Error executing action {action}: {e}")
#             return False
    
#     def on_profile_change(self):
#         """Called when profile changes to reload settings"""
#         self.load_from_profile()
#         self.active_blendshapes = {}
#         self.last_action = None