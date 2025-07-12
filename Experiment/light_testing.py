import cv2
import mediapipe as mp
import time
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ===== Load model =====
BaseOptions = python.BaseOptions
FaceLandmarker = vision.FaceLandmarker
FaceLandmarkerOptions = vision.FaceLandmarkerOptions

model_path = "face_landmarker.task"
base_options = BaseOptions(model_asset_path=model_path)
options = FaceLandmarkerOptions(
    base_options=base_options,
    output_face_blendshapes=True,
)

landmarker = FaceLandmarker.create_from_options(options)

# ===== Danh sách các chỉ số landmark cần vẽ =====
selected_landmark_ids = {
    0, 1, 4, 5, 6, 7, 8, 10, 13, 14, 17, 21, 33, 37, 39, 40, 46, 52, 53, 54, 55, 58, 61, 63, 65, 66, 67, 70, 78, 80,
    81, 82, 84, 87, 88, 91, 93, 95, 103, 105, 107, 109, 127, 132, 133, 136, 144, 145, 146, 148, 149, 150, 152, 153,
    154, 155, 157, 158, 159, 160, 161, 162, 163, 168, 172, 173, 176, 178, 181, 185, 191, 195, 197, 234, 246, 249, 251,
    263, 267, 269, 270, 276, 282, 283, 284, 285, 288, 291, 293, 295, 296, 297, 300, 308, 310, 311, 312, 314, 317, 318,
    321, 323, 324, 332, 334, 336, 338, 356, 361, 362, 365, 373, 374, 375, 377, 378, 379, 380, 381, 382, 384, 385, 386,
    387, 388, 389, 390, 397, 398, 400, 402, 405, 409, 415, 454, 466, 468, 469, 470, 471, 472, 473, 474, 475, 476, 477
}

# ===== Mở video =====
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error opening video.")
    exit()

# ===== Ghi ảnh mỗi giây =====
last_capture_time = time.time()
image_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Chuyển frame sang định dạng mp.Image (RGB)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    # Nhận diện landmark
    result = landmarker.detect(mp_image)

    # Vẽ các landmark được chọn
    h, w, _ = frame.shape
    if result.face_landmarks:
        for face_landmarks in result.face_landmarks:
            for i, landmark in enumerate(face_landmarks):
                if i in selected_landmark_ids:
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

    # Chụp ảnh mỗi giây
    current_time = time.time()
    if current_time - last_capture_time >= 1.0:
        #filename = f"capture_{image_count:03}.jpg"
       # cv2.imwrite(filename, frame)
        #print(f"Saved: {filename}")
        image_count += 1
        last_capture_time = current_time

    cv2.imshow("Selected Face Landmarks", frame)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()
