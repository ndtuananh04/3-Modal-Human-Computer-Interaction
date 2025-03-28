import cv2
import mediapipe as mp
import dlib
import numpy as np
import time

# Khởi tạo Mediapipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, min_detection_confidence=0.5)

# Khởi tạo Dlib Face Detector và Landmark Predictor
dlib_detector = dlib.get_frontal_face_detector()
dlib_predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# Hàm xử lý Mediapipe Face Mesh
def mediapipe_process(frame):
    start_time = time.time()
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)
    
    faces_detected = 0
    landmarks_detected = 0
    if results.multi_face_landmarks:
        faces_detected = len(results.multi_face_landmarks)
        for face_landmarks in results.multi_face_landmarks:
            landmarks_detected = len(face_landmarks.landmark)  # 468 landmarks
            # Vẽ bounding box từ landmarks
            h, w, _ = frame.shape
            x_coords = [lm.x * w for lm in face_landmarks.landmark]
            y_coords = [lm.y * h for lm in face_landmarks.landmark]
            bbox = (int(min(x_coords)), int(min(y_coords)), 
                    int(max(x_coords) - min(x_coords)), int(max(y_coords) - min(y_coords)))
            cv2.rectangle(frame, (bbox[0], bbox[1]), 
                         (bbox[0] + bbox[2], bbox[1] + bbox[3]), (0, 255, 0), 2)
            # Vẽ một số landmarks (ví dụ: 10 điểm chính)
            for idx, landmark in enumerate(face_landmarks.landmark[:68]):  # Chỉ vẽ 10 điểm để tránh rối
                x, y = int(landmark.x * w), int(landmark.y * h)
                cv2.circle(frame, (x, y), 1, (0, 255, 255), -1)
    
    end_time = time.time()
    return end_time - start_time, faces_detected, landmarks_detected

# Hàm xử lý Dlib
def dlib_process(frame):
    start_time = time.time()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = dlib_detector(gray)
    
    faces_detected = len(faces)
    landmarks_detected = 0
    for face in faces:
        x, y, w, h = face.left(), face.top(), face.width(), face.height()
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
        landmarks = dlib_predictor(gray, face)
        landmarks_detected = 68  # Dlib luôn trả về 68 điểm nếu phát hiện khuôn mặt
        for n in range(0, 68):
            x, y = landmarks.part(n).x, landmarks.part(n).y
            cv2.circle(frame, (x, y), 1, (255, 0, 0), -1)
    
    end_time = time.time()
    return end_time - start_time, faces_detected, landmarks_detected

# Khởi tạo video capture (webcam)
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Không thể mở webcam!")
    exit()

# Biến lưu trữ kết quả
mediapipe_times = []
dlib_times = []
mediapipe_faces = []
dlib_faces = []
mediapipe_landmarks = []
dlib_landmarks = []

# Số frame để đo trung bình
num_frames = 600
frame_count = 0

print("Bắt đầu thực nghiệm...")

while frame_count < num_frames:
    ret, frame = cap.read()
    if not ret:
        break

    frame_copy = frame.copy()  # Sao chép để vẽ riêng cho từng phương pháp  # Đo Mediapipe
    mp_time, mp_faces, mp_landmarks = mediapipe_process(frame)
    mediapipe_times.append(mp_time)
    mediapipe_faces.append(mp_faces)
    mediapipe_landmarks.append(mp_landmarks)

    # Đo Dlib
    dlib_time, dlib_faces_count, dlib_landmarks_count = dlib_process(frame_copy)
    dlib_times.append(dlib_time)
    dlib_faces.append(dlib_faces_count)
    dlib_landmarks.append(dlib_landmarks_count)

    # Hiển thị kết quả
    cv2.imshow("Mediapipe", frame)
    cv2.imshow("Dlib", frame_copy)

    frame_count += 1
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Tính toán và in kết quả
avg_mp_time = np.mean(mediapipe_times)
avg_dlib_time = np.mean(dlib_times)
avg_mp_faces = np.mean(mediapipe_faces)
avg_dlib_faces = np.mean(dlib_faces)
avg_mp_landmarks = np.mean(mediapipe_landmarks)
avg_dlib_landmarks = np.mean(dlib_landmarks)

print("\n=== Kết quả thực nghiệm ===")
print(f"Mediapipe - Thời gian trung bình mỗi frame: {avg_mp_time:.4f} giây")
print(f"Dlib - Thời gian trung bình mỗi frame: {avg_dlib_time:.4f} giây")
print(f"Mediapipe - Số khuôn mặt trung bình phát hiện: {avg_mp_faces:.2f}")
print(f"Dlib - Số khuôn mặt trung bình phát hiện: {avg_dlib_faces:.2f}")
print(f"Mediapipe - Số landmarks trung bình phát hiện: {avg_mp_landmarks:.2f}")
print(f"Dlib - Số landmarks trung bình phát hiện: {avg_dlib_landmarks:.2f}")
print(f"Tỷ lệ thời gian (Dlib/Mediapipe): {avg_dlib_time/avg_mp_time:.2f}x")

