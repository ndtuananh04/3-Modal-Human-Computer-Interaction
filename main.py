import argparse
import sys
import time
import cv2

from src.face_utils import init_face_mesh, extract_landmark_positions, draw_landmarks
from src.smile_detector import SmileDetector
from src.mouse_controller import MouseController

def main():
    """Hàm main chính của ứng dụng."""
    parser = argparse.ArgumentParser(description='Hands-free control application')
    parser.add_argument('--nogui', action='store_true')
    args = parser.parse_args()
    
    # Khởi tạo các thành phần
    face_mesh = init_face_mesh()
    smile_detector = SmileDetector()
    mouse_controller = MouseController()
    
    if args.nogui:
        # Chạy phiên bản dòng lệnh
        run_cli_version(face_mesh, smile_detector, mouse_controller)
    else:
        # Chạy phiên bản có GUI
        try:
            from src.simple_gui import launch_simple_gui
            launch_simple_gui(face_mesh, smile_detector, mouse_controller)
        except ImportError as e:
            print(f"Lỗi khi tải giao diện đồ họa: {e}")
            print("Chuyển sang chế độ dòng lệnh...")
            run_cli_version(face_mesh, smile_detector, mouse_controller)

def run_cli_version(face_mesh, smile_detector, mouse_controller):
    """Chạy phiên bản dòng lệnh của ứng dụng."""
    
    # Thực hiện hiệu chỉnh smile detector
    if not smile_detector.calibrate(face_mesh):
        print("Hiệu chỉnh thất bại. Kết thúc chương trình...")
        return
    
    # Mở webcam
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    prev_time = 0
    last_click_time = 0
    
    print("Bắt đầu theo dõi khuôn mặt. Nhấn 'q' để thoát.")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Xử lý Face Mesh
        mesh_results = face_mesh.process(frame_rgb)
        
        # Tính FPS
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time)
        prev_time = curr_time
        
        if mesh_results.multi_face_landmarks:
            for face_landmarks in mesh_results.multi_face_landmarks:
                h, w, _ = frame.shape
                
                # Vẽ landmark
                draw_landmarks(frame, face_landmarks)
                
                # Trích xuất vị trí và di chuyển chuột
                current_position = extract_landmark_positions(face_landmarks, w, h)
                vx, vy = mouse_controller.update(current_position)
                
                # Phát hiện nụ cười và click
                if smile_detector.detect(face_landmarks, h, w):
                    cv2.putText(frame, "Smile Detected!", (10, 60), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    
                    if curr_time - last_click_time > 1:
                        mouse_controller.click()
                        last_click_time = curr_time
        
        # Hiển thị FPS
        cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Hiển thị frame
        cv2.imshow("No Hands No Problem", frame)
        
        # Thoát nếu nhấn 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Giải phóng tài nguyên
    cap.release()
    cv2.destroyAllWindows()
    face_mesh.close()

if __name__ == "__main__":
    main()