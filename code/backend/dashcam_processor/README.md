# DashCam
A YOLO-based system detects potholes from dashcam video in real time and maps detections with GPS data to pinpoint exact locations. The system generates reports for road authorities to ensure timely maintenance.

# Environment Setup
1. Create a conda environment
```bash
conda create -n  dashcam python=3.10 -y
conda activate dashcam
```
2. Install torch
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```
3. Download the dependencies
```bash
pip install -r requirements.txt
```