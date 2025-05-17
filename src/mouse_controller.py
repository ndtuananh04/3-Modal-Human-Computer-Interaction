import numpy as np
import numpy.typing as npt
import pyautogui
from src.accel import SigmoidAccel
import time
from OneEuroFilter import OneEuroFilter

class MouseController:
    def __init__(self):
        # Cấu hình cho chuột
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0
        self.mincutoff = 1.0
        self.beta = 0.1
        config = {
            'freq': 120,       # Hz
            'mincutoff': self.mincutoff,  # Hz
            'beta': self.beta,       
            'dcutoff': 1.0    
            }

        self.f1 = OneEuroFilter(**config)
        self.f2 = OneEuroFilter(**config)
        # Cấu hình cho smoothing filter
        self.buffer_size = 15
        self.pointer_smooth = 15
        self.smooth_kernel = self.calc_smooth_kernel(self.pointer_smooth)
        self.prevvv = 0
        # Buffer cho các vị trí landmark thay vì vận tốc
        self.position_buffer = None
        self.delay_count = 0
        
        # Vị trí trước đó sau khi đã smooth
        self.prev_smooth_position = None
        
        # Hệ số ngưỡng chuyển động
        self.minimum_movement = 1
        
        # Hệ số scale cho vận tốc
        self.velocity_scale = 15.0

        self.accel = SigmoidAccel()
    def reset(self):
        config = {
            'freq': 120,       # Hz
            'mincutoff': self.mincutoff,  # Hz
            'beta': self.beta,       
            'dcutoff': 1.0    
            }

        self.f1 = OneEuroFilter(**config)
        self.f2 = OneEuroFilter(**config)

    def calc_smooth_kernel(self, n: int) -> npt.ArrayLike:
        kernel = np.hamming(n * 2)[:n]
        kernel = kernel / kernel.sum()
        return kernel.reshape(n, 1)

    def apply_smoothing(self, data: npt.ArrayLike) -> npt.ArrayLike:
        # smooth_n = len(self.smooth_kernel)
        # return np.sum(self.smooth_kernel * data[-smooth_n:], axis=0)
        return np.array([self.f1(data[-1:][0][0],time.time()),self.f2(data[-1:][0][1],time.time())])

        # self.prevvv = 0.15 * np.array([(data[-1:][0][0]),(data[-1:][0][1])]) + 0.85 * self.prevvv
        # return self.prevvv
    
    def update(self, current_position):
        # Khởi tạo buffer nếu chưa có
        if self.position_buffer is None:
            self.position_buffer = np.zeros([self.buffer_size, len(current_position)])
            
        # Cập nhật buffer với vị trí hiện tại
        self.position_buffer = np.roll(self.position_buffer, shift=-1, axis=0)
        self.position_buffer[-1] = current_position
        self.delay_count += 1
        
        # Nếu buffer đã đủ dữ liệu
        if self.delay_count >= self.buffer_size:
            # Áp dụng smoothing cho vị trí
            smooth_position = self.apply_smoothing(self.position_buffer)
            
            # Nếu đã có vị trí smooth trước đó, tính vận tốc
            if self.prev_smooth_position is not None:
                # Tính vận tốc từ vị trí đã được làm mượt
                vx = (smooth_position[0] - self.prev_smooth_position[0]) * self.velocity_scale
                vy = (smooth_position[1] - self.prev_smooth_position[1]) * self.velocity_scale
                
                vx *= self.accel(vx)
                vy *= self.accel(vy)

                # Di chuyển chuột nếu vận tốc đủ lớn
                if np.abs(vx) > self.minimum_movement or np.abs(vy) > self.minimum_movement:
                    pyautogui.moveRel(vx, vy, duration=0)
                
                # Lưu vị trí hiện tại và trả về vận tốc
                self.prev_smooth_position = smooth_position
                return vx, vy
            
            # Lưu vị trí hiện tại nếu chưa có vị trí trước đó
            self.prev_smooth_position = smooth_position
        
        return 0, 0
    
    def click(self):
        pyautogui.click()