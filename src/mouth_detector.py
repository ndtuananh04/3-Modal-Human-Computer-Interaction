import cv2
import numpy as np
import time
from src.face_utils import calculate_point_to_line_distance

class MouthDetector:
    def __init__(self):
        # Biến để lưu trữ thông số calibrate
        self.smile_calibrated = False
        self.mouth_width_thres = 0
        self.lip_curve_thres = 0
        
        # Biến để lưu trữ thông số mở miệng
        self.open_mouth_calibrated = False
        self.lip_distance_thres = 0

        self.MOUTH_LANDMARKS = {
            'top_lip': 0,      # Điểm giữa môi trên
            'bottom_lip': 17,   # Điểm giữa môi dưới
            'left_corner': 61,  # Góc miệng bên trái
            'right_corner': 291 # Góc miệng bên phải
        }

    def detect_smile(self, landmarks, h, w):
        """Phát hiện nụ cười dựa trên các landmark khuôn mặt."""
        if not self.smile_calibrated:
            return False
        
        left_corner = landmarks.landmark[self.MOUTH_LANDMARKS['left_corner']]
        right_corner = landmarks.landmark[self.MOUTH_LANDMARKS['right_corner']]
        bottom_lip = landmarks.landmark[self.MOUTH_LANDMARKS['bottom_lip']]
        
        mouth_width = abs(left_corner.x * w - right_corner.x * w)
        lip_curve = calculate_point_to_line_distance(bottom_lip, left_corner, right_corner, w, h)
        
        return np.logical_and(mouth_width > self.mouth_width_thres, 
                              lip_curve > self.lip_curve_thres).item()
    
    def detect_open_mouth(self, landmarks, h, w):
        """Phát hiện mở miệng dựa trên khoảng cách giữa môi trên và dưới."""
        if not self.open_mouth_calibrated:
            return False
        
        # Tính khoảng cách giữa điểm giữa môi trên và môi dưới
        top_lip = landmarks.landmark[self.MOUTH_LANDMARKS['top_lip']]
        bottom_lip = landmarks.landmark[self.MOUTH_LANDMARKS['bottom_lip']]
        
        # Tính khoảng cách theo pixel
        lip_distance = abs(top_lip.y * h - bottom_lip.y * h)
        
        # So sánh với ngưỡng đã hiệu chỉnh
        return lip_distance > self.lip_distance_thres
    
    @property
    def calibrated(self):
        """Kiểm tra xem đã hiệu chỉnh cả hai chức năng chưa."""
        return self.smile_calibrated and self.open_mouth_calibrated