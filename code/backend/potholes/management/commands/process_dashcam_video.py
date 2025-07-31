"""
Django management command to process dashcam videos and sync to database
"""
import os
import csv
import tempfile
from django.core.management.base import BaseCommand
from django.conf import settings
from potholes.models import Pothole
from dashcam_processor.main import main as process_video
from datetime import datetime
import base64
from django.core.files.base import ContentFile


class Command(BaseCommand):
    help = 'Process dashcam video and GPS files to detect potholes and sync to database'

    def add_arguments(self, parser):
        parser.add_argument('--video-path', type=str, required=True,
                          help='Path to the video file')
        parser.add_argument('--gps-directory', type=str, required=True,
                          help='Directory containing GPS .git files')
        parser.add_argument('--distance-threshold', type=float, default=2.5,
                          help='Minimum distance in meters between stored potholes')

    def handle(self, *args, **options):
        video_path = options['video_path']
        gps_directory = options['gps_directory']
        distance_threshold = options['distance_threshold']

        self.stdout.write(
            self.style.SUCCESS(f'Starting video processing: {video_path}')
        )

        # Create temporary directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            output_video_path = os.path.join(temp_dir, "output_with_detections.mp4")
            
            try:
                # Process video using the dashcam pipeline
                process_video(
                    video_path=video_path,
                    git_directory=gps_directory,
                    output_video_path=output_video_path,
                    output_dir=temp_dir,
                    distance_threshold_m=distance_threshold
                )

                # Read the generated CSV and sync to database
                csv_path = os.path.join(temp_dir, "pothole_gps_merged.csv")
                
                if os.path.exists(csv_path):
                    self.sync_csv_to_database(csv_path)
                    self.stdout.write(
                        self.style.SUCCESS('Successfully synced data to database')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('CSV file not found after processing')
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing video: {str(e)}')
                )

    def sync_csv_to_database(self, csv_path):
        """Sync CSV data to Django database"""
        created_count = 0
        updated_count = 0
        
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                try:
                    # Parse data from CSV
                    latitude = float(row['Latitude'])
                    longitude = float(row['Longitude'])
                    pothole_count = int(row['Pothole_Count'])
                    grade = row['Pothole_Grade']
                    frame_data = row.get('Frame_Data', '')
                    frame_number = int(row['Frame']) if row['Frame'] else None
                    
                    # Parse datetime
                    date_str = row['Date']
                    time_str = row['Time']
                    datetime_str = f"{date_str} {time_str}"
                    timestamp = datetime.strptime(datetime_str, "%m/%d/%Y %I:%M:%S %p")
                    
                    # Map grade to severity
                    severity_mapping = {
                        'LOW': 'low',
                        'MEDIUM': 'medium', 
                        'HIGH': 'high',
                        'CRITICAL': 'critical'
                    }
                    severity = severity_mapping.get(grade.upper(), 'medium')
                    
                    # Check if pothole already exists at this location and time
                    existing_pothole = Pothole.objects.filter(
                        latitude=latitude,
                        longitude=longitude,
                        timestamp=timestamp
                    ).first()
                    
                    if existing_pothole:
                        # Update existing pothole
                        existing_pothole.num_potholes = pothole_count
                        existing_pothole.severity = severity
                        existing_pothole.frame_number = frame_number
                        if frame_data:
                            existing_pothole.frame_image_base64 = frame_data
                        existing_pothole.save()
                        updated_count += 1
                    else:
                        # Create new pothole
                        pothole = Pothole(
                            latitude=latitude,
                            longitude=longitude,
                            num_potholes=pothole_count,
                            severity=severity,
                            timestamp=timestamp,
                            frame_number=frame_number,
                            status='reported',
                            description=f"Detected by dashcam processing - Grade: {grade}"
                        )
                        
                        if frame_data:
                            pothole.frame_image_base64 = frame_data
                            
                        pothole.save()
                        created_count += 1
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Error processing row: {str(e)}')
                    )
                    continue
                    
        self.stdout.write(
            self.style.SUCCESS(
                f'Database sync complete: {created_count} created, {updated_count} updated'
            )
        )
