import numpy as np
import mediapipe as mp
import cv2

# Khởi tạo Mediapipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

# Chỉ số iBUG 68 đối xứng
IBUG_68_INDICES = np.array([
    70, 63, 105, 66, 107,
    336, 296, 334, 293, 300,
    168, 6, 197, 195,
    5, 4, 1, 19, 94,
    33, 160, 158, 133, 153, 144,
    362, 385, 387, 263, 373, 380,
    61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308,
    78, 95, 88, 178, 87, 14, 317, 402
])

def init_face_mesh(max_faces=1):
    """Khởi tạo và trả về đối tượng FaceMesh của MediaPipe."""
    return mp_face_mesh.FaceMesh(
        max_num_faces=max_faces, 
        refine_landmarks=True, 
        min_detection_confidence=0.5, 
        min_tracking_confidence=0.5
    )

def extract_landmark_positions(landmarks, w, h, indices=None):
    if indices is None:
        indices = IBUG_68_INDICES
        
    positions = np.array([
        [landmarks.landmark[idx].x * w, landmarks.landmark[idx].y * h]
        for idx in indices
    ])
    
    # Tính vị trí trung bình của tất cả các điểm landmark
    mean_position = np.mean(positions, axis=0)
    
    return mean_position

def calculate_point_to_line_distance(point, line_p1, line_p2, w, h):
    point_np = np.array([point.x * w, point.y * h])
    line_p1_np = np.array([line_p1.x * w, line_p1.y * h])
    line_p2_np = np.array([line_p2.x * w, line_p2.y * h])
    
    numerator = np.abs(np.cross(line_p2_np - line_p1_np, line_p1_np - point_np))
    denominator = np.linalg.norm(line_p2_np - line_p1_np)
    return numerator / denominator if denominator != 0 else 0

def calculate_optical_flow(current_landmarks, previous_landmarks, w, h):
    if previous_landmarks is None or current_landmarks is None:
        return 0, 0

    # Trích xuất các điểm quan trọng để theo dõi
    current_points = np.array([
        [current_landmarks.landmark[idx].x * w, current_landmarks.landmark[idx].y * h]
        for idx in IBUG_68_INDICES
    ])
    
    previous_points = np.array([
        [previous_landmarks.landmark[idx].x * w, previous_landmarks.landmark[idx].y * h]
        for idx in IBUG_68_INDICES
    ])
    
    # Tính vector chuyển động
    movement_vectors = current_points - previous_points
    mean_movement = np.mean(movement_vectors, axis=0)
    
    # Scale movement
    vx = mean_movement[0] * 20
    vy = mean_movement[1] * 20
    
    return vx, vy

def draw_landmarks(frame, face_landmarks, indices=None):
    """Vẽ các điểm landmark lên khung hình."""
    h, w, _ = frame.shape
    if indices is None:
        indices = IBUG_68_INDICES
        
    for idx in indices:
        landmark = face_landmarks.landmark[idx]
        x, y = int(landmark.x * w), int(landmark.y * h)
        cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
    
    return frame