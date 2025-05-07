import tkinter as tk
from tkinter import ttk, Scale, messagebox
import cv2
import numpy as np
import threading
import time
import queue
from threading import Thread, Event
from PIL import Image, ImageTk

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
    def __init__(self, root, face_mesh, smile_detector, mouse_controller):
        """Khởi tạo giao diện đơn giản"""
        self.root = root
        self.root.title("No Hands No Problem")
        self.root.geometry("900x600")
        
        # Lưu trữ các đối tượng
        self.face_mesh = face_mesh
        self.smile_detector = smile_detector
        self.mouse_controller = mouse_controller
        
        # Biến trạng thái
        self.tracking_active = False  # Di chuyển chuột
        self.calibrating = False      # Đang hiệu chỉnh
        self.last_click_time = 0
        self.ui_update_rate = 15      # ms, tương đương ~60fps cho UI
        
        # Biến cho việc tương tác với camera
        self.calibration_mesh_results = None
        
        # Tạo layout đơn giản
        self.create_simple_layout()
        
        # Liên kết sự kiện đóng cửa sổ
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Khởi động camera trong thread riêng (luôn bật)
        self.camera_thread = CameraThread(frame_callback=self.on_new_frame)
        
        # Bắt đầu cập nhật UI
        self.update_ui()
        
    def on_new_frame(self, frame):
        """Callback khi có frame mới từ camera."""
        if self.calibrating:
            # Nếu đang calibrate, xử lý frame tìm khuôn mặt
            try:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mesh_results = self.face_mesh.process(frame_rgb)
                if mesh_results and mesh_results.multi_face_landmarks:
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
        
        self.calibrate_btn = ttk.Button(btn_frame, text="1. Calibrate Smile", command=self.calibrate)
        self.calibrate_btn.pack(fill=tk.X, pady=5)
        
        self.tracking_btn = ttk.Button(btn_frame, text="2. Start Mouse Control", command=self.toggle_tracking, state="disabled")
        self.tracking_btn.pack(fill=tk.X, pady=5)
        
        # Hướng dẫn đơn giản
        help_text = "Camera always on.\n1. First calibrate your smile\n2. Then start mouse control\n3. Smile to click"
        ttk.Label(right_frame, text=help_text, wraplength=200).pack(pady=10)
    
    def update_ui(self):
        """Cập nhật giao diện người dùng."""
        # Lấy frame hiện tại từ camera
        frame = self.camera_thread.get_frame()
        
        if frame is not None:
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
                    # chỉ hiển thị trạng thái
                    cv2.putText(display_frame, "Calibrating...", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                    return
                
                # Nếu đang tracking, xử lý di chuyển chuột
                if self.tracking_active:
                    # Trích xuất vị trí và di chuyển chuột
                    current_position = extract_landmark_positions(face_landmarks, w, h)
                    self.mouse_controller.update(current_position)
                    
                    # Phát hiện nụ cười và click
                    curr_time = time.time()
                    if self.smile_detector.detect(face_landmarks, h, w):
                        cv2.putText(display_frame, "Smile Detected!", (10, 60), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        
                        if curr_time - self.last_click_time > 1:
                            self.mouse_controller.click()
                            self.last_click_time = curr_time
                    
                    # Hiển thị trạng thái tracking
                    cv2.putText(display_frame, "Mouse Control Active", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                else:
                    # Nếu đã calibrate nhưng chưa bật tracking
                    state_text = "Ready - Press 'Start Mouse Control'" if self.smile_detector.calibrated else "Please calibrate first"
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
        if not self.smile_detector.calibrated:
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
        self.status_label.config(text="Calibrating Smile...")
        
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
            self.smile_detector.calibrate_with_landmarks(self.calibration_mesh_results)
            return True
        except Exception as e:
            print(f"Lỗi trong quá trình calibrate: {e}")
            return False
    
    def on_close(self):
        """Xử lý khi đóng cửa sổ."""
        self.root.destroy()

# Hàm để khởi động giao diện đơn giản
def launch_simple_gui(face_mesh, smile_detector, mouse_controller):
    root = tk.Tk()
    app = SimpleNoHandsGUI(root, face_mesh, smile_detector, mouse_controller)
    root.mainloop()