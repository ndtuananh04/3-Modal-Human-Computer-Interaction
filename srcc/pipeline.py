from srcc.camera_thread import CameraThread
from srcc.face_processor import FaceProcessor
from srcc.mouse_controller import MouseController
from srcc.profile_manager import ProfileManager
from srcc.voice_processor import VoiceProcessor
from srcc.blendshape_processor import BlendshapeProcessor
import threading

class Pipeline():
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Pipeline, cls).__new__(cls)
            cls._instance.is_started = False
            cls._instance.camera_thread = None
            cls._instance.profile_manager = None
            cls._instance.face_processor = None
            cls._instance.mouse_controller = None 
            cls._instance.voice_processor = None
            cls._instance.blendshape_processor = None
            cls._instance.latest_processed_frame = None
            cls._instance.lock = threading.Lock()
        return cls._instance
        
    def start(self):
        if not self.is_started:
            self.profile_manager = ProfileManager()

            self.mouse_controller = MouseController()

            self.blendshape_processor = BlendshapeProcessor(self.profile_manager)

            self.voice_processor = VoiceProcessor(self.profile_manager, self.mouse_controller)
            # self.mouse_controller.set_get_cursor(lambda: self.face_processor.get_cursor())

            self.face_processor = FaceProcessor(self.mouse_controller.update_loop, self.blendshape_processor.update_blendshape)
            self.face_processor.initialize()

            self.camera_thread = CameraThread()
            self.camera_thread.set_frame_callback(self.face_processor.process_frame)
            self.camera_thread.start() 

            # self.voice_processor.initialize()

            self.is_started = True
            print(f"Pipeline started.")
        else:
            print(f"Pipeline is already running.")

    def get_profile_manager(self):
        return self.profile_manager
    
    def get_camera_thread(self):
        return self.camera_thread
    
    def get_face_processor(self):
        return self.face_processor
    
    def get_mouse_controller(self):
        return self.mouse_controller
    
    def get_voice_processor(self):
        return self.voice_processor
    
    def get_blendshape_processor(self):
        return self.blendshape_processor
    
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