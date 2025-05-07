import cv2
import mediapipe as mp
import numpy as np
import time
import pyautogui
import copy

screen_width, screen_height = pyautogui.size()
# Khởi tạo Mediapipe Face Mesh và Face Detection
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)
pyautogui.FAILSAFE = False

# Chỉ số iBUG 68 đối xứng
IBUG_68_INDICES = [
    70, 63, 105, 66, 107,
    336, 296, 334, 293, 300,
    168, 6, 197, 195,
    5, 4, 1, 19, 94,
    33, 160, 158, 133, 153, 144,
    362, 385, 387, 263, 373, 380,
    61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308,
    78, 95, 88, 178, 87, 14, 317, 402
]

# Biến toàn cục để lưu tham số calibrate
CALIBRATED = False
mouth_width_thres = 0
lip_curve_thres = 0

# Variables for optical flow
prev_landmarks = None
vx, vy = 0, 0
old_vx, old_vy = 0, 0
lp_weight = 0.8  

def calculate_point_to_line_distance(point, line_p1, line_p2, w, h):
    point = np.array([point.x * w, point.y * h])
    line_p1 = np.array([line_p1.x * w, line_p1.y * h])
    line_p2 = np.array([line_p2.x * w, line_p2.y * h])
    numerator = abs(np.cross(line_p2 - line_p1, line_p1 - point))
    denominator = np.linalg.norm(line_p2 - line_p1)
    return numerator / denominator if denominator != 0 else 0

def calibrate_smile():
    global mouth_width_thres, lip_curve_thres, CALIBRATED
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
                        lip_curve = calculate_point_to_line_distance(lip_center, left_corner, right_corner, w, h)

                        mouth_widths.append(mouth_width)
                        lip_curves.append(lip_curve)

                        cv2.putText(frame, "Calibrating", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        cv2.imshow("Calibrate Smile", frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            mouth_widths_np = np.array(mouth_widths)
            lip_curves_np = np.array(lip_curves)

            MAX_MOUTH_WIDTH = np.max(mouth_widths_np) if mouth_widths_np.size > 0 else 0
            MIN_MOUTH_WIDTH = np.min(mouth_widths_np) if mouth_widths_np.size > 0 else 0
            MAX_LIP_CURVE = np.max(lip_curves_np) if lip_curves_np.size > 0 else 0
            MIN_LIP_CURVE = np.min(lip_curves_np) if lip_curves_np.size > 0 else 0

            mouth_width_thres = 0.8 * (MAX_MOUTH_WIDTH - MIN_MOUTH_WIDTH)
            lip_curve_thres = 0.6 * (MAX_LIP_CURVE - MIN_LIP_CURVE)
            cap.release()
            cv2.destroyAllWindows()
            CALIBRATED = True
            print(f"Calibrated! mouth_width_thres = {mouth_width_thres}, lip_curve_thres = {lip_curve_thres}")
            break

def detect_smile(landmarks, h, w):
    global CALIBRATED, mouth_width_thres, lip_curve_thres
    if not CALIBRATED:
        return False
    
    left_corner = landmarks.landmark[61]
    right_corner = landmarks.landmark[291]
    lip_center = landmarks.landmark[14]
    mouth_width = abs(left_corner.x * w - right_corner.x * w)
    lip_curve = calculate_point_to_line_distance(lip_center, left_corner, right_corner, w, h)
    return np.logical_and(mouth_width > mouth_width_thres, lip_curve > lip_curve_thres).item()

def calculate_optical_flow(current_landmarks, previous_landmarks, w, h):
    """Calculate optical flow using facial landmarks movement"""
    if previous_landmarks is None or current_landmarks is None:
        return 0, 0

    key_indices = [1, 10]
    # Extract key points for tracking
    current_points = np.array([
        [current_landmarks.landmark[idx].x * w, current_landmarks.landmark[idx].y * h]
        for idx in IBUG_68_INDICES
    ])
    
    previous_points = np.array([
        [previous_landmarks.landmark[idx].x * w, previous_landmarks.landmark[idx].y * h]
        for idx in IBUG_68_INDICES
    ])
    
    movement_vectors = current_points - previous_points

    mean_movement = np.mean(movement_vectors, axis=0)
    
    # Scale movement (similar to Har.py)
    vx = mean_movement[0] * 20
    vy = mean_movement[1] * 20
    
    return vx, vy

# Chạy calibrate trước
calibrate_smile()

# Mở webcam chính
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
prev_time = 0
last_click_time = 0

while cap.isOpened():
    start = time.time()
    ret, frame = cap.read()
    if not ret:
        break
    
    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Xử lý Face Mesh và Face Detection
    mesh_results = face_mesh.process(frame_rgb)

    curr_time = time.time()
    fps = 1 / (curr_time - prev_time)
    prev_time = curr_time

    if mesh_results.multi_face_landmarks:
        for face_landmarks in mesh_results.multi_face_landmarks:
            h, w, _ = frame.shape
            # for idx in IBUG_68_INDICES:
            #     landmark = face_landmarks.landmark[idx]
            #     x, y = int(landmark.x * w), int(landmark.y * h)
            #     cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
            a, b = int(face_landmarks.landmark[14].x * w), int(face_landmarks.landmark[14].y * h)
            cv2.circle(frame, (a, b), 2, (255, 0, 0), -1)

            # Calculate optical flow for mouse movement
            if prev_landmarks is not None:
                flow_vx, flow_vy = calculate_optical_flow(face_landmarks, prev_landmarks, w, h)
                
                vx = flow_vx * (1-lp_weight) + old_vx * lp_weight
                vy = flow_vy * (1-lp_weight) + old_vy * lp_weight
                old_vx = vx
                old_vy = vy
                
                distance = np.sqrt(vx*vx + vy*vy)
                if distance < 20:
                    vx = vx/3
                    vy = vy/3
                
                # Move the mouse
                pyautogui.PAUSE = 0
                pyautogui.moveRel(vx, vy, duration=0)
                
                # Visualize flow vectors
                nose_x, nose_y = int(face_landmarks.landmark[1].x * w), int(face_landmarks.landmark[1].y * h)
                cv2.arrowedLine(frame, (nose_x, nose_y), 
                               (nose_x + int(vx), nose_y + int(vy)), 
                               (0, 0, 255), 2)
            
            # Store current landmarks for next frame
            prev_landmarks = copy.deepcopy(face_landmarks)

            # Phát hiện nụ cười và click
            if detect_smile(face_landmarks, h, w):
                cv2.putText(frame, "Smile Detected!", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                if curr_time - last_click_time > 1:
                    pyautogui.click()
                    last_click_time = curr_time

    cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("MediaPipe Face Mesh + Optical Flow", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
face_mesh.close()

