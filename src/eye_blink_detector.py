import cv2
import numpy as np

class EyeBlinkDetector:
    """Lớp nhận diện nháy mắt trái/phải."""
    
    def __init__(self):
        # Ngưỡng tỷ lệ đóng mắt để xác định nháy mắt
        self.blink_threshold = 0.2
        
        # Các landmark chính cho mắt trái
        self.LEFT_EYE_POINTS = [33, 160, 158, 133, 153, 144]
        
        # Các landmark chính cho mắt phải
        self.RIGHT_EYE_POINTS = [362, 385, 387, 263, 373, 380]
    
    def detect_left_eye_blink(self, face_landmarks, image_height, image_width):
        """Phát hiện nháy mắt trái dựa trên tỷ lệ mở mắt."""
        if not face_landmarks:
            return False
        
        # Tính toán tỷ lệ mở mắt
        eye_ratio = self._calculate_eye_aspect_ratio(face_landmarks, self.LEFT_EYE_POINTS)
        
        # Nếu tỷ lệ < ngưỡng, coi như đã nháy mắt
        return eye_ratio < self.blink_threshold
    
    def detect_right_eye_blink(self, face_landmarks, image_height, image_width):
        """Phát hiện nháy mắt phải dựa trên tỷ lệ mở mắt."""
        if not face_landmarks:
            return False
        
        # Tính toán tỷ lệ mở mắt
        eye_ratio = self._calculate_eye_aspect_ratio(face_landmarks, self.RIGHT_EYE_POINTS)
        
        # Nếu tỷ lệ < ngưỡng, coi như đã nháy mắt
        return eye_ratio < self.blink_threshold
    
    def _calculate_eye_aspect_ratio(self, face_landmarks, eye_points):
        """Tính toán tỷ lệ khía cạnh của mắt."""
        # Lấy tọa độ các điểm của mắt
        points = [face_landmarks.landmark[idx] for idx in eye_points]
        
        # Tính khoảng cách dọc giữa mi trên và mi dưới
        vertical_dist = abs(points[1].y - points[4].y) + abs(points[2].y - points[5].y)
        
        # Tính khoảng cách ngang của mắt
        horizontal_dist = abs(points[0].x - points[3].x)
        
        # Tính tỷ lệ: height/width - nếu mắt đóng, tỷ lệ này sẽ rất nhỏ
        if horizontal_dist == 0:
            return 0  # Tránh chia cho 0
        
        return vertical_dist / (2 * horizontal_dist)