# Giải phóng tài nguyên
cap.release()
cv2.destroyAllWindows()

# import cv2
# import mediapipe as mp
# import dlib
# import numpy as np
# import time
# from mtcnn import MTCNN

# # Khởi tạo Mediapipe Face Mesh
# mp_face_mesh = mp.solutions.face_mesh
# mp_drawing = mp.solutions.drawing_utils
# face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, min_detection_confidence=0.5)

# # Hàm xử lý Mediapipe Face Mesh
# def mediapipe_process(frame):
#     start_time = time.time()
#     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     results = face_mesh.process(rgb_frame)
    
#     faces_detected = 0
#     landmarks_detected = 0
#     if results.multi_face_landmarks:
#         faces_detected = len(results.multi_face_landmarks)
#         for face_landmarks in results.multi_face_landmarks:
#             landmarks_detected = len(face_landmarks.landmark)  # 468 landmarks
#             # Vẽ bounding box từ landmarks
#             h, w, _ = frame.shape
#             x_coords = [lm.x * w for lm in face_landmarks.landmark]
#             y_coords = [lm.y * h for lm in face_landmarks.landmark]
#             bbox = (int(min(x_coords)), int(min(y_coords)), 
#                     int(max(x_coords) - min(x_coords)), int(max(y_coords) - min(y_coords)))
#             cv2.rectangle(frame, (bbox[0], bbox[1]), 
#                          (bbox[0] + bbox[2], bbox[1] + bbox[3]), (0, 255, 0), 2)
#             # Vẽ một số landmarks (ví dụ: 10 điểm chính)
#             for idx, landmark in enumerate(face_landmarks.landmark[:68]):  # Chỉ vẽ 10 điểm để tránh rối
#                 x, y = int(landmark.x * w), int(landmark.y * h)
#                 cv2.circle(frame, (x, y), 1, (0, 255, 255), -1)
    
#     end_time = time.time()
#     return end_time - start_time, faces_detected, landmarks_detected

# mtcnn_detector = MTCNN()

# def mtcnn_process(frame):
#     start_time = time.time()
#     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     faces = mtcnn_detector.detect_faces(rgb_frame)
    
#     faces_detected = len(faces)
#     landmarks_detected = 0
#     for face in faces:
#         x, y, w, h = face['box']
#         cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 0), 2)
#         landmarks = face['keypoints']
#         landmarks_detected = len(landmarks)  # 5 điểm: mắt, mũi, miệng
#         for key, point in landmarks.items():
#             cv2.circle(frame, point, 1, (0, 255, 255), -1)
    
#     end_time = time.time()
#     return end_time - start_time, faces_detected, landmarks_detected

# # Khởi tạo video capture (webcam)
# cap = cv2.VideoCapture(0)
# if not cap.isOpened():
#     print("Không thể mở webcam!")
#     exit()

# # Biến lưu trữ kết quả
# mediapipe_times = []
# mediapipe_faces = []
# mediapipe_landmarks = []
# mtcnn_times, mtcnn_faces, mtcnn_landmarks = [], [], []
# # Số frame để đo trung bình
# num_frames = 60
# frame_count = 0

# print("Bắt đầu thực nghiệm...")

# while frame_count < num_frames:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     frame_copy = frame.copy()# Sao chép để vẽ riêng cho từng phương pháp  # Đo Mediapipe
#     mp_time, mp_faces, mp_landmarks = mediapipe_process(frame)
#     mediapipe_times.append(mp_time)
#     mediapipe_faces.append(mp_faces)
#     mediapipe_landmarks.append(mp_landmarks)

#     mtcnn_time, mtcnn_faces_count, mtcnn_landmarks_count = mtcnn_process(frame_copy)
#     mtcnn_times.append(mtcnn_time)
#     mtcnn_faces.append(mtcnn_faces_count)
#     mtcnn_landmarks.append(mtcnn_landmarks_count)

#     # Hiển thị kết quả
#     cv2.imshow("Mediapipe", frame)
#     cv2.imshow("MTCNN", frame_copy)

#     frame_count += 1
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# # Tính toán và in kết quả
# avg_mp_time = np.mean(mediapipe_times)
# avg_mtcnn_time = np.mean(mtcnn_times)
# avg_mp_faces = np.mean(mediapipe_faces)
# avg_mtcnn_faces = np.mean(mtcnn_faces)
# avg_mp_landmarks = np.mean(mediapipe_landmarks)
# avg_mtcnn_landmarks = np.mean(mtcnn_landmarks)

