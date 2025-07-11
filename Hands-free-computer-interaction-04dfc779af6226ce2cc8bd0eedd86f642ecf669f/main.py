import tkinter as tk

from src.face_utils import init_face_mesh, extract_landmark_positions, draw_landmarks
from src.mouth_detector import MouthDetector
from src.mouse_controller import MouseController
from src.gui import HandsFreeGUI

def main():
    face_mesh = init_face_mesh()
    mouth_detector = MouthDetector()
    mouse_controller = MouseController()

    root = tk.Tk()
    app = HandsFreeGUI(root, face_mesh, mouth_detector, mouse_controller)
    root.mainloop()

if __name__ == "__main__":
    main()

# from source.face_utils import init_face_mesh, extract_landmark_positions, draw_landmarks
# from source.mouth_detector import MouthDetector
# from source.mouse_controller import MouseController
# from source.gui import launch_gui

# def main():
#     face_mesh = init_face_mesh()
#     mouth_detector = MouthDetector()
#     mouse_controller = MouseController()
#     launch_gui(face_mesh, mouth_detector, mouse_controller)

# if __name__ == "__main__":
#     main()