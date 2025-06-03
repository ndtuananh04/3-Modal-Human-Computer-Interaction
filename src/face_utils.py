import numpy as np
import mediapipe as mp
import cv2
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Khởi tạo Mediapipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

# Chỉ số iBUG 68 đối xứng
INDICES = np.array([
    133, 362
])

mp_task = "task/face_landmarker.task"
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
        indices = INDICES
        
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

def draw_landmarks(frame, face_landmarks, indices=None):
    """Vẽ các điểm landmark lên khung hình."""
    h, w, _ = frame.shape
    if indices is None:
        indices = INDICES
        
    for idx in indices:
        landmark = face_landmarks.landmark[idx]
        x, y = int(landmark.x * w), int(landmark.y * h)
        cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
    
    return frame