"""
Complete License Plate Detection System
All-in-one implementation with OCR processor and testing examples
"""
import re
import cv2
import easyocr
import numpy as np
import argparse
import os

class OCRProcessor_blur:
    """
    OCR processor for extracting number plate information from video frames
    """
    
    def __init__(self, languages=['en'], gpu=False):
        """
        Initialize OCR reader
        
        Args:
            languages (list): List of languages for OCR
            gpu (bool): Whether to use GPU acceleration
        """
        print("Initializing EasyOCR...")
        self.reader = easyocr.Reader(languages, gpu=gpu)
        print("EasyOCR initialized successfully!")
    
    def is_valid_license_plate(self, text):
        """
        Check if the extracted text matches common license plate patterns
        
        Args:
            text (str): Text to validate
            
        Returns:
            bool: True if text looks like a license plate
        """
        # Remove spaces and convert to uppercase
        clean_text = re.sub(r'\s+', '', text.upper())
        
        # Common license plate patterns (adjust based on your region)
        patterns = [
            r'^[A-Z]{2}\d{2}[A-Z]{2}\d{4}$',  # AA00AA0000 (Indian format)
            r'^[A-Z]{2}\d{2}[A-Z]\d{4}$',    # AA00A0000 (Indian format)
            r'^[A-Z]{3}\d{4}$',              # AAA0000 (US format)
            r'^[A-Z]{2,3}\d{3,4}$',          # AA000 or AAA0000
            r'^\d{1,3}[A-Z]{1,3}\d{1,4}$',   # 0A000 or 00AA0000
            r'^[A-Z]{1,2}\d{1,4}[A-Z]{0,2}$', # General alphanumeric
            r'^[A-Z0-9]{5,8}$',              # General 5-8 character plates
        ]
        
        # Check against patterns
        for pattern in patterns:
            if re.match(pattern, clean_text):
                return True
                
        # Additional checks for minimum length and alphanumeric content
        if len(clean_text) >= 4 and len(clean_text) <= 10:
            # Must contain both letters and numbers
            has_letters = bool(re.search(r'[A-Z]', clean_text))
            has_numbers = bool(re.search(r'\d', clean_text))
            if has_letters and has_numbers:
                return True
                
        return False
    
    def extract_license_plates_from_ocr_results(self, ocr_results):
        """
        Extract license plate numbers from OCR results
        
        Args:
            ocr_results: OCR results from easyocr containing (bbox, text, confidence)
        
        Returns:
            list: List of dictionaries containing plate info with bbox, text, and confidence
        """
        license_plates = []
        
        for bbox, text, confidence in ocr_results:
            # Clean the text
            cleaned_text = re.sub(r'[^\w\s]', '', text).strip()
            
            # Skip very short texts or low confidence results
            if len(cleaned_text) < 3 or confidence < 0.5:
                continue
                
            # Check if it looks like a license plate
            if self.is_valid_license_plate(cleaned_text):
                license_plates.append({
                    'bbox': bbox,
                    'text': cleaned_text.upper(),
                    'confidence': confidence,
                    'original_text': text
                })
        
        return license_plates
    
    def extract_license_plates_from_frame(self, image):
        """
        Extract all license plates from video frame using OCR on the entire image
        
        Args:
            image: Input video frame (full image, not cropped)
        
        Returns:
            tuple: (license_plates, all_ocr_texts) where license_plates is a list of detected plates
        """
        # Perform OCR on the entire image
        ocr_results = self.reader.readtext(image)
        ocr_texts = [text for (_, text, _) in ocr_results]
        
        # Extract license plates
        license_plates = self.extract_license_plates_from_ocr_results(ocr_results)
        
        return license_plates, ocr_texts
    
    def blur_all_text_from_frame(self, image):
        """
        Blur ALL detected text in the image with maximum intensity
        
        Args:
            image: Input image
            
        Returns:
            tuple: (blurred_image, all_ocr_texts)
        """
        # Perform OCR on the entire image
        ocr_results = self.reader.readtext(image)
        ocr_texts = [text for (_, text, _) in ocr_results]
        
        # Blur all detected text regions with maximum intensity
        blurred_image = image.copy()
        
        for bbox, text, confidence in ocr_results:
            # Use very low confidence threshold to catch all text
            if confidence < 0.1:
                continue
                
            # Convert bbox to coordinates
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            x1, x2 = int(min(x_coords)), int(max(x_coords))
            y1, y2 = int(min(y_coords)), int(max(y_coords))
            
            # Add padding around text region for better coverage
            padding = 5
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(image.shape[1], x2 + padding)
            y2 = min(image.shape[0], y2 + padding)
            
            # Extract and blur the text region with maximum intensity
            if x2 > x1 and y2 > y1:
                roi = blurred_image[y1:y2, x1:x2]
                
                # Maximum blur intensity - multiple blur applications
                blur_strength = 51  # Must be odd number, maximum effective value
                
                # Apply multiple blur passes for 100% intensity
                blurred_roi = cv2.GaussianBlur(roi, (blur_strength, blur_strength), 0)
                blurred_roi = cv2.GaussianBlur(blurred_roi, (blur_strength, blur_strength), 0)
                blurred_roi = cv2.GaussianBlur(blurred_roi, (blur_strength, blur_strength), 0)
                
                # Additional blur using motion blur effect
                kernel_motion_blur = np.ones((15, 15), np.float32) / 225
                blurred_roi = cv2.filter2D(blurred_roi, -1, kernel_motion_blur)
                
                blurred_image[y1:y2, x1:x2] = blurred_roi
        
        return blurred_image, ocr_texts
    
    def get_plate_coordinates(self, license_plates):
        """
        Extract bounding box coordinates for detected license plates
        
        Args:
            license_plates: List of license plate dictionaries from extract_license_plates_from_frame
            
        Returns:
            list: List of bounding box coordinates for each plate
        """
        coordinates = []
        for plate in license_plates:
            bbox = plate['bbox']
            # Convert bbox to standard format (x1, y1, x2, y2)
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            x1, x2 = min(x_coords), max(x_coords)
            y1, y2 = min(y_coords), max(y_coords)
            coordinates.append((x1, y1, x2, y2))
        return coordinates