# print("\n=== Kết quả thực nghiệm ===")
# print(f"Mediapipe - Thời gian trung bình mỗi frame: {avg_mp_time:.4f} giây")
# print(f"MTCNN - Thời gian trung bình mỗi frame: {avg_mtcnn_time:.4f} giây")
# print(f"Mediapipe - Số khuôn mặt trung bình phát hiện: {avg_mp_faces:.2f}")
# print(f"MTCNN - Số khuôn mặt trung bình phát hiện: {avg_mtcnn_faces:.2f}")
# print(f"Mediapipe - Số landmarks trung bình phát hiện: {avg_mp_landmarks:.2f}")
# print(f"MTCNN - Số landmarks trung bình phát hiện: {avg_mtcnn_landmarks:.2f}")
# print(f"Tỷ lệ thời gian (MTCNN/Mediapipe): {avg_mtcnn_time/avg_mp_time:.2f}x")

# # Giải phóng tài nguyên
# cap.release()
# cv2.destroyAllWindows()

# import cv2
# import mediapipe as mp
# import numpy as np
# import time

# # Khởi tạo Mediapipe Face Detection
# mp_face_detection = mp.solutions.face_detection
# mp_drawing = mp.solutions.drawing_utils
# face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.5)

# # Khởi tạo OpenCV Haar Cascade Face Detector
# face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# # Hàm xử lý Mediapipe
# def mediapipe_process(frame):
#     start_time = time.time()
#     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     results = face_detection.process(rgb_frame)
    
#     faces_detected = 0
#     if results.detections:
#         faces_detected = len(results.detections)
#         for detection in results.detections:
#             bboxC = detection.location_data.relative_bounding_box
#             ih, iw, _ = frame.shape
#             bbox = int(bboxC.xmin * iw), int(bboxC.ymin * ih), \
#                    int(bboxC.width * iw), int(bboxC.height * ih)
#             cv2.rectangle(frame, (bbox[0], bbox[1]), 
#                          (bbox[0] + bbox[2], bbox[1] + bbox[3]), (0, 255, 0), 2)
    
#     end_time = time.time()
#     return end_time - start_time, faces_detected

# # Hàm xử lý OpenCV Haar Cascade
# def opencv_process(frame):
#     start_time = time.time()
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
#     faces_detected = len(faces)
#     for (x, y, w, h) in faces:
#         cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
    
#     end_time = time.time()
#     return end_time - start_time, faces_detected

# # Khởi tạo video capture (webcam)
# cap = cv2.VideoCapture(0)
# if not cap.isOpened():
#     print("Không thể mở webcam!")
#     exit()

# # Biến lưu trữ kết quả
# mediapipe_times = []
# opencv_times = []
# mediapipe_faces = []
# opencv_faces = []

# # Số frame để đo trung bình
# num_frames = 600
# frame_count = 0

# print("Bắt đầu thực nghiệm...")

# while frame_count < num_frames:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     frame_copy = frame.copy()  # Sao chép để vẽ riêng cho từng phương pháp

#     # Đo Mediapipe
#     mp_time, mp_faces = mediapipe_process(frame)
#     mediapipe_times.append(mp_time)
#     mediapipe_faces.append(mp_faces)

#     # Đo OpenCV
#     opencv_time, opencv_faces_count = opencv_process(frame_copy)
#     opencv_times.append(opencv_time)
#     opencv_faces.append(opencv_faces_count)

#     # Hiển thị kết quả
#     cv2.imshow("Mediapipe", frame)
#     cv2.imshow("OpenCV", frame_copy)

#     frame_count += 1
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# # Tính toán và in kết quả
# avg_mp_time = np.mean(mediapipe_times)
# avg_opencv_time = np.mean(opencv_times)
# avg_mp_faces = np.mean(mediapipe_faces)
# avg_opencv_faces = np.mean(opencv_faces)

# print("\n=== Kết quả thực nghiệm ===")
# print(f"Mediapipe - Thời gian trung bình mỗi frame: {avg_mp_time:.4f} giây")
# print(f"OpenCV - Thời gian trung bình mỗi frame: {avg_opencv_time:.4f} giây")
# print(f"Mediapipe - Số khuôn mặt trung bình phát hiện: {avg_mp_faces:.2f}")
# print(f"OpenCV - Số khuôn mặt trung bình phát hiện: {avg_opencv_faces:.2f}")
# print(f"Tỷ lệ thời gian (OpenCV/Mediapipe): {avg_opencv_time/avg_mp_time:.2f}x")

# # Giải phóng tài nguyên
# cap.release()
# cv2.destroyAllWindows()

# import cv2
# import mediapipe as mp
# import numpy as np
# import time

