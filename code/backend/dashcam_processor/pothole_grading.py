"""
Pothole Grading Module
Handles pothole classification based on size
"""
import os
import csv

def grade_pothole(width, height, confidence):
    """
    Grade potholes based on size (area)
    
    Args:
        width (int): Width of bounding box
        height (int): Height of bounding box  
        confidence (float): Detection confidence (not used in current implementation)
    
    Returns:
        tuple: (grade, color) where grade is severity level and color is BGR tuple
    """
    area = width * height
    
    # Simple size-based grading
    if area < 6000:
        grade = "Low Severity"
        color = (0, 255, 0)  # Green
    elif area > 6001 and area < 8000:
        grade = "Moderate Severity"
        color = (0, 165, 255)  # Orange
    else:
        grade = "High Severity"
        color = (0, 0, 255)  # Red
    
    return grade, color

def generate_grading_summary(csv_path, output_dir):
    """
    Generate a summary report of pothole grading statistics
    
    Args:
        csv_path (str): Path to the CSV file with pothole data
        output_dir (str): Directory to save the summary report
    """
    summary_path = os.path.join(output_dir, "pothole_grading_summary.txt")
    
    grade_counts = {"Low Severity": 0, "Moderate Severity": 0, "High Severity": 0}
    total_potholes = 0
    total_frames = 0
    frames_with_potholes = 0
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for row in csv_reader:
                total_frames += 1
                pothole_count = int(row['Pothole_Count']) if row['Pothole_Count'] else 0
                
                if pothole_count > 0:
                    frames_with_potholes += 1
                    total_potholes += pothole_count
                    
                    # Parse grades from the Pothole_Grade column
                    grades = row['Pothole_Grade'].split(', ') if row['Pothole_Grade'] else []
                    for grade in grades:
                        if grade.strip() in grade_counts:
                            grade_counts[grade.strip()] += 1
                            
    except FileNotFoundError:
        print(f"CSV file not found: {csv_path}")
        return
    
    # Write summary
    with open(summary_path, 'w', encoding='utf-8') as summary_file:
        summary_file.write("POTHOLE GRADING SUMMARY REPORT\n")
        summary_file.write("=" * 40 + "\n\n")
        summary_file.write(f"Total Frames Processed: {total_frames}\n")
        summary_file.write(f"Frames with Potholes: {frames_with_potholes}\n")
        summary_file.write(f"Total Potholes Detected: {total_potholes}\n\n")
        
        summary_file.write("GRADE DISTRIBUTION (by size):\n")
        summary_file.write("-" * 30 + "\n")
        for grade, count in grade_counts.items():
            percentage = (count / total_potholes * 100) if total_potholes > 0 else 0
            summary_file.write(f"{grade}: {count} ({percentage:.1f}%)\n")
        
        summary_file.write("\nGRADE DEFINITIONS:\n")
        summary_file.write("-" * 17 + "\n")
        summary_file.write("Low Severity: Area < 6000 pixels\n")
        summary_file.write("Moderate Severity: 6001-8000 pixels\n")
        summary_file.write("High Severity: Area > 8000 pixels\n")
    
    print(f"Grading summary saved to: {summary_path}")