class LicensePlateDetector:
    """
    Complete license plate detection system
    """
    
    def __init__(self, use_gpu=False):
        """
        Initialize the license plate detector
        
        Args:
            use_gpu (bool): Whether to use GPU acceleration for OCR
        """
        self.ocr_processor = OCRProcessor_blur(languages=['en'], gpu=use_gpu)
        print("License Plate Detector initialized!")
    
    def detect_in_image(self, image_path, save_output=True, show_result=False):
        """
        Detect license plates in a single image
        
        Args:
            image_path (str): Path to the image file
            save_output (bool): Whether to save the output image with bounding boxes
            show_result (bool): Whether to display the result
            
        Returns:
            list: List of detected license plates
        """
        print(f"\nProcessing image: {image_path}")
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Could not load image from {image_path}")
            return []
        
        print(f"Image dimensions: {image.shape}")
        
        # Extract license plates
        license_plates, all_texts = self.ocr_processor.extract_license_plates_from_frame(image)
        
        print(f"All OCR texts detected: {all_texts}")
        print(f"Number of license plates detected: {len(license_plates)}")
        
        # Display results
        for i, plate in enumerate(license_plates):
            print(f"Plate {i+1}:")
            print(f"  Text: {plate['text']}")
            print(f"  Confidence: {plate['confidence']:.2f}")
            print(f"  Original text: {plate['original_text']}")
        
        # Visualize results
        if save_output or show_result:
            output_image = self._blur_plates_on_image(image.copy(), license_plates)
            
            if save_output:
                output_path = image_path.replace('.', '_blurred_plates.')
                cv2.imwrite(output_path, output_image)
                print(f"Output image with blurred plates saved as: {output_path}")
            
            if show_result:
                cv2.imshow('License Plates Blurred', output_image)
                print("Press any key to close the image window...")
                cv2.waitKey(0)
                cv2.destroyAllWindows()
        
        return license_plates
    
    def blur_all_text_in_image(self, image_path, save_output=True):
        """
        Blur ALL detected text in a single image with maximum intensity
        
        Args:
            image_path (str): Path to the image file
            save_output (bool): Whether to save the output image
            
        Returns:
            tuple: (blurred_image, all_texts)
        """
        print(f"\nBlurring ALL text in image with 100% intensity: {image_path}")
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Could not load image from {image_path}")
            return None, []
        
        print(f"Image dimensions: {image.shape}")
        
        # Blur all detected text with maximum intensity
        blurred_image, all_texts = self.ocr_processor.blur_all_text_from_frame(image)
        
        print(f"All detected texts to be blurred: {all_texts}")
        print(f"Total text regions blurred with 100% intensity: {len(all_texts)}")
        
        if save_output:
            output_path = image_path.replace('.', '_100percent_text_blurred.')
            cv2.imwrite(output_path, blurred_image)
            print(f"Output image with ALL text 100% blurred saved as: {output_path}")
        
        return blurred_image, all_texts
    
    def process_multiple_images(self, input_folder, output_folder="dataset_blurred", max_images=float('inf')):
        """
        Process multiple images from a folder and save blurred versions
        
        Args:
            input_folder (str): Path to folder containing input images
            output_folder (str): Path to folder where blurred images will be saved
            max_images (int or float): Maximum number of images to process. Use float('inf') to process all images
            
        Returns:
            list: List of processed image results
        """
        print(f"\nProcessing multiple images from folder: {input_folder}")
        print(f"Output folder: {output_folder}")
        print(f"Maximum images to process: {max_images}")
        
        # Create output folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"Created output folder: {output_folder}")
        
        # Get list of image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
        image_files = []
        
        if os.path.isdir(input_folder):
            for file in os.listdir(input_folder):
                file_lower = file.lower()
                if any(file_lower.endswith(ext) for ext in image_extensions):
                    image_files.append(os.path.join(input_folder, file))
        else:
            print(f"Error: {input_folder} is not a valid directory")
            return []
        
        # Limit to max_images (if specified)
        if max_images != float('inf'):
            image_files = sorted(image_files)[:max_images]
        else:
            image_files = sorted(image_files)
        
        if not image_files:
            print("No image files found in the specified folder")
            return []
        
        print(f"Found {len(image_files)} image(s) to process")
        
        results = []
        
        for i, image_path in enumerate(image_files, 1):
            print(f"\n{'='*60}")
            print(f"Processing image {i}/{len(image_files)}: {os.path.basename(image_path)}")
            print(f"{'='*60}")
            
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                print(f"Error: Could not load image {image_path}")
                continue
            
            print(f"Image dimensions: {image.shape}")
            
            # Blur all detected text with maximum intensity
            blurred_image, all_texts = self.ocr_processor.blur_all_text_from_frame(image)
            
            print(f"Detected texts: {all_texts}")
            print(f"Total text regions blurred: {len(all_texts)}")
            
            # Save blurred image to output folder with same filename as input
            filename = os.path.basename(image_path)
            output_path = os.path.join(output_folder, filename)
            
            cv2.imwrite(output_path, blurred_image)
            print(f"Blurred image saved: {output_path}")
            
            results.append({
                'input_path': image_path,
                'output_path': output_path,
                'texts_detected': all_texts,
                'text_count': len(all_texts)
            })
        
        print(f"\n{'='*80}")
        print(f"BATCH PROCESSING COMPLETE")
        print(f"{'='*80}")
        print(f"Total images processed: {len(results)}")
        print(f"Output folder: {output_folder}")
        
        # Summary statistics
        total_texts = sum(result['text_count'] for result in results)
        print(f"Total text regions blurred across all images: {total_texts}")
        
        return results
    
    def detect_in_webcam(self, camera_index=0):
        """
        Detect license plates using webcam
        
        Args:
            camera_index (int): Camera index (0 for default webcam)
        """
        print("Starting webcam detection...")
        print("Controls:")
        print("  SPACE: Analyze current frame")
        print("  'q': Quit")
        print("  's': Save current frame")
        
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            print(f"Error: Could not open camera {camera_index}")
            return
        
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame from camera")
                break
            
            # Display the frame
            cv2.imshow('Webcam - License Plate Detection', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord(' '):  # Space key
                print(f"\nAnalyzing frame {frame_count}...")
                
                # Detect license plates
                license_plates, all_texts = self.ocr_processor.extract_license_plates_from_frame(frame)
                
                print(f"OCR texts: {all_texts}")
                print(f"License plates found: {len(license_plates)}")
                
                if license_plates:
                    for i, plate in enumerate(license_plates):
                        print(f"  Plate {i+1}: {plate['text']} (confidence: {plate['confidence']:.2f})")
                    
                    # Show result with blurred plates
                    result_frame = self._blur_plates_on_image(frame.copy(), license_plates)
                    cv2.imshow('Detection Result', result_frame)
                else:
                    print("  No license plates detected")
                
                frame_count += 1
            
            elif key == ord('s'):  # Save frame
                filename = f"webcam_frame_{frame_count}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Frame saved as: {filename}")
        
        cap.release()
        cv2.destroyAllWindows()
        print("Webcam detection stopped")
    
    def detect_in_video(self, video_path, sample_every_n_frames=30, save_output=False):
        """
        Detect license plates in a video file
        
        Args:
            video_path (str): Path to the video file
            sample_every_n_frames (int): Process every nth frame
            save_output (bool): Whether to save output video with detections
            
        Returns:
            list: List of all detections with timestamps
        """
        print(f"Processing video: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video {video_path}")
            return []
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"Video info: {total_frames} frames, {fps} FPS, {width}x{height}")
        
        all_detections = []
        
        # Setup video writer if saving output
        if save_output:
            output_path = video_path.replace('.', '_detected_plates.')
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_number = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process every nth frame
            if frame_number % sample_every_n_frames == 0:
                print(f"Processing frame {frame_number}/{total_frames}")
                
                # Detect license plates
                license_plates, all_texts = self.ocr_processor.extract_license_plates_from_frame(frame)
                
                if license_plates:
                    timestamp = frame_number / fps
                    print(f"  Frame {frame_number} (t={timestamp:.1f}s) - Found {len(license_plates)} plates:")
                    
                    for plate in license_plates:
                        print(f"    - {plate['text']} (confidence: {plate['confidence']:.2f})")
                        all_detections.append({
                            'frame': frame_number,
                            'timestamp': timestamp,
                            'plate': plate
                        })
                    
                    # Blur license plates on frame
                    if save_output:
                        frame = self._blur_plates_on_image(frame, license_plates)
            
            # Save frame to output video
            if save_output:
                out.write(frame)
            
            frame_number += 1
        
        cap.release()
        if save_output:
            out.release()
            print(f"Output video saved as: {output_path}")
        
        # Summary
        unique_plates = list(set([d['plate']['text'] for d in all_detections]))
        print(f"\n=== VIDEO ANALYSIS SUMMARY ===")
        print(f"Total detections: {len(all_detections)}")
        print(f"Unique plates: {len(unique_plates)}")
        for plate in unique_plates:
            print(f"  - {plate}")
        
        return all_detections
    
    def _blur_plates_on_image(self, image, license_plates):
        """
        Blur detected license plates on the image
        
        Args:
            image: Image to process
            license_plates: List of detected plates
            
        Returns:
            image: Image with license plates blurred
        """
        coordinates = self.ocr_processor.get_plate_coordinates(license_plates)
        
        for i, (x1, y1, x2, y2) in enumerate(coordinates):
            # Convert coordinates to integers and ensure they're within image bounds
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(image.shape[1], x2)
            y2 = min(image.shape[0], y2)
            
            # Extract the region of interest (license plate area)
            if x2 > x1 and y2 > y1:  # Ensure valid region
                roi = image[y1:y2, x1:x2]
                
                # Apply Gaussian blur to the license plate region
                blur_strength = 15  # Adjust this value for more/less blur
                blurred_roi = cv2.GaussianBlur(roi, (blur_strength, blur_strength), 0)
                
                # Replace the original region with the blurred version
                image[y1:y2, x1:x2] = blurred_roi
        
        return image

