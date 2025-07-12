import mediapipe as mp
import time
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import cv2 as cv
import threading

class FaceProcessor:
    def __init__(self, landmark_call_back = None, blendshape_call_back = None,  model_path="srcc/tasks/face_landmarker.task"):
        self.model_path = model_path
        self.model = None
        self.result = None  
        self.lock = threading.Lock()
        self.is_initialized = False
        self.processed_frame = None

        self.frame_width = 640
        self.frame_height = 480
        self.indices = [133, 362] 

        self.landmark_call_back = landmark_call_back
        self.blendshape_call_back = blendshape_call_back

        self.is_live_stream_mode = True  
        self.mode_change_callback = None

    def set_mode_change_callback(self, callback):
        self.mode_change_callback = callback

    def toggle_mode(self):
        self.close()
        
        self.is_live_stream_mode = not self.is_live_stream_mode
        
        success = self.initialize()
        
        mode_name = "LIVE_STREAM" if self.is_live_stream_mode else "IMAGE"
        print(f"Switched to {mode_name} mode - {'Success' if success else 'Failed'}")
        
        if self.mode_change_callback:
            self.mode_change_callback(mode_name, success)
        
        return success

    def get_current_mode(self):
        return "LIVE_STREAM" if self.is_live_stream_mode else "IMAGE"

    def initialize(self):
        try:
            with open(self.model_path, mode="rb") as f:
                model_buffer = f.read()
            
            base_options = python.BaseOptions(model_asset_buffer=model_buffer)
            if self.is_live_stream_mode:
                options = vision.FaceLandmarkerOptions(
                    base_options=base_options,
                    output_face_blendshapes=True,
                    output_facial_transformation_matrixes=False,
                    running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
                    num_faces=1,
                    result_callback=self.mp_callback
                )
            else:
                options = vision.FaceLandmarkerOptions(
                    base_options=base_options,
                    output_face_blendshapes=True,
                    output_facial_transformation_matrixes=False,
                    running_mode=mp.tasks.vision.RunningMode.IMAGE,
                    num_faces=1
                )
            
            self.model = vision.FaceLandmarker.create_from_options(options)
            self.is_initialized = True
            print("FaceProcessor Initialized Successfully")
            return True

        except Exception as e:
            print(f"FaceProcessor Init Error: {e}")
            self.is_initialized = False
            return False

    def mp_callback(self, mp_result, output_image, timestamp_ms):
        with self.lock:
            self.result = mp_result
        self.new_result()

    def new_result (self):
        try:
            self.cursor = self.get_cursor()
            if self.landmark_call_back and len(self.cursor) > 0:
                self.landmark_call_back(self.cursor)
            if self.blendshape_call_back and self.result and self.result.face_blendshapes:
                self.blendshape_call_back(self.result.face_blendshapes[0])
        except Exception as e:
            print(f"new_result error: {e}")

    def process_frame(self, frame):
        try:
            if not self.is_initialized or self.model is None:
                return frame
            
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)

            if self.is_live_stream_mode:
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
                return process_frame
            else:
                detection_result = self.model.detect(mp_image)

                with self.lock:
                    self.result = detection_result

                self.new_result()
                
                process_frame = frame.copy()
                if detection_result and detection_result.face_landmarks:
                    for idx in self.indices:
                        landmark = detection_result.face_landmarks[0][idx]
                        x = int(landmark.x * frame.shape[1])
                        y = int(landmark.y * frame.shape[0])
                        cv.circle(process_frame, (x, y), 1, (0, 255, 0), -1)
                
                self.processed_frame = process_frame
                return process_frame
                
        except Exception as e:
            print(f"Lỗi xử lý frame: {e}")
            return frame

    def get_processed_frame(self):
        with self.lock:
            if self.processed_frame is not None:
                return self.processed_frame
        return None

    def get_cursor(self):
        with self.lock:
            if self.result and self.result.face_landmarks and len(self.result.face_landmarks) > 0:
                positions = np.array([[self.result.face_landmarks[0][idx].x * self.frame_width, self.result.face_landmarks[0][idx].y * self.frame_height] for idx in self.indices])
                mean_position = np.mean(positions, axis=0)
            else:
                mean_position = []
        return mean_position
    
    def close(self):
        if self.model:
            self.model.close()
            self.model = None
            self.is_initialized = False
    
    def __del__(self):
        self.close()

