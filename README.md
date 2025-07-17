# 3-Modal Human-Computer Interaction
## Introduction
An interactive application supports individuals with mobility impairments using computer. 
## Main Feature
Multimodal Human-Computer Interaction:
- **Head-based Mouse Control**: Adaptive cursor positioning using facial landmarks
- **Facial Expression Recognition**: 13 customizable expressions for actions
- **Voice Command Detection**: Offline speech recognition with custom commands
## Requirements
- Python 3.12
- Webcam
- Microphone
## Installation
### Clone the repository
``` git clone https://github.com/ndtuananh04/3-Modal-Human-Computer-Interaction.git ```
### Create and activate a virtual environment (optional but recommended)
``` python -m venv venv ```
```venv\Scripts\activate ```
### Install the required packages: ###
``` pip install -r requirements.txt ```
## Usage
### Run the application:
``` python app.py ```
### Adjust mouse parameter
- Choose proper mode, LIVE_STREAM for smooth real-time response, IMAGE for synchronous processing with high speed
- Firstly, set beta to 0 and mincutoff to a reasonable value such as 1.0
- Move head steadily at a very low speed to adjust mincutoff (decreasing mincutoff reduces jitter but increases lag)
- Secondly, move head quickly and increase beta until lag is minimized
- Note that, if high speed lag occurs, increase beta, if slow speed jitter appears, decrease mincutoff.
- Then, set a appropriate mouse speed to match your preference and comfort level
### Add preferred blendshapes bindings
- Add preferred blendshape bindings for mouse clicks and keyboard actions
- Test different facial expressions to find comfortable triggers
- Adjust sensitivity thresholds as needed
### Configure Voice Commands
- Choose your preferred microphone device
- Add custom voice commands for frequently used actions
- Double click in specific command to adjust or delete it

## License
This project is licensed under the MIT License - see the LICENSE file for details.
