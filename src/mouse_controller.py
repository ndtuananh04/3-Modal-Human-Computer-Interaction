import numpy as np
import numpy.typing as npt
import pyautogui

class MouseController:
    def __init__(self):
        # Cấu hình cho chuột
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0
        
        # Cấu hình cho smoothing filter
        self.buffer_size = 10
        self.pointer_smooth = 10
        self.smooth_kernel = self.calc_smooth_kernel(self.pointer_smooth)
        
        # Buffer cho các vị trí landmark thay vì vận tốc
        self.position_buffer = None
        self.delay_count = 0
        
        # Vị trí trước đó sau khi đã smooth
        self.prev_smooth_position = None
        
        # Hệ số ngưỡng chuyển động
        self.minimum_movement = 1
        
        # Hệ số scale cho vận tốc
        self.velocity_scale = 20.0
    
    def calc_smooth_kernel(self, n: int) -> npt.ArrayLike:
        kernel = np.hamming(n * 2)[:n]
        kernel = kernel / kernel.sum()
        return kernel.reshape(n, 1)

    def apply_smoothing(self, data: npt.ArrayLike) -> npt.ArrayLike:
        smooth_n = len(self.smooth_kernel)
        return np.sum(self.smooth_kernel * data[-smooth_n:], axis=0)
    
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