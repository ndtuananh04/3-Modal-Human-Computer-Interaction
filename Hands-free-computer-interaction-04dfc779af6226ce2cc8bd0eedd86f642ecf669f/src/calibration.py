import time
import threading
import cv2
from src.face_utils import calculate_point_to_line_distance

class CalibrationManager:
    """Quản lý quá trình hiệu chuẩn nụ cười và mở miệng."""
    
    def __init__(self, face_mesh, mouth_detector):
        self.face_mesh = face_mesh
        self.mouth_detector = mouth_detector
        self.calibrating = False
        self.calibration_mesh_results = None
        self.collecting_data = False
        
    def start_calibration(self, update_status_callback, on_complete_callback):
        self.calibrating = True
        self.calibration_mesh_results = None
        self.update_status = update_status_callback
        
        # Hiệu chuẩn trong thread riêng
        threading.Thread(
            target=lambda: self.run_calibration(on_complete_callback),
            daemon=True
        ).start()
    
    def process_new_frame(self, frame_rgb):
        """Xử lý frame mới cho hiệu chuẩn."""
        if not self.calibrating:
            return
            
        try:
            mesh_results = self.face_mesh.process(frame_rgb)
            
            if mesh_results and mesh_results.multi_face_landmarks:
                if not self.calibration_mesh_results or self.collecting_data:
                    self.calibration_mesh_results = mesh_results
        except Exception as e:
            print(f"Lỗi xử lý frame trong calibration: {e}")
    
    def run_calibration(self, on_complete_callback):
        """Thực hiện hiệu chuẩn trong thread riêng."""
        success = self.calibrate_with_frames()
        self.calibrating = False
        
        on_complete_callback(success)
    
    def calibrate_with_frames(self):
        """Phương pháp calibrate sử dụng các frame."""
        # Đợi đến khi có kết quả detection
        print("Waiting for face...")
        
        max_wait_time = 10  # Đợi tối đa 10 giây
        start_wait = time.time()
        
        # Lặp đến khi có kết quả hoặc hết thời gian chờ
        while not self.calibration_mesh_results and time.time() - start_wait < max_wait_time:
            time.sleep(0.1)
        
        if not self.calibration_mesh_results:
            print("Không tìm thấy khuôn mặt sau thời gian chờ.")
            return False
        
        print("Face detected! Starting calibration...")
        
        try:
            h, w = 480, 640
            
            # PHẦN 1: CALIBRATE NỤ CƯỜI
            if not self._calibrate_smile(h, w):
                return False
                
            # PHẦN 2: CALIBRATE MỞ MIỆNG
            if not self._calibrate_open_mouth(h, w):
                return False
            
            return True
        except Exception as e:
            print(f"Lỗi trong quá trình calibrate: {e}")
            import traceback
            traceback.print_exc()
            self.collecting_data = False
            return False
    
    def _calibrate_smile(self, h, w):
        """Phần 1: Hiệu chuẩn nụ cười."""
        print("\n== CALIBRATE NỤ CƯỜI ==")
        
        # 1.1. Thu thập dữ liệu khuôn mặt bình thường (không cười)
        face_landmarks = self.calibration_mesh_results.multi_face_landmarks[0]
        
        # Lấy các landmark của miệng
        left_corner = face_landmarks.landmark[self.mouth_detector.MOUTH_LANDMARKS['left_corner']]
        right_corner = face_landmarks.landmark[self.mouth_detector.MOUTH_LANDMARKS['right_corner']]
        bottom_lip = face_landmarks.landmark[self.mouth_detector.MOUTH_LANDMARKS['bottom_lip']]
        
        # Tính giá trị ban đầu (không cười)
        neutral_mouth_width = abs(left_corner.x * w - right_corner.x * w)
        neutral_lip_curve = calculate_point_to_line_distance(bottom_lip, left_corner, right_corner, w, h)
        
        print(f"Độ rộng miệng khi không cười: {neutral_mouth_width:.2f}")
        print(f"Độ cong môi khi không cười: {neutral_lip_curve:.2f}")
        
        # 1.2. Thông báo người dùng mỉm cười
        self.update_status("Please smile naturally...")
        
        # Khởi tạo các biến thu thập dữ liệu nụ cười
        smile_start = time.time()
        smile_duration = 3.0  # 3 giây
        smile_widths = [neutral_mouth_width]  # Bao gồm giá trị neutral
        smile_curves = [neutral_lip_curve]    # Bao gồm giá trị neutral
        
        # Reset biến kết quả để nhận landmarks mới
        self.calibration_mesh_results = None
        
        # Bật cờ thu thập dữ liệu
        self.collecting_data = True
        
        # 1.3. Thu thập dữ liệu nụ cười trong 3 giây
        print("Collecting smile data for 3 seconds...")
        while time.time() - smile_start < smile_duration:
            # Kiểm tra có mesh results mới không
            if self.calibration_mesh_results and self.calibration_mesh_results.multi_face_landmarks:
                smile_landmarks = self.calibration_mesh_results.multi_face_landmarks[0]
                
                # Lấy các landmark
                left_corner = smile_landmarks.landmark[self.mouth_detector.MOUTH_LANDMARKS['left_corner']]
                right_corner = smile_landmarks.landmark[self.mouth_detector.MOUTH_LANDMARKS['right_corner']]
                bottom_lip = smile_landmarks.landmark[self.mouth_detector.MOUTH_LANDMARKS['bottom_lip']]
                
                # Tính toán giá trị
                width = abs(left_corner.x * w - right_corner.x * w)
                curve = calculate_point_to_line_distance(bottom_lip, left_corner, right_corner, w, h)
                
                # Lưu lại
                smile_widths.append(width)
                smile_curves.append(curve)
                
                # In thông tin debug
                print(f"Current smile width: {width:.2f}, curve: {curve:.2f}")
                
                # Reset để lấy mẫu tiếp theo
                self.calibration_mesh_results = None
            
            # Cập nhật thời gian còn lại
            seconds_left = int(smile_duration - (time.time() - smile_start)) + 1
            self.update_status(f"Keep smiling ({seconds_left}s left)")
            
            # Đợi một chút giữa các lần lấy mẫu
            time.sleep(0.1)
        
        # 1.4. Phân tích dữ liệu nụ cười
        if len(smile_widths) < 3 or len(smile_curves) < 3:
            print("Thu thập dữ liệu nụ cười không đủ!")
            self.collecting_data = False
            return False
            
        # Tìm giá trị tối đa cho nụ cười
        max_width = max(smile_widths)
        max_curve = max(smile_curves)
        
        print(f"Smile calibration complete. Samples collected: {len(smile_widths)}")
        print(f"Maximum mouth width: {max_width:.2f}")
        print(f"Maximum lip curve: {max_curve:.2f}")
        
        # Tính ngưỡng ở giữa neutral và max
        self.mouth_detector.mouth_width_thres = (neutral_mouth_width + max_width) / 2
        self.mouth_detector.lip_curve_thres = (neutral_lip_curve + max_curve) / 2
        
        print(f"Width threshold: {self.mouth_detector.mouth_width_thres:.2f}")
        print(f"Curve threshold: {self.mouth_detector.lip_curve_thres:.2f}")
        
        # Đánh dấu đã hiệu chuẩn nụ cười
        self.mouth_detector.smile_calibrated = True
        
        # Thông báo hoàn tất bước 1
        self.update_status("Smile calibration complete! Now preparing for mouth open...")
        time.sleep(1)  # Đợi một chút trước khi chuyển sang bước tiếp theo
        
        return True
    
    def _calibrate_open_mouth(self, h, w):
        """Phần 2: Hiệu chuẩn mở miệng."""
        print("\n== CALIBRATE MỞ MIỆNG ==")
        
        # 2.1. Thu thập dữ liệu neutral cho miệng
        # Reset để lấy kết quả mới
        self.calibration_mesh_results = None
        
        # Đợi để lấy frame mới
        max_wait_time = 3  # Đợi tối đa 3 giây cho frame mới
        start_wait = time.time()
        while not self.calibration_mesh_results and time.time() - start_wait < max_wait_time:
            time.sleep(0.1)
        
        if not self.calibration_mesh_results:
            print("Không lấy được frame mới cho calibrate mở miệng.")
            self.collecting_data = False
            return False
        
        # Lấy frame mới cho miệng đóng
        face_landmarks = self.calibration_mesh_results.multi_face_landmarks[0]
        
        # Lấy điểm landmark môi
        top_lip = face_landmarks.landmark[self.mouth_detector.MOUTH_LANDMARKS['top_lip']]
        bottom_lip = face_landmarks.landmark[self.mouth_detector.MOUTH_LANDMARKS['bottom_lip']]
        
        # Tính khoảng cách neutral
        neutral_distance = abs(top_lip.y * h - bottom_lip.y * h)
        print(f"Neutral lip distance: {neutral_distance:.2f}")
        
        # 2.2. Cập nhật UI với hướng dẫn
        self.update_status("Keep mouth closed...")
        time.sleep(1)
        
        # 2.3. Chuẩn bị thu thập dữ liệu mở miệng
        self.update_status("Now open your mouth wide...")
        
        # Khởi tạo các biến thu thập dữ liệu
        start_collection = time.time()
        collection_duration = 3.0  # 3 giây
        lip_distances = [neutral_distance]  # Đã bao gồm giá trị neutral ban đầu
        
        # Reset biến kết quả để nhận landmarks mới
        self.calibration_mesh_results = None
        
        # 2.4. Thu thập dữ liệu liên tục từ on_new_frame
        print("Collecting mouth open data for 3 seconds...")
        while time.time() - start_collection < collection_duration:
            # Kiểm tra có mesh results mới không
            if self.calibration_mesh_results and self.calibration_mesh_results.multi_face_landmarks:
                face_landmarks = self.calibration_mesh_results.multi_face_landmarks[0]
                
                # Lấy các landmark
                top_lip = face_landmarks.landmark[self.mouth_detector.MOUTH_LANDMARKS['top_lip']]
                bottom_lip = face_landmarks.landmark[self.mouth_detector.MOUTH_LANDMARKS['bottom_lip']]
                
                # Tính khoảng cách và lưu lại
                lip_distance = abs(top_lip.y * h - bottom_lip.y * h)
                lip_distances.append(lip_distance)
                
                # In thông tin debug
                print(f"Current lip distance: {lip_distance:.2f}")
                
                # Reset để lấy mẫu tiếp theo
                self.calibration_mesh_results = None
            
            # Cập nhật thời gian còn lại
            seconds_left = int(collection_duration - (time.time() - start_collection)) + 1
            self.update_status(f"Keep mouth open ({seconds_left}s left)")
            
            # Đợi một chút giữa các lần lấy mẫu
            time.sleep(0.1)
        
        # Kết thúc thu thập dữ liệu
        self.collecting_data = False
        
        # 2.5. Phân tích dữ liệu thu thập được
        if len(lip_distances) < 3:
            print("Thu thập dữ liệu mở miệng không đủ!")
            return False
            
        # Tìm khoảng cách lớn nhất và nhỏ nhất
        min_distance = min(lip_distances)
        max_distance = max(lip_distances)
        
        print(f"Collection complete. Samples collected: {len(lip_distances)}")
        print(f"Minimum lip distance: {min_distance:.2f}")
        print(f"Maximum lip distance: {max_distance:.2f}")
        
        # 2.6. Thiết lập các thông số cho mouth_detector
        self.mouth_detector.lip_distance_neutral = min_distance
        self.mouth_detector.lip_distance_max = max_distance
        
        # Tính ngưỡng ở mức 80% khoảng cách từ neutral đến max
        range_distance = max_distance - min_distance
        threshold = min_distance + range_distance * 0.8
        self.mouth_detector.lip_distance_thres = threshold
        
        print(f"Setting threshold at 80% range: {threshold:.2f}")
        
        # 2.7. Đánh dấu quá trình hiệu chuẩn hoàn tất
        self.mouth_detector.open_mouth_calibrated = True
        
        # 2.8. Hiển thị thông báo hoàn tất
        self.update_status("Calibration complete!")
        
        return True