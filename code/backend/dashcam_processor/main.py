"""
Main Pipeline for Dashcam Pothole Detection and Grading
Orchestrates all modules: YOLO detection, GPS parsing, grading, and OCR processing

Features:
- GPU-accelerated YOLO pothole detection using CUDA
- GPU-accelerated OCR text extraction using CUDA  
- Automatic fallback to CPU if GPU not available
- Consolidated GPS data processing from all .git files
- Smart caching to avoid re-processing GPS data
- Enhanced CSV output with GPS source tracking
- Multiple video processing capability
"""
import os
import cv2
import csv
import glob
import base64
import numpy as np
from yolo_detection import PotholeDetector
from gps_parser import convert_git_to_data, find_matching_gps
from pothole_grading import grade_pothole, generate_grading_summary
from ocr_processor import OCRProcessor
from blurring import OCRProcessor_blur, LicensePlateDetector
from geopy.distance import geodesic

def is_far_enough(pt1, pt2, threshold_m=2.5):
    """
    Check if two GPS points are far enough apart using Haversine distance
    
    Args:
        pt1 (tuple): (latitude, longitude) of first point
        pt2 (tuple): (latitude, longitude) of second point
        threshold_m (float): Minimum distance in meters to consider points different
    
    Returns:
        bool: True if points are far enough apart, False otherwise
    """
    try:
        distance_meters = geodesic(pt1, pt2).meters
        return distance_meters > threshold_m
    except Exception as e:
        print(f"Error calculating distance: {e}")
        return True  # Default to storing if error occurs

def should_store_pothole(new_location, stored_locations, threshold_m=2.5):
    """
    Check if a new pothole location should be stored based on distance from previously stored locations
    
    Args:
        new_location (tuple): (latitude, longitude) of new pothole
        stored_locations (list): List of previously stored (latitude, longitude) tuples
        threshold_m (float): Minimum distance in meters to consider locations different
    
    Returns:
        bool: True if pothole should be stored, False if too close to existing ones
    """
    if not stored_locations:
        return True
    
    for stored_location in stored_locations:
        if not is_far_enough(new_location, stored_location, threshold_m):
            return False
    
    return True

def find_video_files(video_directory):
    """
    Find all video files in the specified directory
    
    Args:
        video_directory (str): Directory to search for video files
    
    Returns:
        list: List of video file paths
    """
    video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv', '*.flv', '*.webm']
    video_files = []
    
    for extension in video_extensions:
        video_files.extend(glob.glob(os.path.join(video_directory, extension)))
        video_files.extend(glob.glob(os.path.join(video_directory, extension.upper())))
    
    return sorted(video_files)

