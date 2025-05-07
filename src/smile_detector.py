import cv2
import numpy as np
import time
from src.face_utils import calculate_point_to_line_distance

class SmileDetector:
    def __init__(self):
        # Biến để lưu trữ thông số calibrate
        self.calibrated = False
        self.mouth_width_thres = 0
        self.lip_curve_thres = 0
    
    def calibrate(self, face_mesh):
        """Hiệu chỉnh các ngưỡng để phát hiện nụ cười."""
        mouth_widths = []
        lip_curves = []
        print("Calibrating")

        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        print("Waiting for face...")
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(frame_rgb)
            
            if results.multi_face_landmarks:
                print("Face detected! Starting calibration...")
                start_time = time.time()
                while time.time() - start_time < 5:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    frame = cv2.flip(frame, 1)
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = face_mesh.process(frame_rgb)
                    
                    if results.multi_face_landmarks:
                        for face_landmarks in results.multi_face_landmarks:
                            h, w, _ = frame.shape
                            left_corner = face_landmarks.landmark[61]
                            right_corner = face_landmarks.landmark[291]
                            lip_center = face_landmarks.landmark[14]
                            
                            mouth_width = abs(left_corner.x * w - right_corner.x * w)
                            lip_curve = calculate_point_to_line_distance(
                                lip_center, left_corner, right_corner, w, h
                            )
                            
                            mouth_widths.append(mouth_width)
                            lip_curves.append(lip_curve)

                            cv2.putText(frame, "Calibrating", (10, 30), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                            cv2.imshow("Calibrate Smile", frame)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                # Xử lý dữ liệu thu thập được
                mouth_widths_np = np.array(mouth_widths)
                lip_curves_np = np.array(lip_curves)

                if mouth_widths_np.size > 0 and lip_curves_np.size > 0:
                    MAX_MOUTH_WIDTH = np.max(mouth_widths_np)
                    MIN_MOUTH_WIDTH = np.min(mouth_widths_np)
                    MAX_LIP_CURVE = np.max(lip_curves_np)
                    MIN_LIP_CURVE = np.min(lip_curves_np)
                    
                    self.mouth_width_thres = 0.8 * (MAX_MOUTH_WIDTH - MIN_MOUTH_WIDTH)
                    self.lip_curve_thres = 0.6 * (MAX_LIP_CURVE - MIN_LIP_CURVE)
                    self.calibrated = True
                    print(f"Calibrated! mouth_width_thres = {self.mouth_width_thres}, "
                          f"lip_curve_thres = {self.lip_curve_thres}")
                else:
                    print("Calibration failed! No valid data collected.")
                
                cap.release()
                cv2.destroyAllWindows()
                break
        
        return self.calibrated
    
    def detect(self, landmarks, h, w):
        """Phát hiện nụ cười dựa trên các landmark khuôn mặt."""
        if not self.calibrated:
            return False
        
        left_corner = landmarks.landmark[61]
        right_corner = landmarks.landmark[291]
        lip_center = landmarks.landmark[14]
        
        mouth_width = abs(left_corner.x * w - right_corner.x * w)
        lip_curve = calculate_point_to_line_distance(lip_center, left_corner, right_corner, w, h)
        
        return np.logical_and(mouth_width > self.mouth_width_thres, 
                               lip_curve > self.lip_curve_thres).item()