def main():
    """
    Main function with command line interface
    """
    parser = argparse.ArgumentParser(description='License Plate Detection System')
    parser.add_argument('--mode', choices=['image', 'webcam', 'video', 'batch'], default='batch',
                       help='Detection mode: image, webcam, video, or batch')
    parser.add_argument('--input', type=str, help='Input file/folder path')
    parser.add_argument('--output', type=str, default='blurred_dataset', help='Output folder for batch processing')
    parser.add_argument('--max-images', type=int, default=10, help='Maximum images to process in batch mode')
    parser.add_argument('--gpu', action='store_true', help='Use GPU acceleration')
    parser.add_argument('--save', action='store_true', help='Save output with detections')
    parser.add_argument('--show', action='store_true', help='Show detection results')
    parser.add_argument('--camera', type=int, default=0, help='Camera index for webcam mode')
    parser.add_argument('--sample', type=int, default=30, help='Sample every N frames for video')
    
    args = parser.parse_args()
    
    # Initialize detector
    detector = LicensePlateDetector(use_gpu=args.gpu)
    
    if args.mode == 'batch':
        input_folder = args.input or "DashCam/frames_output_100"
        detector.process_multiple_images(
            input_folder=input_folder,
            output_folder=args.output,
            max_images=args.max_images
        )
    
    elif args.mode == 'image':
        if not args.input:
            print("Error: --input required for image mode")
            print("Example: python license_plate_detector.py --mode image --input test_image.jpg --show")
            return
        
        if not os.path.exists(args.input):
            print(f"Error: Input file {args.input} does not exist")
            return
        
        detector.blur_all_text_in_image(args.input, save_output=args.save)
    
    elif args.mode == 'webcam':
        detector.detect_in_webcam(camera_index=args.camera)
    
    elif args.mode == 'video':
        if not args.input:
            print("Error: --input required for video mode")
            print("Example: python license_plate_detector.py --mode video --input video.mp4 --save")
            return
        
        if not os.path.exists(args.input):
            print(f"Error: Input file {args.input} does not exist")
            return
        
        detector.detect_in_video(args.input, sample_every_n_frames=args.sample, save_output=args.save)

