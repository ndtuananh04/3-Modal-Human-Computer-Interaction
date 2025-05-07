import tkinter as tk
from tkinter import ttk, Scale, messagebox
import cv2
import numpy as np
import threading
import time
from PIL import Image, ImageTk

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
        self.running = False
        self.camera_active = False
        self.camera_thread = None
        self.last_click_time = 0
        
        # Tạo layout đơn giản
        self.create_simple_layout()
        
        # Liên kết sự kiện đóng cửa sổ
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
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
        
        # Canvas hiển thị video
        self.canvas = tk.Canvas(left_frame, bg="black", width=640, height=480)
        self.canvas.pack(pady=10, padx=10)
        
        # Panel điều khiển đơn giản
        ttk.Label(right_frame, text="No Hands No Problem", font=("Arial", 14, "bold")).pack(pady=10)
        
        # FPS
        # fps_frame = ttk.Frame(status_frame)
        # fps_frame.pack(fill=tk.X, pady=2)
        # ttk.Label(fps_frame, text="FPS:").pack(side=tk.LEFT)
        # self.fps_label = ttk.Label(fps_frame, text="0")
        # self.fps_label.pack(side=tk.RIGHT)
        
        # # Smile detection
        # smile_frame = ttk.Frame(status_frame)
        # smile_frame.pack(fill=tk.X, pady=2)
        # ttk.Label(smile_frame, text="Smile:").pack(side=tk.LEFT)
        # self.smile_label = ttk.Label(smile_frame, text="Not detected")
        # self.smile_label.pack(side=tk.RIGHT)
        
        # Điều chỉnh tốc độ
        ttk.Label(right_frame, text="Mouse Speed:").pack(anchor=tk.W, pady=(10, 0))
        self.speed_var = tk.DoubleVar(value=self.mouse_controller.velocity_scale)
        speed_scale = Scale(right_frame, from_=1, to=40, orient=tk.HORIZONTAL,
                           variable=self.speed_var, command=self.update_speed)
        speed_scale.pack(fill=tk.X)
        
        # Các nút điều khiển
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.calibrate_btn = ttk.Button(btn_frame, text="Calibrate", command=self.calibrate)
        self.calibrate_btn.pack(fill=tk.X, pady=5)
        
        self.start_btn = ttk.Button(btn_frame, text="Start Camera", command=self.toggle_camera)
        self.start_btn.pack(fill=tk.X, pady=5)
        
        # Hướng dẫn đơn giản
        help_text = "Calibrate → Start → Smile to click"
        ttk.Label(right_frame, text=help_text, wraplength=200).pack(pady=10)
    
    def toggle_camera(self):
        """Bật/tắt camera"""
        if self.running:
            self.running = False
            self.start_btn.config(text="Start Camera")
        else:
            self.running = True
            self.start_btn.config(text="Stop Camera")
            
            if self.camera_thread is None or not self.camera_thread.is_alive():
                self.camera_thread = threading.Thread(target=self.process_camera, daemon=True)
                self.camera_thread.start()
    
    def calibrate(self):
        """Hiệu chỉnh nụ cười"""
        if self.running:
            self.toggle_camera()  # Dừng camera trước
        
        self.calibrate_btn.config(state="disabled")
        threading.Thread(target=self.run_calibration, daemon=True).start()
    
    def run_calibration(self):
        """Thực hiện quá trình hiệu chỉnh trong thread riêng"""
        success = self.smile_detector.calibrate(self.face_mesh)
        
        # Bật lại nút sau khi hoàn thành
        self.root.after(0, lambda: self.calibrate_btn.config(state="normal"))
        
        if success:
            messagebox.showinfo("Calibration", "Smile calibration completed!")
        else:
            messagebox.showerror("Error", "Calibration failed. Please try again.")
    
    def update_speed(self, value):
        """Cập nhật tốc độ di chuyển chuột"""
        self.mouse_controller.velocity_scale = float(value)
    
    def process_camera(self):
        """Xử lý camera và hiển thị"""
        from src.face_utils import draw_landmarks, extract_landmark_positions
        
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        last_ui_update = 0
        ui_update_interval = 3
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                break
            
            # FPS
            # curr_time = time.time()
            # fps = 1 / (curr_time - prev_time)
            # prev_time = curr_time
            
            # Cập nhật FPS trên giao diện
            # self.root.after(0, lambda f=fps: self.fps_label.config(text=f"{int(f)}"))
            
            # Xử lý frame
            # frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mesh_results = self.face_mesh.process(frame_rgb)

            curr_time = time.time()
            update_ui = (curr_time - last_ui_update) > ui_update_interval
            
            if mesh_results.multi_face_landmarks:
                for face_landmarks in mesh_results.multi_face_landmarks:
                    h, w, _ = frame.shape
                    
                    # Vẽ landmark
                    # draw_landmarks(frame, face_landmarks)
                    
                    # Trích xuất vị trí và di chuyển chuột
                    current_position = extract_landmark_positions(face_landmarks, w, h)
                    vx, vy = self.mouse_controller.update(current_position)
                    
                    # Phát hiện nụ cười
                    if self.smile_detector.detect(face_landmarks, h, w):
                        if curr_time - self.last_click_time > 1:
                            self.mouse_controller.click()
                            self.last_click_time = curr_time
            
            if update_ui:
                # Lật hình cho preview
                display_frame = cv2.flip(frame, 1)
                
                # Thêm chỉ báo trạng thái
                cv2.putText(display_frame, "Running", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Cập nhật hiển thị đơn giản
                self.update_display_simple(display_frame)
                last_ui_update = curr_time
        
        cap.release()
    
    def update_display_simple(self, frame):
        """Cập nhật hiển thị frame lên canvas"""
        if not self.running:
            return
            
        # Chuyển đổi frame sang định dạng PIL Image
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        
        self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        self.canvas.image = imgtk
    
    def on_close(self):
        """Xử lý khi đóng cửa sổ"""
        self.running = False
        if self.camera_thread and self.camera_thread.is_alive():
            self.camera_thread.join(timeout=1.0)
        
        self.root.destroy()

# Hàm để khởi động giao diện đơn giản
def launch_simple_gui(face_mesh, smile_detector, mouse_controller):
    root = tk.Tk()
    app = SimpleNoHandsGUI(root, face_mesh, smile_detector, mouse_controller)
    root.mainloop()