# # Khởi tạo Mediapipe Face Detection
# mp_face_detection = mp.solutions.face_detection
# mp_drawing = mp.solutions.drawing_utils
# face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.5)

# # Khởi tạo YuNet
# yunet = cv2.FaceDetectorYN.create(
#     model="face_detection_yunet_2023mar.onnx",  # Đường dẫn tới file mô hình YuNet
#     config="",  # Không cần config file
#     input_size=(320, 320),  # Kích thước đầu vào
#     score_threshold=0.9,  # Ngưỡng điểm tin cậy
#     nms_threshold=0.3,  # Ngưỡng NMS để loại bỏ trùng lặp
#     top_k=5000  # Số lượng khuôn mặt tối đa
# )

# # Hàm xử lý Mediapipe
# def mediapipe_process(frame):
#     start_time = time.time()
#     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     results = face_detection.process(rgb_frame)
    
#     faces_detected = 0
#     if results.detections:
#         faces_detected = len(results.detections)
#         for detection in results.detections:
#             bboxC = detection.location_data.relative_bounding_box
#             ih, iw, _ = frame.shape
#             bbox = int(bboxC.xmin * iw), int(bboxC.ymin * ih), \
#                    int(bboxC.width * iw), int(bboxC.height * ih)
#             cv2.rectangle(frame, (bbox[0], bbox[1]), 
#                          (bbox[0] + bbox[2], bbox[1] + bbox[3]), (0, 255, 0), 2)
    
#     end_time = time.time()
#     return end_time - start_time, faces_detected

# # Hàm xử lý YuNet
# def yunet_process(frame):
#     start_time = time.time()
#     h, w, _ = frame.shape
#     yunet.setInputSize((w, h))  # Đặt kích thước đầu vào động
#     _, faces = yunet.detect(frame)  # faces: [x, y, w, h, confidence, landmarks...]
    
#     faces_detected = 0
#     if faces is not None:
#         faces_detected = len(faces)
#         for face in faces:
#             x, y, w, h = map(int, face[:4])
#             cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
#             # Vẽ 5 landmarks nếu muốn (tọa độ nằm từ face[4:])
#             # landmarks = face[4:14].reshape(5, 2)  # 5 điểm: mắt, mũi, miệng
#             # for (lx, ly) in landmarks:
#             #     cv2.circle(frame, (int(lx), int(ly)), 1, (255, 0, 0), -1)
    
#     end_time = time.time()
#     return end_time - start_time, faces_detected

# # Khởi tạo video capture (webcam)
# cap = cv2.VideoCapture(0)
# if not cap.isOpened():
#     print("Không thể mở webcam!")
#     exit()

# # Biến lưu trữ kết quả
# mediapipe_times = []
# yunet_times = []
# mediapipe_faces = []
# yunet_faces = []

# # Số frame để đo trung bình
# num_frames = 600
# frame_count = 0

# print("Bắt đầu thực nghiệm...")

# while frame_count < num_frames:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     frame_copy = frame.copy()  # Sao chép để vẽ riêng cho từng phương pháp

#     # Đo Mediapipe
#     mp_time, mp_faces = mediapipe_process(frame)
#     mediapipe_times.append(mp_time)
#     mediapipe_faces.append(mp_faces)

#     # Đo YuNet
#     yunet_time, yunet_faces_count = yunet_process(frame_copy)
#     yunet_times.append(yunet_time)
#     yunet_faces.append(yunet_faces_count)

#     # Hiển thị kết quả
#     cv2.imshow("Mediapipe", frame)
#     cv2.imshow("YuNet", frame_copy)

#     frame_count += 1
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# # Tính toán và in kết quả
# avg_mp_time = np.mean(mediapipe_times)
# avg_yunet_time = np.mean(yunet_times)
# avg_mp_faces = np.mean(mediapipe_faces)
# avg_yunet_faces = np.mean(yunet_faces)

# print("\n=== Kết quả thực nghiệm ===")
# print(f"Mediapipe - Thời gian trung bình mỗi frame: {avg_mp_time:.4f} giây (FPS: {1/avg_mp_time:.2f})")
# print(f"YuNet - Thời gian trung bình mỗi frame: {avg_yunet_time:.4f} giây (FPS: {1/avg_yunet_time:.2f})")
# print(f"Mediapipe - Số khuôn mặt trung bình phát hiện: {avg_mp_faces:.2f}")
# print(f"YuNet - Số khuôn mặt trung bình phát hiện: {avg_yunet_faces:.2f}")
# print(f"Tỷ lệ thời gian (YuNet/Mediapipe): {avg_yunet_time/avg_mp_time:.2f}x")

# # Giải phóng tài nguyên
# cap.release()
# cv2.destroyAllWindows()