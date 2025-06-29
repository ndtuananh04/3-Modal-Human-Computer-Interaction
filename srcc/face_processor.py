import mediapipe as mp
import time
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import cv2 as cv
import threading

class FaceProcessor:
    def __init__(self, result_call_back = None,  model_path="srcc/tasks/face_landmarker.task"):
        self.model_path = model_path
        self.model = None
        self.result = None  
        self.lock = threading.Lock()
        self.is_initialized = False
        self.processed_frame = None
        self.indices = [133, 362] 
        self.result_call_back = result_call_back

    def initialize(self):
        try:
            with open(self.model_path, mode="rb") as f:
                model_buffer = f.read()
            
            def mp_callback(mp_result, output_image, timestamp_ms):
                with self.lock:
                    self.result = mp_result
                self.new_result()
            
            base_options = python.BaseOptions(model_asset_buffer=model_buffer)
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                output_face_blendshapes=False,
                output_facial_transformation_matrixes=False,
                running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
                num_faces=1,
                result_callback=mp_callback
            )
            self.model = vision.FaceLandmarker.create_from_options(options)
            self.is_initialized = True
            print("FaceProcessor Initialized Successfully")
            return True

        except Exception as e:
            print(f"FaceProcessor Init Error: {e}")
            self.is_initialized = False
            return False

    def new_result (self):
        try:
            self.cursor = self.get_cursor()
            if self.result_call_back:
                self.result_call_back(self.cursor)
                # print(f"Cursor Position callback called: {self.cursor}")
        except Exception as e:
            print(f"new_result error: {e}")

    def process_frame(self, frame):
        try:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
            
            timestamp_ms = int(time.time() * 1000)
            self.model.detect_async(mp_image, timestamp_ms)
            
            process_frame = frame.copy()
            with self.lock:
                if self.result and self.result.face_landmarks:
                    for idx in self.indices:
                        landmark = self.result.face_landmarks[0][idx]
                        x = int(landmark.x * frame.shape[1])
                        y = int(landmark.y * frame.shape[0])
                        cv.circle(process_frame, (x, y), 1, (0, 255, 0), -1)
            self.processed_frame = process_frame
            
        except Exception as e:
            print(f"Lỗi xử lý frame: {e}")
            return frame

    def get_processed_frame(self):
        with self.lock:
            if self.processed_frame is not None:
                # resize_frame = cv.resize(self.processed_frame, (480, 360))
                return self.processed_frame
        return None

    def get_cursor(self):
        with self.lock:
            # if self.result and self.result.face_landmarks:
            positions = np.array([[self.result.face_landmarks[0][idx].x * 640, self.result.face_landmarks[0][idx].y * 480] for idx in self.indices])
            mean_position = np.mean(positions, axis=0)
        return mean_position
    
    def close(self):
        if self.model:
            self.model.close()
            self.model = None
            self.is_initialized = False
    
    def __del__(self):
        self.close()

