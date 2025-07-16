import numpy as np
import numpy.typing as npt
import pyautogui
from src.accel import SigmoidAccel
import time
from src.modified_oneEuroFilter import OneEuroFilter
import threading
import queue
import math
# class MouseMoverThread(threading.Thread):
#     def __init__(self):
#         super().__init__(daemon=True)
#         self.queue = queue.Queue()
#         self.running = True
    
#     def run(self):
#         while self.running:
#             try:
#                 if not self.queue.empty():
#                     vx, vy, duration = self.queue.get(block=False)
#                     pyautogui.moveRel(vx, vy, duration=duration)
#                     self.queue.task_done()
#                 else:
#                     time.sleep(0.001)  # Ngủ ngắn khi không có công việc
    
#             except Exception as e:
#                 print(f"Error in mouse mover thread: {e}")
    
#     def move(self, vx, vy, duration=0.016):
#         self.queue.put((vx, vy, duration))
    
#     def stop(self):
#         self.running = False

class MouseController:
    def __init__(self):
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0
        pyautogui.MINIMUM_DURATION = 0
        pyautogui.MINIMUM_SLEEP = 0.0049
        self.mincutoff = 0.5
        self.beta = 0.07
        self.vx = 0
        self.vy = 0
        config = {
            'freq': 30,      
            'mincutoff': self.mincutoff, 
            'beta': self.beta,       
            'dcutoff': 1.0    
            }

        self.f1 = OneEuroFilter(**config)
 
        self.position_buffer = None
        self.prev_smooth_position = None
        self.velocity_scale = 20.0
        self.accel = SigmoidAccel()
        self.get_cursor = None

        self.tracking_active = False

        self.update_thread = None
        self.running = False
        self.update_interval = 0.005
        self.lock = threading.Lock()
        self.previous_cursor = None
        self.tmp = time.time()

        # self.mouse_mover = MouseMoverThread()
        # self.mouse_mover.start()

    def reset(self):
        config = {
            'freq': 120,      
            'mincutoff': self.mincutoff,  
            'beta': self.beta,       
            'dcutoff': 1.0    
            }
        self.f1 = OneEuroFilter(**config)
        self.prev_smooth_position = None

    def set_get_cursor(self, get_cursor_func):
        self.get_cursor = get_cursor_func
        print("Get cursor function set successfully")
    
    def apply_smoothing(self, point):
        current_time = time.time()
        return self.f1(math.sqrt(point[0]**2+point[1]**2), current_time)
    
    def move(self, current_position):
        _, alpha = self.apply_smoothing(current_position)
        
        if self.prev_smooth_position is not None:
            self.vx, self.vy  = ((current_position - self.prev_smooth_position) * alpha + (1 - alpha) * (np.array([self.vx, self.vy])))
            self.prev_smooth_position = current_position
            vx = -self.vx*self.accel(self.vx*self.velocity_scale)*self.velocity_scale
            vy = self.vy*self.accel(self.vy*self.velocity_scale)*self.velocity_scale
            #vx = -self.vx*self.velocity_scale
            #vy = self.vy*self.velocity_scale
            pyautogui.moveRel(vx/2, vy/2, duration=0)
            time.sleep(0.01)
            pyautogui.moveRel(vx/2, vy/2, duration=0)

            # self.mouse_mover.move(vx, vy, duration=0.022)

            return vx, vy
        else:
            self.prev_smooth_position = current_position
            # self.mouse_mover.move(vx, vy, duration=0.022)
        return 0, 0
    
    def update_loop(self, cursor_pos=None):
        try:
            if self.tracking_active and cursor_pos is not None:
                # cursor_pos = self.get_cursor()
                # if np.array_equal(cursor_pos, self.previous_cursor):
                #     continue
                # print(f"Cursor Position: {cursor_pos}")
                self.move(cursor_pos)
                # print(time.time())
                # self.previous_cursor = np.array(cursor_pos)
        except Exception as e:
            print(f"Error in mouse update loop: {e}")
        
        # time.sleep(self.update_interval)

    def start_tracking(self):
        with self.lock:
            self.tracking_active = True
            self.prev_smooth_position = None

            # if self.update_thread is None or not self.update_thread.is_alive():
            #         self.running = True
            #         self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
            #         self.update_thread.start()

            print("Mouse tracking started")
        
    def stop_tracking(self):
        self.tracking_active = False
        print("Mouse tracking stopped")
    
    def click(self):
        pyautogui.click()

    def increase_speed(self, step=5):
        try:
            current = self.velocity_scale
            new_speed = min(50, current + step) 
            self.velocity_scale = new_speed
            return True
        except Exception as e:
            print(f"Error increasing mouse speed: {e}")
            return False

    def decrease_speed(self, step=5):
        try:
            current = self.velocity_scale
            new_speed = max(1, current - step) 
            self.velocity_scale = new_speed
            return True
        except Exception as e:
            print(f"Error decreasing mouse speed: {e}")
            return False