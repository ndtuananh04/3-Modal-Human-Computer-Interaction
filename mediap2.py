import cv2
import mediapipe as mp
import numpy as np
import time
import pyautogui

screen_width, screen_height = pyautogui.size()
# Khởi tạo Mediapipe Face Mesh và Face Detection
mp_face_mesh = mp.solutions.face_mesh
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)
face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.5)
pyautogui.FAILSAFE = False

# Chỉ số iBUG 68 đối xứng
IBUG_68_INDICES = [
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,  # Đường viền
    336, 296, 334, 293, 300,  # Lông mày trái
    70, 63, 105, 66, 107,  # Lông mày phải
    168, 6, 197, 195 , 49, 279, 4, 458, 278, # Mũi
    263, 249, 390, 373, 374, 380,  # Mắt trái
    33, 7, 163, 144, 145, 153,  # Mắt phải
    61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308,  # Môi ngoài
    78, 191, 80, 81, 82, 14, 312, 311, 310, 415, 308  # Môi trong
]

# Biến toàn cục để lưu tham số calibrate
CALIBRATED = False
mouth_width_thres = 0
lip_curve_thres = 0

# Lịch sử vị trí để làm mượt (moving average)
MOUSE_HISTORY = []
HISTORY_SIZE = 5  # Số frame để tính trung bình trượt

def calculate_point_to_line_distance(point, line_p1, line_p2, w, h):
    point = np.array([point.x * w, point.y * h])
    line_p1 = np.array([line_p1.x * w, line_p1.y * h])
    line_p2 = np.array([line_p2.x * w, line_p2.y * h])
    numerator = abs(np.cross(line_p2 - line_p1, line_p1 - point))
    denominator = np.linalg.norm(line_p2 - line_p1)
    return numerator / denominator if denominator != 0 else 0

def calibrate_smile():
    global mouth_width_thres, lip_curve_thres, CALIBRATED
    MAX_MOUTH_WIDTH = -np.inf
    MIN_MOUTH_WIDTH = np.inf
    MAX_LIP_CURVE = -np.inf
    MIN_LIP_CURVE = np.inf
    print("Hãy cười to trong 5 giây để calibrate...")

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

                        MAX_MOUTH_WIDTH = max(MAX_MOUTH_WIDTH, mouth_width)
                        MIN_MOUTH_WIDTH = min(MIN_MOUTH_WIDTH, mouth_width)
                        MAX_LIP_CURVE = max(MAX_LIP_CURVE, lip_curve)
                        MIN_LIP_CURVE = min(MIN_LIP_CURVE, lip_curve)

                        cv2.putText(frame, "Cuoi trong 3 giay...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        cv2.imshow("Calibrate Smile", frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
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
    return mouth_width > mouth_width_thres and lip_curve > lip_curve_thres

def get_cursor(landmarks, detection_results, w, h, screen_width, screen_height):
    # Từ Face Mesh (landmarks)
    nose = landmarks.landmark[1]  # Điểm mũi
    mesh_x, mesh_y = nose.x , nose.y 
    
    # Từ Face Detection (bounding box)
    det_x, det_y = mesh_x, mesh_y  # Giá trị mặc định nếu không có detection
    if detection_results.detections:
        for detection in detection_results.detections:
            bboxC = detection.location_data.relative_bounding_box
            det_x = bboxC.xmin + bboxC.width / 2  # Trung tâm bounding box
            det_y = bboxC.ymin + bboxC.height / 2

    # Kết hợp trọng số (70% landmarks, 30% detection)
    weight_mesh = 0.7
    weight_det = 0.3
    combined_x = weight_mesh * mesh_x + weight_det * det_x
    combined_y = weight_mesh * mesh_y + weight_det * det_y

    # Làm mượt bằng trung bình trượt
    MOUSE_HISTORY.append([combined_x, combined_y])
    if len(MOUSE_HISTORY) > HISTORY_SIZE:
        MOUSE_HISTORY.pop(0)
    smoothed_x, smoothed_y = np.mean(MOUSE_HISTORY, axis=0)
    mouse_x = screen_width / 2 + screen_width * (smoothed_x-0.5) * 3
    mouse_y = screen_height / 2 + screen_height * (smoothed_y-0.6) * 3
    
    return mouse_x, mouse_y

# Chạy calibrate trước
# calibrate_smile()

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
    detection_results = face_detection.process(frame_rgb)

    curr_time = time.time()
    fps = 1 / (curr_time - prev_time)
    prev_time = curr_time

    # if detection_results.detections:
    #     for detection in detection_results.detections:
    #         h, w, _ = frame.shape
    #         # Lấy thông tin bounding box
    #         bboxC = detection.location_data.relative_bounding_box
    #         x_min = int(bboxC.xmin * w)
    #         y_min = int(bboxC.ymin * h)
    #         box_width = int(bboxC.width * w)
    #         box_height = int(bboxC.height * h)

    #         # Vẽ bounding box
    #         cv2.rectangle(frame, (x_min, y_min), (x_min + box_width, y_min + box_height), (0, 255, 255), 2)

    if mesh_results.multi_face_landmarks:
        for face_landmarks in mesh_results.multi_face_landmarks:
            h, w, _ = frame.shape
            for idx in IBUG_68_INDICES:
                landmark = face_landmarks.landmark[idx]
                x, y = int(landmark.x * w), int(landmark.y * h)
                cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
            a, b = int(face_landmarks.landmark[14].x * w), int(face_landmarks.landmark[14].y * h)
            cv2.circle(frame, (a, b), 2, (255, 0, 0), -1)

            # Điều khiển chuột
            mouse_x, mouse_y = get_cursor(face_landmarks, detection_results, w, h, screen_width, screen_height)
            pyautogui.PAUSE = 0
            print(f"mouse_x = {mouse_x}, mouse_y = {mouse_y}")
            pyautogui.moveTo(mouse_x, mouse_y)  # Điều chỉnh tỷ lệ màn hình

            # Phát hiện nụ cười và click
            # if detect_smile(face_landmarks, h, w):
            #     cv2.putText(frame, "Smile Detected!", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            #     if curr_time - last_click_time > 1:
            #         pyautogui.click()
            #         last_click_time = curr_time

    print(f"Thời gian xử lý: {time.time() - start:.4f} giây")
    cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("MediaPipe Face Mesh + Detection (Smile Click)", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
face_mesh.close()
face_detection.close()