import tkinter as tk
from tkinter import ttk, Scale, messagebox
import cv2
import numpy as np
import threading
import time
import queue
import os
import pyautogui
from threading import Thread, Event
from PIL import Image, ImageTk
from src.voice_to_text import VoiceToText
from src.face_utils import calculate_point_to_line_distance

class CameraThread:
    """Quản lý camera trong một thread riêng biệt, luôn hoạt động."""
    
    def __init__(self, frame_callback=None):
        """Khởi tạo thread camera.
        
        Args:
            frame_callback: Hàm callback khi có frame mới
        """
        self.lock = threading.Lock()
        self.frame_callback = frame_callback
        self.cap = None
        self.is_running = False
        self.stop_flag = Event()
        self.camera_thread = None
        self.current_frame = None
        self.current_rgb_frame = None
        self.frame_queue = queue.Queue(maxsize=10)  # Hàng đợi lưu trữ các frame gần nhất
        
        # Khởi động camera ngay lập tức
        self.start()
    
    def start(self):
        """Khởi động thread camera."""
        if not self.is_running:
            self.is_running = True
            self.stop_flag.clear()
            self.camera_thread = Thread(target=self.camera_loop, daemon=True)
            self.camera_thread.start()
    
    def camera_loop(self):
        """Vòng lặp chính của camera - luôn chạy."""
        # Mở camera
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
                
                # Thêm frame vào hàng đợi cho quá trình calibration
                try:
                    if not self.frame_queue.full():
                        self.frame_queue.put((frame.copy(), frame_rgb.copy()), block=False)
                    else:
                        # Nếu hàng đợi đầy, loại bỏ frame cũ
                        self.frame_queue.get(block=False)
                        self.frame_queue.put((frame.copy(), frame_rgb.copy()), block=False)
                except:
                    pass  # Bỏ qua nếu không thêm được vào queue
                
                if self.frame_callback:
                    self.frame_callback(frame)
                
            except Exception as e:
                print(f"Lỗi trong camera_loop: {e}")
                time.sleep(0.1)
            
            # Đợi một chút để giảm sử dụng CPU
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
    
    def get_frames_for_calibration(self, count=5):
        """Lấy nhiều frame cho calibration từ queue."""
        frames = []
        rgb_frames = []
        
        # Ưu tiên lấy từ queue trước
        while len(frames) < count and not self.frame_queue.empty():
            try:
                frame, rgb_frame = self.frame_queue.get(block=False)
                frames.append(frame)
                rgb_frames.append(rgb_frame)
            except:
                break
        
        # Nếu không đủ frame, lấy frame hiện tại
        if not frames and self.current_frame is not None:
            with self.lock:
                frames.append(self.current_frame.copy())
                rgb_frames.append(self.current_rgb_frame.copy())
        
        return frames, rgb_frames
    
    def __del__(self):
        """Destructor - giải phóng tài nguyên khi đối tượng bị hủy."""
        self.stop_flag.set()
        if hasattr(self, 'camera_thread') and self.camera_thread and self.camera_thread.is_alive():
            self.camera_thread.join(timeout=1.0)
        
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()


