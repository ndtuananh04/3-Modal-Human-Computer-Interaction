import cv2
import threading
import time
from threading import Thread, Event

class CameraThread:
    """Quản lý camera trong một thread riêng biệt, luôn hoạt động."""
    
    def __init__(self, frame_callback=None):
        self.lock = threading.Lock()
        self.frame_callback = frame_callback
        self.cap = None
        self.is_running = False
        self.stop_flag = Event()
        self.camera_thread = None
        self.current_frame = None
        self.current_rgb_frame = None
        
        # Khởi động camera ngay lập tức
        self.start()
    
    def start(self):
        if not self.is_running:
            self.is_running = True
            self.stop_flag.clear()
            self.camera_thread = Thread(target=self.camera_loop, daemon=True)
            self.camera_thread.start()
    
    def camera_loop(self):
        try:
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            if not self.cap.isOpened():
                print("Không thể mở camera!")
                self.is_running = False
                return
        except Exception as e:
            print(f"Lỗi khởi tạo camera: {e}")
            self.is_running = False
            return
        
        failure_count = 0  # Đếm số lần đọc frame thất bại liên tiếp
        
        while not self.stop_flag.is_set():
            try:
                ret, frame = self.cap.read()
                if not ret:
                    failure_count += 1
                    print(f"Lỗi đọc frame từ camera (lần {failure_count})")
                    
                    # Nếu lỗi quá 5 lần liên tiếp, thử khởi động lại camera
                    if failure_count > 5:
                        print("Thử khởi động lại camera...")
                        self.cap.release()
                        time.sleep(1)
                        self.cap = cv2.VideoCapture(0)
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        failure_count = 0
                    
                    time.sleep(0.1)
                    continue
                
                # Reset failure count
                failure_count = 0
                
                # Lật hình để dễ nhìn
                frame = cv2.flip(frame, 1)
                
                # Tạo phiên bản RGB để sử dụng với mediapipe
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Lưu frame hiện tại và thông báo qua callback
                with self.lock:
                    self.current_frame = frame.copy()
                    self.current_rgb_frame = frame_rgb.copy()
                
                if self.frame_callback:
                    self.frame_callback(frame)
                
            except Exception as e:
                print(f"Lỗi trong camera_loop: {e}")
                time.sleep(0.1)
            
            try:
                cv2.waitKey(1)
            except:
                pass
    
    def get_frame(self):
        """Lấy frame hiện tại từ camera."""
        with self.lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
            return None
    
    def get_rgb_frame(self):
        """Lấy frame RGB hiện tại từ camera (để dùng với mediapipe)."""
        with self.lock:
            if self.current_rgb_frame is not None:
                return self.current_rgb_frame.copy()
            return None
    
    def __del__(self):
        """Destructor - giải phóng tài nguyên khi đối tượng bị hủy."""
        self.stop_flag.set()
        if hasattr(self, 'camera_thread') and self.camera_thread and self.camera_thread.is_alive():
            self.camera_thread.join(timeout=1.0)
        
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()