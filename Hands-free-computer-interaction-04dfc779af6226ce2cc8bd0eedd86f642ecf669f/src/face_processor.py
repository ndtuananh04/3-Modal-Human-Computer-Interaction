import cv2
import time
from src.face_utils import draw_landmarks, extract_landmark_positions

class FaceProcessor:
    def __init__(self, face_mesh, mouth_detector, mouse_controller):
        self.face_mesh = face_mesh
        self.mouth_detector = mouth_detector
        self.mouse_controller = mouse_controller
        self.last_click_time = 0
    
    def process_face(self, frame, frame_rgb, tracking_active=False, calibrating=False):
       
        display_frame = frame.copy()
        face_data = {
            "detected": False,
            "landmarks": None,
            "smile_detected": False,
            "mouth_open": False,
            "dimensions": {"height": frame.shape[0], "width": frame.shape[1]},
        }
        
        # Xử lý tìm khuôn mặt
        mesh_results = self.face_mesh.process(frame_rgb)
        
        if mesh_results and mesh_results.multi_face_landmarks:
            face_landmarks = mesh_results.multi_face_landmarks[0]
            h, w = frame.shape[:2]
            face_data["detected"] = True
            face_data["landmarks"] = face_landmarks
            
            # Vẽ landmark trên khuôn mặt
            draw_landmarks(display_frame, face_landmarks)
            
            # Nếu đang calibrating, chỉ hiển thị trạng thái
            if calibrating:
                cv2.putText(display_frame, "Calibrating...", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                return display_frame, face_data
            
            # Kiểm tra mở miệng
            face_data["mouth_open"] = self.mouth_detector.detect_open_mouth(face_landmarks, h, w)
            if face_data["mouth_open"]:
                cv2.putText(display_frame, "Open Mouth Detected!", (10, 90), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Nếu đang tracking, xử lý di chuyển chuột
            if tracking_active:
                # Trích xuất vị trí và di chuyển chuột
                current_position = extract_landmark_positions(face_landmarks, w, h)
                self.mouse_controller.update(current_position)
                
                # Phát hiện nụ cười và click
                face_data["smile_detected"] = self.mouth_detector.detect_smile(face_landmarks, h, w)
                curr_time = time.time()
                
                if face_data["smile_detected"]:
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
                state_text = "Ready - Press 'Start Mouse Control'" if self.mouth_detector.calibrated else "Please calibrate first"
                cv2.putText(display_frame, state_text, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        else:
            # Không tìm thấy khuôn mặt
            if calibrating:
                cv2.putText(display_frame, "No face detected - Keep face centered", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            elif tracking_active:
                cv2.putText(display_frame, "No face detected", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            else:
                cv2.putText(display_frame, "No face detected", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
        return display_frame, face_data