def test_examples():
    """
    Test function with batch processing for multiple images
    """
    print("Testing License Plate Detection System - Batch Processing")
    print("=" * 60)
    
    # Initialize detector
    detector = LicensePlateDetector(use_gpu=False)
    
    # Process multiple images from frames_output_100 folder
    detector.process_multiple_images(
        input_folder="Datasetv14_yv8/valid/images",
        output_folder="Datasetv14_yv8/valid/blurred", 
        max_images=float('inf')  # Process all images by setting to infinity
    )
    
    # Test single image (optional)
    # detector.blur_all_text_in_image("framejpg", save_output=True)
    
    # Test with webcam (uncomment to test)
    # detector.detect_in_webcam()
    
    # Test with video (uncomment and provide correct path)
    # detector.detect_in_video("test_video.mp4", sample_every_n_frames=30, save_output=True)
    
    print("\nTo test other modes:")
    print("1. Uncomment other test functions above")
    print("2. Or use command line interface:")
    print("   python license_plate_detector.py --mode image --input test_image.jpg --show")
    print("   python license_plate_detector.py --mode webcam")
    print("   python license_plate_detector.py --mode video --input test_video.mp4 --save")

if __name__ == "__main__":
    # Uncomment the line below to use command line interface
    # main()
    
    # Or uncomment the line below to run test examples
    test_examples()