def consolidate_gps_files(git_directory="git", output_dir="output_videos_8m", consolidated_csv="consolidated_gps_data.csv"):
    """
    Consolidate all GPS .git files into one CSV file
    
    Args:
        git_directory (str): Directory containing .git files
        output_dir (str): Output directory for consolidated CSV
        consolidated_csv (str): Name of the consolidated CSV file
    
    Returns:
        str: Path to the consolidated CSV file
    """
    consolidated_path = os.path.join(output_dir, consolidated_csv)
    
    # Check if consolidated file already exists
    if os.path.exists(consolidated_path):
        print(f"Consolidated GPS file already exists: {consolidated_path}")
        return consolidated_path
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all .git files
    git_files = glob.glob(os.path.join(git_directory, "*.git"))
    
    if not git_files:
        print(f"No .git files found in {git_directory}")
        return None
    
    print(f"Found {len(git_files)} .git files. Consolidating GPS data...")
    
    all_gps_data = []
    processed_files = 0
    
    # Process each .git file
    for git_file in sorted(git_files):
        try:
            print(f"Processing: {os.path.basename(git_file)}")
            gps_data = convert_git_to_data(git_file)
            
            # Add source file information to each GPS entry
            for entry in gps_data:
                entry['source_file'] = os.path.basename(git_file)
            
            all_gps_data.extend(gps_data)
            processed_files += 1
            
        except Exception as e:
            print(f"Error processing {git_file}: {e}")
            continue
    
    # Write consolidated GPS data to CSV
    if all_gps_data:
        with open(consolidated_path, mode='w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['source_file', 'date', 'time', 'lat', 'lon', 'speed', 'alt']
            csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            csv_writer.writeheader()
            
            # Write all GPS data
            csv_writer.writerows(all_gps_data)
        
        print(f"Consolidated {len(all_gps_data)} GPS entries from {processed_files} files")
        print(f"Consolidated GPS data saved to: {consolidated_path}")
        return consolidated_path
    else:
        print("No GPS data found to consolidate")
        return None

def load_consolidated_gps_data(consolidated_csv_path):
    """
    Load GPS data from consolidated CSV file
    
    Args:
        consolidated_csv_path (str): Path to consolidated GPS CSV file
    
    Returns:
        list: List of GPS data dictionaries
    """
    gps_data = []
    
    if not os.path.exists(consolidated_csv_path):
        print(f"Consolidated GPS file not found: {consolidated_csv_path}")
        return gps_data
    
    try:
        with open(consolidated_csv_path, mode='r', newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for row in csv_reader:
                # Convert string values back to appropriate types
                if row['lat']:
                    row['lat'] = float(row['lat'])
                if row['lon']:
                    row['lon'] = float(row['lon'])
                if row['speed']:
                    row['speed'] = float(row['speed'])
                if row['alt']:
                    row['alt'] = float(row['alt'])
                
                gps_data.append(row)
        
        print(f"Loaded {len(gps_data)} GPS entries from consolidated file")
        return gps_data
        
    except Exception as e:
        print(f"Error loading consolidated GPS data: {e}")
        return gps_data

def check_gpu_availability():
    """
    Check if GPU is available for acceleration
    
    Returns:
        bool: True if GPU is available, False otherwise
    """
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False

def get_gpu_info():
    """
    Get GPU information if available
    
    Returns:
        dict: GPU information or None if not available
    """
    try:
        import torch
        if torch.cuda.is_available():
            return {
                'name': torch.cuda.get_device_name(0),
                'memory_gb': torch.cuda.get_device_properties(0).total_memory / 1024**3,
                'available': True
            }
    except ImportError:
        pass
    
    return {'available': False}

def frame_to_base64(frame, quality=85):
    """
    Convert frame to base64 encoded string for storage in CSV
    
    Args:
        frame: OpenCV frame (numpy array)
        quality (int): JPEG compression quality (1-100, higher = better quality)
    
    Returns:
        str: Base64 encoded frame data
    """
    try:
        # Encode frame as JPEG to reduce size
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        result, encoded_img = cv2.imencode('.jpg', frame, encode_param)
        
        if result:
            # Convert to base64 string
            frame_data = base64.b64encode(encoded_img).decode('utf-8')
            return frame_data
        else:
            print("Warning: Failed to encode frame")
            return ""
    except Exception as e:
        print(f"Error encoding frame: {e}")
        return ""

def base64_to_frame(base64_string):
    """
    Convert base64 string back to OpenCV frame
    
    Args:
        base64_string (str): Base64 encoded frame data
    
    Returns:
        numpy.ndarray: OpenCV frame or None if failed
    """
    try:
        # Decode base64 string
        img_data = base64.b64decode(base64_string)
        
        # Convert to numpy array
        nparr = np.frombuffer(img_data, np.uint8)
        
        # Decode image
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
    except Exception as e:
        print(f"Error decoding frame: {e}")
        return None

def deduplicate_csv_by_location_time(csv_path):
    """
    Remove duplicate rows based on latitude, longitude, date, and time.
    Keep only the row with the highest pothole count for each unique location-time combination.
    
    Args:
        csv_path (str): Path to the CSV file to deduplicate
    """
    import pandas as pd
    
    try:
        # Read the CSV file
        df = pd.read_csv(csv_path)
        
        if df.empty:
            print("CSV file is empty, nothing to deduplicate")
            return
        
        initial_count = len(df)
        print(f"Initial CSV has {initial_count} rows")
        
        # Group by location and time, keeping row with maximum pothole count
        # If multiple rows have same max pothole count, keep the first one
        deduplicated_df = df.loc[df.groupby(['Latitude', 'Longitude', 'Date', 'Time'])['Pothole_Count'].idxmax()]
        
        # Sort by frame number to maintain order
        deduplicated_df = deduplicated_df.sort_values('Frame').reset_index(drop=True)
        
        final_count = len(deduplicated_df)
        removed_count = initial_count - final_count
        
        # Write the deduplicated data back to the CSV
        deduplicated_df.to_csv(csv_path, index=False)
        
        print(f"Deduplication complete:")
        print(f"  - Removed {removed_count} duplicate rows")
        print(f"  - Final CSV has {final_count} rows")
        print(f"  - Kept rows with highest pothole counts for each location-time combination")
        
    except Exception as e:
        print(f"Error during deduplication: {e}")
        print("CSV file remains unchanged")

def process_single_video(video_path, detector, ocr_processor, gps_data, stored_pothole_locations, csv_writer, output_dir, distance_threshold_m=2.5):
    """
    Process a single video file for pothole detection
    
    Args:
        video_path (str): Path to the video file
        detector: PotholeDetector instance
        ocr_processor: OCRProcessor instance
        gps_data (list): GPS data for matching
        stored_pothole_locations (list): List of previously stored pothole locations
        csv_writer: CSV writer object
        output_dir (str): Directory for output files
        distance_threshold_m (float): Minimum distance between stored potholes
    
    Returns:
        tuple: (total_detections, stored_potholes, total_frames)
    """
    video_name = os.path.basename(video_path)
    video_name_without_ext = os.path.splitext(video_name)[0]
    print(f"\n🎥 Processing video: {video_name}")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Error opening video: {video_path}")
        return 0, 0, 0
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"📊 Video properties: {width}x{height} @ {fps:.2f}fps, {total_frames} frames")
    
    # Setup output video writer
    output_video_path = os.path.join(output_dir, f"{video_name_without_ext}_detected.mp4")
    # # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    # # out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    # if not out.isOpened():
    #     print(f"❌ Error creating output video: {output_video_path}")
    #     cap.release()
    #     return 0, 0, 0
    
    frame_count = 0
    total_detections = 0
    stored_potholes = 0
    
    while True:
        success, img = cap.read()
        if not success:
            break
        
        pothole_count = 0
        pothole_grades = []
        
        # Detect potholes using YOLO
        detections = detector.detect_potholes(img)
        total_detections += len(detections)
        
        # Process each detection and draw on image
        for detection in detections:
            pothole_count += 1
            
            # Grade the pothole
            w, h = detection['width'], detection['height']
            conf = detection['confidence']
            grade, color = grade_pothole(w, h, conf)
            pothole_grades.append(grade)
            
            # Draw bounding box with grading color
            x1, y1, w, h = detection['bbox']
            import cvzone
            cvzone.cornerRect(img, (x1, y1, w, h), t=2, colorR=color)
            cvzone.putTextRect(img, f'Pothole {conf:.2f}', (max(0, x1), max(35, y1)), scale=1.5, thickness=2, colorR=color)
            cvzone.putTextRect(img, f'Grade: {grade}', (max(0, x1), max(65, y1 + 30)), scale=1.2, thickness=2, colorR=color)
        
        # Process OCR and GPS only if potholes detected
        if pothole_count > 0:
            # Extract datetime from frame
            date, time, ocr_texts = ocr_processor.extract_datetime_from_frame(img)
            print(f"OCR raw texts (frame {frame_count}): {ocr_texts}")
            
            if date and time:
                # Find matching GPS data from consolidated data
                gps_entry = find_matching_gps(gps_data, date, time)
                if gps_entry:
                    current_location = (gps_entry['lat'], gps_entry['lon'])
                    
                    # Check if this location is far enough from previously stored potholes
                    if should_store_pothole(current_location, stored_pothole_locations, distance_threshold_m):
                        # Calculate distance from previous stored location
                        distance_from_previous = "N/A"
                        if stored_pothole_locations:
                            last_location = stored_pothole_locations[-1]
                            distance_from_previous = f"{geodesic(current_location, last_location).meters:.2f}m"
                        
                        # Join all grades for this frame
                        grades_str = ", ".join(pothole_grades)
                        
                        # Include GPS source file information
                        gps_source = gps_entry.get('source_file', 'Unknown')
                        
                        # Convert frame to base64 for storage
                        print(f"📍 Storing new pothole location: {current_location}")
                        print(f"Encoding frame {frame_count} with {pothole_count} potholes...")
                        # Blur all text in the frame for anonymization
                        frame_blurred, text = LicensePlateDetector.blur_all_text_in_image(img)
                        frame_data = frame_to_base64(frame_blurred, quality=75)  # Lower quality to reduce size
                        
                        csv_writer.writerow([
                            video_name, frame_count, date, time,
                            gps_entry['lat'], gps_entry['lon'],
                            pothole_count, grades_str, gps_source, frame_data, distance_from_previous
                        ])
                        
                        # Add location to stored locations
                        stored_pothole_locations.append(current_location)
                        stored_potholes += 1
                        
                        # Add visual indicator for stored pothole
                        cv2.putText(img, "STORED", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        
                        print(f"✅ {video_name} Frame {frame_count}: {date} {time} | Potholes: {pothole_count} | Grades: {pothole_grades} | Distance: {distance_from_previous}")
                    else:
                        # Calculate distance to nearest stored location for logging
                        nearest_distance = min([geodesic(current_location, stored_loc).meters for stored_loc in stored_pothole_locations])
                        
                        # Add visual indicator for skipped pothole
                        cv2.putText(img, "SKIPPED", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        cv2.putText(img, f"Too close: {nearest_distance:.1f}m", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
                        print(f"❌ {video_name} Frame {frame_count}: Pothole too close to existing one ({nearest_distance:.2f}m < {distance_threshold_m}m threshold) - SKIPPED")
                else:
                    print(f"No GPS match for {date} {time} in {video_name}")
            else:
                print(f"{video_name} Frame {frame_count}: Potholes found, but no valid datetime")
        
        # Add frame info overlay
        cv2.putText(img, f"Frame: {frame_count}", (10, height - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(img, f"Video: {video_name}", (10, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        if pothole_count > 0:
            cv2.putText(img, f"Potholes: {pothole_count}", (10, height - 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        # Write frame to output video
        # out.write(img)
        frame_count += 1
        
        # Progress indicator for long videos
        if frame_count % 1000 == 0:
            print(f"  Progress: {frame_count}/{total_frames} frames processed...")
    
    # Cleanup
    cap.release()
    # out.release()
    
    print(f"✅ Completed {video_name}: {frame_count} frames processed")
    print(f"📹 Output video saved: {output_video_path}")
    return total_detections, stored_potholes, frame_count

def main(video_directory="Media", git_directory="git", output_dir="output_videos", distance_threshold_m=2.5):
    """
    Main pipeline function that processes multiple videos for pothole detection and grading
    
    Args:
        video_directory (str): Directory containing video files to process
        git_directory (str): Directory containing GPS .git files
        output_dir (str): Directory for output files
        distance_threshold_m (float): Minimum distance in meters between stored potholes
    """
    # Check GPU availability
    print("🔍 Checking GPU availability...")
    gpu_info = get_gpu_info()
    if gpu_info['available']:
        print(f"✅ GPU Available: {gpu_info['name']} ({gpu_info['memory_gb']:.1f}GB VRAM)")
    else:
        print("⚠️ GPU not available, using CPU")
    
    print(f"📍 Using geospatial deduplication with {distance_threshold_m}m minimum distance")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all video files
    video_files = find_video_files(video_directory)
    if not video_files:
        print(f"❌ No video files found in {video_directory}")
        return
    
    print(f"🎥 Found {len(video_files)} video files:")
    for video_file in video_files:
        print(f"  - {os.path.basename(video_file)}")
    
    # # Limit to first 10 videos
    # if len(video_files) > 2:
    #     print(f"\n📌 Processing only the first 2 videos out of {len(video_files)} found")
    #     video_files = video_files[:2]
    # else:
    #     print(f"\n📌 Processing all {len(video_files)} videos")
    
    # Consolidate GPS files (only if not already done)
    consolidated_gps_path = consolidate_gps_files(git_directory, output_dir)
    if not consolidated_gps_path:
        print("Failed to consolidate GPS files. Exiting.")
        return
    
    # Load consolidated GPS data
    gps_data = load_consolidated_gps_data(consolidated_gps_path)
    
    # Initialize components with GPU acceleration
    gpu_available = check_gpu_availability()

    detector = PotholeDetector("weights/best_dv14_yv8x.pt", confidence_threshold=0.4)
    # Enable GPU for YOLO model if available
    if gpu_available and hasattr(detector.model, 'to'):
        try:
            detector.model.to('cuda')
            print("✅ YOLO model moved to GPU (CUDA)")
        except Exception as e:
            print(f"⚠️ Failed to move YOLO to GPU: {e}")
    else:
        print("⚠️ YOLO using CPU")
    
    # Initialize OCR processor with GPU acceleration
    ocr_processor = OCRProcessor(['en'], gpu=gpu_available)
    if gpu_available:
        print("✅ OCR processor using GPU (CUDA)")
    else:
        print("⚠️ OCR using CPU")
    
    # Initialize stored pothole locations for radius-based deduplication (shared across all videos)
    stored_pothole_locations = []
    
    # Setup CSV output for all videos
    csv_path = os.path.join(output_dir, "pothole_gps_merged_multi_video.csv")
    
    # Processing statistics
    total_videos_processed = 0
    total_detections_all = 0
    total_stored_all = 0
    total_frames_all = 0
    output_videos = []
    
    with open(csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Video_Name', 'Frame', 'Date', 'Time', 'Latitude', 'Longitude', 'Pothole_Count', 'Pothole_Grade', 'GPS_Source', 'Frame_Data', 'Distance_from_Previous'])
        
        # Process each video
        for video_path in video_files:
            try:
                total_detections, stored_potholes, total_frames = process_single_video(
                    video_path, detector, ocr_processor, gps_data, 
                    stored_pothole_locations, csv_writer, output_dir, distance_threshold_m
                )
                
                # Track output video path
                video_name_without_ext = os.path.splitext(os.path.basename(video_path))[0]
                output_video_path = os.path.join(output_dir, f"{video_name_without_ext}_detected.mp4")
                output_videos.append(output_video_path)
                
                total_videos_processed += 1
                total_detections_all += total_detections
                total_stored_all += stored_potholes
                total_frames_all += total_frames
                
            except Exception as e:
                print(f"❌ Error processing {video_path}: {e}")
                continue
    
    print(f"\n🎉 Processing Complete!")
    print(f"📊 Summary:")
    print(f"   • Videos processed: {total_videos_processed}/{len(video_files)}")
    print(f"   • Total frames processed: {total_frames_all}")
    print(f"   • Total detections: {total_detections_all}")
    print(f"   • Stored unique potholes: {total_stored_all}")
    print(f"   • Filtered out (too close): {total_detections_all - total_stored_all}")
    print(f"   • Distance threshold: {distance_threshold_m}m")
    if total_stored_all > 0:
        reduction_percentage = ((total_detections_all - total_stored_all) / total_detections_all) * 100
        print(f"   • Reduction in duplicates: {reduction_percentage:.1f}%")
    
    print(f"\n📁 Output files:")
    print(f"   • CSV: {csv_path}")
    print(f"   • Consolidated GPS: {consolidated_gps_path}")
    print(f"   • Output videos: {len(output_videos)} generated")
    for i, output_video in enumerate(output_videos, 1):
        print(f"     {i}. {output_video}")
    print(f"   • Output directory: {output_dir}")
    
    # Generate grading summary
    generate_grading_summary(csv_path, output_dir)

if __name__ == "__main__":
    video_directory = "Media"  # Directory containing all video files
    git_directory = "git"  # Directory containing all .git files
    main(video_directory, git_directory)
