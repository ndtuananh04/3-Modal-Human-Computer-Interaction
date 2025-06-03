from srcc.camera_thread import CameraThread
from srcc.face_processor import FaceProcessor
from srcc.mouse_controller import MouseController
import threading

class Pipeline():
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Pipeline, cls).__new__(cls)
            cls._instance.is_started = False
            cls._instance.camera_thread = None
            cls._instance.face_processor = None
            cls._instance.mouse_controller = None 
            cls._instance.latest_processed_frame = None
            cls._instance.lock = threading.Lock()
        return cls._instance
        
    def start(self):
        if not self.is_started:

            self.mouse_controller = MouseController()
            # self.mouse_controller.set_get_cursor(lambda: self.face_processor.get_cursor())

            self.face_processor = FaceProcessor(self.mouse_controller.update_loop)
            self.face_processor.initialize()

            self.camera_thread = CameraThread()
            self.camera_thread.set_frame_callback(self.face_processor.process_frame)
            self.camera_thread.start() 

            self.is_started = True
            print(f"Pipeline started.")
        else:
            print(f"Pipeline is already running.")

    def get_camera_thread(self):
        return self.camera_thread
    
    def get_face_processor(self):
        return self.face_processor
    
    def stop(self):
        if self.is_started:
            if self.camera_thread:
                self.camera_thread.stop_flag.set()

            if self.face_processor:
                self.face_processor.close()
            self.is_started = False
            print(f"Pipeline stopped.")
        else:
            print(f"Pipeline is not running.")