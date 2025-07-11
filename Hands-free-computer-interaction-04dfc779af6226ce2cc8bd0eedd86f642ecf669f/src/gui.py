import tkinter as tk
from tkinter import ttk, Scale, messagebox
import cv2
import threading
import time
import os
from PIL import Image, ImageTk
from src.face_utils import calculate_point_to_line_distance

from src.voice_to_text import VoiceToText
from src.camera_thread import CameraThread
from src.face_processor import FaceProcessor
from src.speech_handler import SpeechHandler
from src.calibration import CalibrationManager

class HandsFreeGUI:
    def __init__(self, root, face_mesh, mouth_detector, mouse_controller):
        """Khởi tạo giao diện đơn giản"""
        self.root = root
        self.root.title("Hands-free Computer Interaction")
        self.root.geometry("900x700")

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
        
        self.init_modules(face_mesh, mouth_detector, mouse_controller)
        # Tạo layout đơn giản
        self.create_simple_layout()
        
        self.load_and_display_waiting_image()

        # Liên kết sự kiện đóng cửa sổ
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Thiết lập callback khi nhận dạng xong
        self.voice_to_text.on_transcription_done = self.on_transcription_done
        
        # Bắt đầu cập nhật UI
        self.update_ui()

    def init_modules(self, face_mesh, mouth_detector, mouse_controller):
        self.camera_thread = CameraThread(frame_callback=self.on_new_frame)

        self.voice_to_text = VoiceToText(
            model_name="small", 
            on_status_change=self.update_recording_status
        )

        self.speech_handler = SpeechHandler(self.voice_to_text)
        self.speech_handler.set_status_callback(self.update_recording_status)
        self.speech_handler.set_transcription_callback(self.on_transcription_done)

        self.face_processor = FaceProcessor(face_mesh, mouth_detector, mouse_controller)

        self.calibration_manager = CalibrationManager(face_mesh, mouth_detector)
        self.face_mesh = face_mesh
        self.mouth_detector = mouth_detector
        self.mouse_controller = mouse_controller
        
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
        self.camera_ready = True

        # if self.calibrating:
        #     # Nếu đang calibrate, xử lý frame tìm khuôn mặt
        #     try:
        #         frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        #         mesh_results = self.face_mesh.process(frame_rgb)
        #         if not self.calibration_mesh_results or hasattr(self, 'collecting_calibration_data'):
        #             self.calibration_mesh_results = mesh_results
        #     except Exception as e:
        #         print(f"Lỗi xử lý frame trong calibration: {e}")
        if self.calibration_manager.calibrating:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.calibration_manager.process_new_frame(frame_rgb)
    
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

        ttk.Label(right_frame, text="Mincutoff:").pack(anchor=tk.W, pady=(10, 0))
        self.mincutoff = tk.DoubleVar(value=self.mouse_controller.mincutoff)
        mincutoff = Scale(right_frame, from_=0.5, to=5, resolution=0.1, orient=tk.HORIZONTAL,
                           variable=self.mincutoff, command=self.update_mincutoff)
        mincutoff.pack(fill=tk.X)

        ttk.Label(right_frame, text="Beta:").pack(anchor=tk.W, pady=(10, 0))
        self.beta = tk.DoubleVar(value=self.mouse_controller.beta)
        beta = Scale(right_frame, from_=0.001, to=0.5, resolution=0.001, orient=tk.HORIZONTAL,
                           variable=self.beta, command=self.update_beta)
        beta.pack(fill=tk.X)
        
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
            # Lấy RGB frame cho xử lý
            frame_rgb = self.camera_thread.get_rgb_frame()
            
            # Xử lý khuôn mặt và hiển thị
            display_frame, face_data = self.face_processor.process_face(
                frame, 
                frame_rgb,
                tracking_active=self.tracking_active,
                calibrating=self.calibration_manager.calibrating
            )
            
            # Xử lý mở miệng để bắt đầu/dừng ghi âm nếu phát hiện khuôn mặt
            if face_data["detected"] and not self.calibration_manager.calibrating:
                self.speech_handler.handle_mouth_open(face_data["mouth_open"])
            
            # Chuyển đổi frame để hiển thị trên canvas
            self.update_canvas_image(display_frame)
        
        # Lập lịch cập nhật tiếp theo
        self.root.after(self.ui_update_rate, self.update_ui)
    
    def update_canvas_image(self, display_frame):
        """Cập nhật hình ảnh trên canvas."""
        frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        
        # Cập nhật canvas
        self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        self.canvas.image = imgtk
    
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

    def update_mincutoff(self, value):
        self.mouse_controller.mincutoff = float(value)
        self.mouse_controller.reset()
    
    def update_beta(self, value):
        self.mouse_controller.beta = float(value)
        self.mouse_controller.reset()
    
    def calibrate(self):
        """Bắt đầu quá trình hiệu chuẩn."""
        # Tạm dừng tracking nếu đang hoạt động
        was_tracking = self.tracking_active
        self.tracking_active = False
        
        # Vô hiệu hóa các nút
        self.calibrate_btn.config(state="disabled")
        self.tracking_btn.config(state="disabled")
        
        # Bắt đầu hiệu chuẩn
        def update_status(text):
            self.root.after(0, lambda: self.status_label.config(text=text))
            
        def on_calibration_complete(success):
            self.root.after(0, lambda: self.handle_calibration_result(success, was_tracking))
            
        self.calibration_manager.start_calibration(
            update_status_callback=update_status,
            on_complete_callback=on_calibration_complete
        )
    
    def handle_calibration_result(self, success, was_tracking):
        """Xử lý kết quả sau khi hiệu chuẩn hoàn tất."""
        # Khôi phục nút calibrate
        self.calibrate_btn.config(state="normal")
        
        if success:
            self.status_label.config(text="Calibration Successful")
            self.tracking_btn.config(state="normal")
            messagebox.showinfo("Calibration", "Mouth calibration completed successfully!")
            
            # Khôi phục trạng thái tracking
            if was_tracking:
                self.root.after(100, self.toggle_tracking)
        else:
            self.status_label.config(text="Calibration Failed")
            messagebox.showerror("Error", "Calibration failed. Please try again.")

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
        self.speech_handler.cleanup()
        self.root.destroy()
        
    