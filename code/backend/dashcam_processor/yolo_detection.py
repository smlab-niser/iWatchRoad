"""
YOLO Detection Module
Handles pothole detection using YOLO model
"""
import math
import cvzone
from ultralytics import YOLO

class PotholeDetector:
    """
    YOLO-based pothole detector
    """
    
    def __init__(self, model_path="Weights/best.pt", confidence_threshold=0.4):
        """
        Initialize the pothole detector
        
        Args:
            model_path (str): Path to YOLO model weights
            confidence_threshold (float): Minimum confidence for detection
        """
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.class_names = ['Pothole']
    
    def detect_potholes(self, image):
        """
        Detect potholes in an image
        
        Args:
            image: Input image (numpy array)
        
        Returns:
            list: List of detection dictionaries with bbox, confidence, etc.
        """
        detections = []
        results = self.model(image, stream=True)
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                w, h = x2 - x1, y2 - y1
                conf = math.ceil((box.conf[0] * 100)) / 100
                cls = int(box.cls[0])
                
                if conf > self.confidence_threshold:
                    detections.append({
                        'bbox': (x1, y1, w, h),
                        'confidence': conf,
                        'class': cls,
                        'width': w,
                        'height': h
                    })
        
        return detections
    
    def draw_detections(self, image, detections, grades_colors):
        """
        Draw detection bounding boxes and labels on image
        
        Args:
            image: Input image to draw on
            detections: List of detection dictionaries
            grades_colors: List of tuples (grade, color) for each detection
        
        Returns:
            image: Image with drawn detections
        """
        for detection, (grade, color) in zip(detections, grades_colors):
            x1, y1, w, h = detection['bbox']
            conf = detection['confidence']
            cls = detection['class']
            
            # Draw bounding box with grading color
            cvzone.cornerRect(image, (x1, y1, w, h), t=2, colorR=color)
            cvzone.putTextRect(image, f'{self.class_names[cls]} {conf}', 
                             (max(0, x1), max(35, y1)), scale=1, thickness=1, colorR=color)
            cvzone.putTextRect(image, f'Grade: {grade}', 
                             (max(0, x1), max(65, y1 + 30)), scale=0.8, thickness=1, colorR=color)
        
        return image
