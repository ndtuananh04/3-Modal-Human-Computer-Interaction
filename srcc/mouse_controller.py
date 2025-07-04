import numpy as np
import numpy.typing as npt
import pyautogui
from src.accel import SigmoidAccel
import time
from OneEuroFilter import OneEuroFilter
import threading
import queue

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
        config = {
            'freq': 120,      
            'mincutoff': self.mincutoff, 
            'beta': self.beta,       
            'dcutoff': 1.0    
            }

        self.f1 = OneEuroFilter(**config)
        self.f2 = OneEuroFilter(**config)
 
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
        self.f2 = OneEuroFilter(**config)
        self.prev_smooth_position = None

    def set_get_cursor(self, get_cursor_func):
        self.get_cursor = get_cursor_func
        print("Get cursor function set successfully")
    
    def apply_smoothing(self, point):
        current_time = time.time()
        return np.array([
            self.f1(point[0], current_time),
            self.f2(point[1], current_time)
        ])
    
    def move(self, current_position):
        smooth_position = self.apply_smoothing(current_position)
        
        if self.prev_smooth_position is not None:
            vx = (smooth_position[0] - self.prev_smooth_position[0]) * self.velocity_scale
            vy = (smooth_position[1] - self.prev_smooth_position[1]) * self.velocity_scale
            
            vx *= self.accel(vx)
            vy *= self.accel(vy)

            pyautogui.moveRel(vx/2, vy/2, duration=0)
            time.sleep(0.01)
            pyautogui.moveRel(vx, vy, duration=0)

            # self.mouse_mover.move(vx, vy, duration=0.022)

            self.prev_smooth_position = smooth_position
            return vx, vy
        
        self.prev_smooth_position = smooth_position
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