import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time
import threading # Import threading library for synchronization

# Path to the MediaPipe .task model file
# Ensure the 'face_landmarker.task' file is in the same directory as this script
MP_TASK_FILE = "srcc/tasks/face_landmarker.task"

# Load the model from the .task file
try:
    with open(MP_TASK_FILE, mode="rb") as f:
        f_buffer = f.read()
except FileNotFoundError:
    print(f"Error: Model file '{MP_TASK_FILE}' not found. Please ensure the model file is in the same directory as the script.")
    exit()

# Global variable to store detection results and a lock for synchronization
detection_result_global = None
result_lock = threading.Lock()

# Callback function that will be called when detection results are available in LIVE_STREAM mode
def result_callback(result: vision.FaceLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    global detection_result_global
    with result_lock:
        detection_result_global = result

# Configure options for FaceLandmarker
base_options = python.BaseOptions(model_asset_buffer=f_buffer)
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    output_face_blendshapes=True,  # Enable blendshape output
    output_facial_transformation_matrixes=False, # No need for facial transformation matrices
    running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,  # ✅ Changed to LIVE_STREAM mode
    num_faces=1, # Detect only one face
    result_callback=result_callback) # Assign the callback function

# Create the FaceLandmarker object
model = vision.FaceLandmarker.create_from_options(options)

# Open the webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam. Please check webcam connection or access permissions.")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Set frame width
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) # Set frame height

def draw_selected_blendshapes(blendshapes, target_names, width=640, height=150):
    """
    Draws a bar chart for specific blendshapes identified by their names.
    Displays the name and score of each blendshape.

    Args:
        blendshapes (list): List of blendshape objects from MediaPipe.
        target_names (list): List of names (category_name) of blendshapes to display.
        width (int): Width of the chart canvas.
        height (int): Height of the chart canvas.

    Returns:
        numpy.ndarray: Image canvas containing the blendshape chart.
    """
    # Create a white canvas
    canvas = np.ones((height, width, 3), dtype=np.uint8) * 255
    if not blendshapes:
        # If no blendshapes are available, display a message
        cv2.putText(canvas, "No blendshapes data.", (10, height // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        return canvas

    selected_blendshapes = []
    # Filter blendshapes based on target names
    for b in blendshapes:
        if b.category_name in target_names:
            selected_blendshapes.append(b)
    
    # Sort the selected blendshapes by the order of target_names for consistent display
    # Create a dict for easy score lookup by name
    blendshape_map = {b.category_name: b for b in selected_blendshapes}
    sorted_selected_blendshapes = [blendshape_map[name] for name in target_names if name in blendshape_map]


    if not sorted_selected_blendshapes:
        # If no selected blendshapes are found, display a message
        cv2.putText(canvas, f"No selected expressions found ({', '.join(target_names)}).", (10, height // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        return canvas

    num_selected = len(sorted_selected_blendshapes)
    bar_spacing = 20  # Spacing between bars
    # Calculate the width of each bar, ensuring enough space
    bar_width = (width - (num_selected + 1) * bar_spacing) // num_selected
    if bar_width <= 0: # Ensure bar width is not negative
        bar_width = 10

    max_bar_height = height - 80  # Leave space for name and score
    if max_bar_height <= 0: # Ensure bar height is not negative
        max_bar_height = 10

    x_offset = bar_spacing # Starting position to draw bars
    for i, b in enumerate(sorted_selected_blendshapes):
        # Calculate bar height based on score (0 to 1)
        bar_height = int(b.score * max_bar_height)
        
        # Coordinates to draw the bar
        x1 = x_offset + i * (bar_width + bar_spacing)
        y1 = height - bar_height - 40  # Top position of the bar (leave space for name)
        x2 = x1 + bar_width
        y2 = height - 40  # Bottom position of the bar (leave space for score)

        # Ensure coordinates are within canvas limits
        y1 = max(0, y1)
        y2 = min(height, y2)
        x1 = max(0, x1)
        x2 = min(width, x2)

        # Draw the bar chart (orange-blue color)
        color = (255, 150, 50)
        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, -1)
        # Draw border for the bar
        cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 0, 0), 1)

        # Display blendshape name
        text_name = f"{b.category_name}"
        # Calculate text position to center on the bar
        text_size_name = cv2.getTextSize(text_name, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0] # Smaller font for more names
        text_x_name = x1 + (bar_width - text_size_name[0]) // 2
        cv2.putText(canvas, text_name, (text_x_name, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)

        # Display blendshape score
        text_score = f"{b.score:.2f}"
        # Calculate text position to center below the bar
        text_size_score = cv2.getTextSize(text_score, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0] # Smaller font
        text_x_score = x1 + (bar_width - text_size_score[0]) // 2
        cv2.putText(canvas, text_score, (text_x_score, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)

    return canvas

# Main loop to process frames from the webcam
timestamp_ms = 0
while True:
    ret, frame_np = cap.read()
    if not ret:
        print("Could not read frame from webcam. Exiting...")
        break

    # Convert frame from BGR (OpenCV) to RGB (MediaPipe)
    frame_rgb = cv2.cvtColor(frame_np, cv2.COLOR_BGR2RGB)
    # Create MediaPipe Image object
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

    # Increment timestamp for each frame (important for LIVE_STREAM mode)
    timestamp_ms = int(time.time() * 1000)
    # Send frame for asynchronous detection
    model.detect_async(mp_image, timestamp_ms)

    # Safely retrieve detection results
    current_detection_result = None
    with result_lock:
        current_detection_result = detection_result_global

    # If results are available and face landmarks are detected
    if current_detection_result and current_detection_result.face_landmarks:
        h, w, _ = frame_np.shape
        # Draw landmarks on the face
        for landmark in current_detection_result.face_landmarks[0]:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            cv2.circle(frame_np, (x, y), 1, (0, 255, 0), -1) # Draw a green dot

        # If blendshape data is available
        if current_detection_result.face_blendshapes:
            # ✅ BLENDSHAPE NAMES TO DISPLAY ON THE CHART AND PRINT
            selected_names_for_display = [
                # "browInnerUp", "browDownLeft", "browDownRight",
                # "eyeBlinkLeft", "eyeBlinkRight",
                "mouthLeft", "mouthRight", "mouthSmileLeft", "mouthSmileRight",
                # "mouthFunnel", "mouthRollLower", "mouthRollUpper", "jawOpen", "mouthShrugLower"
                "eyeLookDownLeft",
                "eyeLookDownRight",
                "eyeLookInLeft",
                "eyeLookInRight",
                "eyeLookOutLeft",
                "eyeLookOutRight",
                "eyeLookUpLeft",
                "eyeLookUpRight"
 # Using cheekPuff for "mồm thổi"
            ]

            # Draw chart for selected blendshapes
            selected_blend_canvas = draw_selected_blendshapes(current_detection_result.face_blendshapes[0], selected_names_for_display, width=640, height=250) # Increased height for more bars
            # Stack webcam frame and blendshape canvas
            frame_np = np.vstack((frame_np, selected_blend_canvas))
            
            # Print values of specific blendshapes as requested
    else:
        # Display message if no results yet or no face detected
        cv2.putText(frame_np, "Waiting for detection results...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)


    # Display the result frame
    cv2.imshow("FaceLandmarker - Landmarks + Selected Blendshapes (LIVE_STREAM Mode)", frame_np)

    # Press 'ESC' to exit
    if cv2.waitKey(1) & 0xFF == 27:
        break

# Release webcam resources and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()
