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
    
    # def calibrate_with_landmarks(self, mesh_results):
    #     if not mesh_results.multi_face_landmarks:
    #         print("Không tìm thấy khuôn mặt để hiệu chỉnh")
    #         return False
        
    #     # Dữ liệu tạm
    #     # neutral_mouth_width = 0
    #     # neutral_lip_curve = 0
    #     # smiling_mouth_width = 0
    #     # smiling_lip_curve = 0
        
    #     # Thực hiện quy trình tương tự như calibrate
    #     # Sử dụng kết quả nhận diện có sẵn thay vì thực hiện lại
    #     face_landmarks = mesh_results.multi_face_landmarks[0]
        
    #     # Xác định kích thước ảnh
    #     # Sử dụng giá trị mặc định hoặc lấy từ trường hợp gần nhất
    #     h, w = 480, 640  # Giá trị mặc định, tương ứng với kích thước camera
        
    #     # Lấy các landmark của miệng
    #     top_lip = face_landmarks.landmark[self.MOUTH_LANDMARKS['top_lip']]
    #     bottom_lip = face_landmarks.landmark[self.MOUTH_LANDMARKS['bottom_lip']]
    #     left_corner = face_landmarks.landmark[self.MOUTH_LANDMARKS['left_corner']]
    #     right_corner = face_landmarks.landmark[self.MOUTH_LANDMARKS['right_corner']]
        
    #     # Tính toán các giá trị neutral
    #     neutral_mouth_width = abs(left_corner.x * w - right_corner.x * w)
    #     neutral_lip_curve = calculate_point_to_line_distance(bottom_lip, left_corner, right_corner, w, h)
        
    #     # Yêu cầu người dùng mỉm cười để lấy giá trị smiling
    #     print("Hãy mỉm cười và giữ nụ cười trong 3 giây...")
    #     time.sleep(3)
        
    #     smiling_mouth_width = neutral_mouth_width * 1.2  # Giả định miệng rộng hơn 20% khi cười
    #     smiling_lip_curve = neutral_lip_curve * 1.5      # Giả định độ cong môi tăng 50% khi cười
        
    #     # Đặt ngưỡng ở giá trị trung bình
    #     self.mouth_width_thres = (neutral_mouth_width + smiling_mouth_width) / 2
    #     self.lip_curve_thres = (neutral_lip_curve + smiling_lip_curve) / 2
        
    #     print(f"Ngưỡng độ rộng miệng: {self.mouth_width_thres:.2f}")
    #     print(f"Ngưỡng độ cong môi: {self.lip_curve_thres:.2f}")
    #     self.smile_calibrated = True
        
    #     # HIỆU CHUẨN MỞ MIỆNG
    #     print("\n== HIỆU CHUẨN MỞ MIỆNG ==")
        
    #     # Tính khoảng cách giữa môi trên và môi dưới khi miệng đóng
    #     neutral_lip_distance = abs(top_lip.y * h - bottom_lip.y * h)
        
    #     # Yêu cầu người dùng mở miệng
    #     print("Bây giờ hãy mở miệng to và giữ trong 3 giây...")
    #     time.sleep(3)
        
    #     # Giả định rằng người dùng đã mở miệng
    #     # Trong thực tế, ta sẽ lấy frame mới khi người dùng đã mở miệng
    #     open_lip_distance = neutral_lip_distance   # Giả định khoảng cách tăng 3 lần khi mở miệng
        
    #     # Đặt ngưỡng ở giá trị trung bình
    #     self.lip_distance_thres = (neutral_lip_distance + open_lip_distance)
        
    #     print(f"Khoảng cách môi khi đóng: {neutral_lip_distance:.2f}")
    #     print(f"Ngưỡng mở miệng: {self.lip_distance_thres:.2f}")
    #     self.open_mouth_calibrated = True
        
    #     print("\nHiệu chỉnh hoàn tất cho cả nụ cười và mở miệng!")
    #     return True
    

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