class SimpleNoHandsGUI:
    def __init__(self, root, face_mesh, mouth_detector, mouse_controller):
        """Khởi tạo giao diện đơn giản"""
        self.root = root
        self.root.title("No Hands No Problem")
        self.root.geometry("900x600")
        
        # Lưu trữ các đối tượng
        self.face_mesh = face_mesh
        self.mouth_detector = mouth_detector
        self.mouse_controller = mouse_controller
        
        self.voice_to_text = VoiceToText(model_name="small")

        # Biến trạng thái
        self.tracking_active = False  # Di chuyển chuột
        self.calibrating = False      # Đang hiệu chỉnh
        self.is_recording = False
        self.last_click_time = 0
        self.last_mouth_open_time = 0
        self.ui_update_rate = 15      # ms, tương đương ~60fps cho UI
        self.camera_ready = False 
        self.mouth_open_cooldown = 1.5
        
        # Biến cho việc tương tác với camera
        self.calibration_mesh_results = None

        self.collecting_calibration_data = False
        
        # Tạo layout đơn giản
        self.create_simple_layout()
        
        self.load_and_display_waiting_image()

        # Liên kết sự kiện đóng cửa sổ
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Khởi động camera trong thread riêng (luôn bật)
        self.camera_thread = CameraThread(frame_callback=self.on_new_frame)

        self.voice_to_text = VoiceToText(
            model_name="small", 
            on_status_change=self.update_recording_status
        )
        
        # Thiết lập callback khi nhận dạng xong
        self.voice_to_text.on_transcription_done = self.on_transcription_done
        
        # Bắt đầu cập nhật UI
        self.update_ui()
        
    def load_and_display_waiting_image(self):
        """Tải và hiển thị ảnh chờ từ images/wait.png."""
        wait_image_path = os.path.join("src", "images", "wait.png")
        waiting_img = Image.open(wait_image_path)
        
        # Chuyển đổi sang định dạng Tkinter
        self.waiting_image = ImageTk.PhotoImage(waiting_img)
        
        # Hiển thị lên canvas
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.waiting_image)
        self.canvas.image = self.waiting_image  # Giữ tham chiếu
        
        # Cập nhật status
        self.status_label.config(text="Initializing Camera...")


    def on_new_frame(self, frame):
        """Callback khi có frame mới từ camera."""
        if not self.camera_ready:
            self.camera_ready = True
            self.status_label.config(text="Camera Ready - Please Calibrate")
        if self.calibrating:
            # Nếu đang calibrate, xử lý frame tìm khuôn mặt
            try:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mesh_results = self.face_mesh.process(frame_rgb)
                if not self.calibration_mesh_results or hasattr(self, 'collecting_calibration_data'):
                    self.calibration_mesh_results = mesh_results
            except Exception as e:
                print(f"Lỗi xử lý frame trong calibration: {e}")
    
    def create_simple_layout(self):
        """Tạo layout đơn giản với 2 phần chính"""
        # Frame chính
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame bên trái cho video
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Frame bên phải cho điều khiển
        right_frame = ttk.Frame(main_frame, width=250)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas hiển thị video - kích thước cố định
        self.canvas = tk.Canvas(left_frame, bg="black", width=640, height=480)
        self.canvas.pack(pady=10, padx=10)
        
        # Panel điều khiển đơn giản
        ttk.Label(right_frame, text="No Hands No Problem", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Trạng thái
        status_frame = ttk.LabelFrame(right_frame, text="Status", padding=5)
        status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(status_frame, text="Camera Running")
        self.status_label.pack(fill=tk.X)
        
        # Điều chỉnh tốc độ
        ttk.Label(right_frame, text="Mouse Speed:").pack(anchor=tk.W, pady=(10, 0))
        self.speed_var = tk.DoubleVar(value=self.mouse_controller.velocity_scale)
        speed_scale = Scale(right_frame, from_=1, to=40, orient=tk.HORIZONTAL,
                           variable=self.speed_var, command=self.update_speed)
        speed_scale.pack(fill=tk.X)
        
        # Các nút điều khiển
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.calibrate_btn = ttk.Button(btn_frame, text="1. Calibrate Mouth", command=self.calibrate)
        self.calibrate_btn.pack(fill=tk.X, pady=5)
        
        self.tracking_btn = ttk.Button(btn_frame, text="2. Start Mouse Control", command=self.toggle_tracking, state="disabled")
        self.tracking_btn.pack(fill=tk.X, pady=5)
        
        status_frame = ttk.LabelFrame(right_frame, text="Status", padding=5)
        status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(status_frame, text="Camera Running")
        self.status_label.pack(fill=tk.X)
        
        # Thêm label hiển thị trạng thái ghi âm
        self.recording_label = ttk.Label(status_frame, text="Not Recording")
        self.recording_label.pack(fill=tk.X)

        transcript_frame = ttk.LabelFrame(right_frame, text="Speech Recognition", padding=5)
        transcript_frame.pack(fill=tk.X, pady=10)

        # Tạo Text widget để hiển thị kết quả nhận dạng giọng nói
        self.transcript_text = tk.Text(transcript_frame, height=4, width=20, wrap=tk.WORD)
        self.transcript_text.pack(fill=tk.X, expand=True, pady=5)

        # Thanh cuộn cho transcript_text
        transcript_scrollbar = ttk.Scrollbar(transcript_frame, orient="vertical", command=self.transcript_text.yview)
        transcript_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.transcript_text.config(yscrollcommand=transcript_scrollbar.set)
    
    def update_ui(self):
        """Cập nhật giao diện người dùng."""
        # Lấy frame hiện tại từ camera
        frame = self.camera_thread.get_frame()
        
        if frame is not None:
            self.camera_ready = True
            display_frame = frame.copy()
            
            # Xử lý khuôn mặt và mỉm cười
            self.process_face(display_frame)
            
            # Chuyển đổi frame để hiển thị trên canvas
            frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            
            # Cập nhật canvas
            self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
            self.canvas.image = imgtk  # Giữ tham chiếu
        
        # Lập lịch cập nhật tiếp theo
        self.root.after(self.ui_update_rate, self.update_ui)
    
    def process_face(self, display_frame):
        """Xử lý nhận diện khuôn mặt, cập nhật frame hiển thị và điều khiển chuột nếu được bật."""
        from src.face_utils import draw_landmarks, extract_landmark_positions
        
        # Lấy RGB frame cho mediapipe
        frame_rgb = self.camera_thread.get_rgb_frame()
        if frame_rgb is None:
            return
        
        # Xử lý tìm khuôn mặt
        mesh_results = self.face_mesh.process(frame_rgb)
        
        if mesh_results and mesh_results.multi_face_landmarks:
            for face_landmarks in mesh_results.multi_face_landmarks:
                h, w, _ = display_frame.shape
                
                # Vẽ landmark trên khuôn mặt
                draw_landmarks(display_frame, face_landmarks)
                
                # Nếu đang calibrating, xử lý dữ liệu khuôn mặt cho calibration
                if self.calibrating:
                    # Việc calibrate được xử lý ở phương thức khác, 
                    if hasattr(self, 'collecting_calibration_data') and self.collecting_calibration_data:
                        self.calibration_mesh_results = mesh_results
                    # chỉ hiển thị trạng thái
                    cv2.putText(display_frame, "Calibrating...", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                    return
                
                self.handle_mouth_open_for_recording(face_landmarks, h, w, display_frame)
                # Nếu đang tracking, xử lý di chuyển chuột
                if self.tracking_active:
                    # Trích xuất vị trí và di chuyển chuột
                    current_position = extract_landmark_positions(face_landmarks, w, h)
                    self.mouse_controller.update(current_position)
                    
                    # Phát hiện nụ cười và click
                    curr_time = time.time()
                    if self.mouth_detector.detect_smile(face_landmarks, h, w):
                        cv2.putText(display_frame, "Smile Detected!", (10, 60), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        
                        if curr_time - self.last_click_time > 1:
                            self.mouse_controller.click()
                            self.last_click_time = curr_time
                    
                    # if self.mouth_detector.detect_open_mouth(face_landmarks, h, w):
                    #     cv2.putText(display_frame, "Open Mouth Detected!", (10, 90), 
                    #                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # Hiển thị trạng thái tracking
                    cv2.putText(display_frame, "Mouse Control Active", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                else:
                    # Nếu đã calibrate nhưng chưa bật tracking
                    state_text = "Ready - Press 'Start Mouse Control'" if self.mouth_detector.calibrated else "Please calibrate first"
                    cv2.putText(display_frame, state_text, (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        else:
            # Không tìm thấy khuôn mặt
            if self.calibrating:
                cv2.putText(display_frame, "No face detected - Keep face centered", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            elif self.tracking_active:
                cv2.putText(display_frame, "No face detected", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            else:
                cv2.putText(display_frame, "No face detected", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    def toggle_tracking(self):
        """Bật/tắt tính năng theo dõi khuôn mặt và điều khiển chuột."""
        if not self.mouth_detector.calibrated:
            messagebox.showerror("Error", "Please calibrate smile detection first.")
            return
            
        self.tracking_active = not self.tracking_active
        
        if self.tracking_active:
            self.tracking_btn.config(text="Stop Mouse Control")
            self.status_label.config(text="Mouse Control Active")
        else:
            self.tracking_btn.config(text="Start Mouse Control")
            self.status_label.config(text="Ready - Camera Running")
    
    def update_speed(self, value):
        """Cập nhật tốc độ di chuyển chuột."""
        self.mouse_controller.velocity_scale = float(value)
    
    def calibrate(self):
        """Hiệu chỉnh nụ cười sử dụng frame hiện hành."""
        # Tạm dừng tracking nếu đang hoạt động
        was_tracking = self.tracking_active
        self.tracking_active = False
        
        self.calibrating = True
        self.calibration_mesh_results = None
        self.calibrate_btn.config(state="disabled")
        self.tracking_btn.config(state="disabled")
        self.status_label.config(text="Calibrating...")
        
        # Thực hiện hiệu chỉnh trong thread riêng, sử dụng frame từ camera thread
        threading.Thread(target=lambda: self.run_calibration(was_tracking), daemon=True).start()
    
    def run_calibration(self, restore_tracking):
        """Thực hiện quá trình hiệu chỉnh trong thread riêng."""
        # Sử dụng phương thức calibrate_with_frames được tùy chỉnh thay vì gọi trực tiếp
        success = self.calibrate_with_frames()
        
        # Đánh dấu rằng việc calibration đã hoàn thành
        self.calibrating = False
        
        # Khôi phục UI sau khi hiệu chỉnh
        self.root.after(0, lambda: self.calibrate_btn.config(state="normal"))
        
        if success:
            self.root.after(0, lambda: self.status_label.config(text="Calibration Successful"))
            self.root.after(0, lambda: self.tracking_btn.config(state="normal"))
            messagebox.showinfo("Calibration", "Smile calibration completed successfully!")
        else:
            self.root.after(0, lambda: self.status_label.config(text="Calibration Failed"))
            messagebox.showerror("Error", "Calibration failed. Please try again.")
        
        # Khôi phục trạng thái tracking nếu đã bật trước đó
        if restore_tracking and success:
            self.root.after(100, self.toggle_tracking)
    
    def calibrate_with_frames(self):
        """Phương pháp calibrate sử dụng các frame đã có từ camera thread."""
        # Đợi đến khi có kết quả detection
        print("Calibrating")
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
        
        # Sử dụng kết quả detection có sẵn
        try:
                    # 1. Thu thập dữ liệu neutral
            h, w = 480, 640
            
            # PHẦN 1: CALIBRATE NỤ CƯỜI
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
            self.root.after(0, lambda: self.status_label.config(text="Please smile naturally..."))
            
            # Khởi tạo các biến thu thập dữ liệu nụ cười
            smile_start = time.time()
            smile_duration = 3.0  # 3 giây
            smile_widths = [neutral_mouth_width]  # Bao gồm giá trị neutral
            smile_curves = [neutral_lip_curve]    # Bao gồm giá trị neutral
            
            # Reset biến kết quả để nhận landmarks mới
            self.calibration_mesh_results = None
            
            # Bật cờ thu thập dữ liệu
            self.collecting_calibration_data = True
            
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
                self.root.after(0, lambda t=seconds_left: 
                    self.status_label.config(text=f"Keep smiling ({t}s left)"))
                
                # Đợi một chút giữa các lần lấy mẫu
                time.sleep(0.1)
            
            # 1.4. Phân tích dữ liệu nụ cười
            if len(smile_widths) < 3 or len(smile_curves) < 3:
                print("Thu thập dữ liệu nụ cười không đủ!")
                self.collecting_calibration_data = False
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
            self.root.after(0, lambda: self.status_label.config(text="Smile calibration complete! Now preparing for mouth open..."))
            time.sleep(1)  # Đợi một chút trước khi chuyển sang bước tiếp theo
            
            # PHẦN 2: CALIBRATE MỞ MIỆNG (giữ nguyên phần cũ)
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
                self.collecting_calibration_data = False
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
            self.root.after(0, lambda: self.status_label.config(text="Keep mouth closed..."))
            time.sleep(1)
            
            # 2.3. Chuẩn bị thu thập dữ liệu mở miệng
            self.root.after(0, lambda: self.status_label.config(text="Now open your mouth wide..."))
            
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
                self.root.after(0, lambda t=seconds_left: 
                    self.status_label.config(text=f"Keep mouth open ({t}s left)"))
                
                # Đợi một chút giữa các lần lấy mẫu
                time.sleep(0.1)
            
            # Kết thúc thu thập dữ liệu
            self.collecting_calibration_data = False
            
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
            self.root.after(0, lambda: self.status_label.config(text="Calibration complete!"))
            
            return True
        except Exception as e:
            print(f"Lỗi trong quá trình calibrate: {e}")
            return False
    
    def handle_mouth_open_for_recording(self, face_landmarks, height, width, display_frame):
        """Xử lý cử chỉ mở miệng để bắt đầu/dừng ghi âm"""
        curr_time = time.time()
        
        # Phát hiện miệng mở
        mouth_open = self.mouth_detector.detect_open_mouth(face_landmarks, height, width)
        
        # Hiển thị trạng thái mở miệng
        if mouth_open:
            cv2.putText(display_frame, "Open Mouth Detected!", (10, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Chỉ xử lý nếu đã qua thời gian cooldown
            if curr_time - self.last_mouth_open_time > self.mouth_open_cooldown:
                if not self.voice_to_text.is_recording:
                    # Nếu chưa ghi âm -> bắt đầu ghi
                    self.voice_to_text.start_recording()
                else:
                    # Nếu đang ghi âm -> dừng ghi và xử lý
                    self.voice_to_text.stop_recording()
                
                self.last_mouth_open_time = curr_time

    def update_recording_status(self, status):
        """Cập nhật trạng thái ghi âm trên UI."""
        if hasattr(self, 'recording_label'):
            self.recording_label.config(text=status)

    def on_transcription_done(self, text):
        """Xử lý khi nhận dạng giọng nói hoàn tất."""
        # Hiển thị kết quả và gõ văn bản
        self.voice_to_text.transcribe_and_type(text, self.transcript_text)

    def on_close(self):
        """Xử lý khi đóng cửa sổ."""
        if self.voice_to_text.is_recording:
            self.voice_to_text.stop_recording(process_audio=False)
        self.root.destroy()
        

    def on_close(self):
        """Xử lý khi đóng cửa sổ."""
        if self.is_recording:
            self.voice_to_text.stop_recording(process_audio=False)
        self.root.destroy()

    

# Hàm để khởi động giao diện đơn giản
def launch_simple_gui(face_mesh, mouth_detector, mouse_controller):
    root = tk.Tk()
    app = SimpleNoHandsGUI(root, face_mesh, mouth_detector, mouse_controller)
    root.mainloop()