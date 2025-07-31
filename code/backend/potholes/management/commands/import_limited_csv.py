from django.core.management.base import BaseCommand
import csv
import json
import base64
from datetime import datetime
from potholes.models import Pothole
import random

class Command(BaseCommand):
    help = 'Import limited number of pothole data from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('--csv-path', type=str, default='pothole_gps_final.csv', help='Path to the CSV file')
        parser.add_argument('--limit', type=int, default=600, help='Maximum number of rows to import')
        parser.add_argument('--clear', action='store_true', help='Clear existing data before import')

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        limit = options['limit']
        clear_existing = options['clear']
        
        if clear_existing:
            self.stdout.write("Clearing existing pothole data...")
            count = Pothole.objects.count()
            Pothole.objects.all().delete()
            self.stdout.write(f"Deleted {count} existing records")
        
        # Dummy contractors for realistic data
        contractors = [
            "ABC Construction Ltd", "XYZ Infrastructure", "City Roads Corp", 
            "BuildRight Contractors", "RoadMaster Inc", "UrbanDev Solutions",
            "Metro Construction", "Highway Builders", "CivilTech Ltd",
            "Infrastructure Pro", "RoadCraft Co", "CityBuild Inc"
        ]
        
        # Status distribution (realistic)
        status_choices = ['reported', 'verified', 'in_progress', 'fixed', 'closed']
        status_weights = [40, 30, 15, 12, 3]  # Percentage distribution
        
        # Severity distribution
        severity_choices = ['low', 'medium', 'high', 'critical']
        severity_weights = [30, 40, 25, 5]
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                # Set field size limit to handle large base64 data
                csv.field_size_limit(10**7)  # 10MB limit
                reader = csv.DictReader(file)
                
                potholes_to_create = []
                processed = 0
                imported = 0
                
                self.stdout.write(f"Starting import of up to {limit} rows from {csv_path}...")
                
                for row in reader:
                    if processed >= limit:
                        break
                        
                    processed += 1
                    
                    try:
                        # Extract coordinates (note the capitalized column names)
                        latitude = float(row.get('Latitude', 0))
                        longitude = float(row.get('Longitude', 0))
                        
                        if latitude == 0 or longitude == 0:
                            continue
                            
                        # Generate location string
                        location_string = f"Lat: {latitude:.6f}, Lng: {longitude:.6f}"
                        
                        # Extract other fields with defaults
                        num_potholes = int(row.get('Pothole_Count', 1))
                        
                        # Map pothole grade to severity
                        grade = row.get('Pothole_Grade', '').lower()
                        if 'low' in grade:
                            severity = 'low'
                        elif 'medium' in grade or 'moderate' in grade:
                            severity = 'medium' 
                        elif 'high' in grade:
                            severity = 'high'
                        elif 'critical' in grade or 'severe' in grade:
                            severity = 'critical'
                        else:
                            severity = random.choices(severity_choices, weights=severity_weights)[0]
                        
                        # Random status based on realistic distribution
                        status = random.choices(status_choices, weights=status_weights)[0]
                        
                        # Generate description with video info
                        video_name = row.get('Video_Name', 'Unknown')
                        frame_num = row.get('Frame', 'N/A')
                        description = f"Pothole detected in {video_name} at frame {frame_num} - {severity} severity"
                        
                        # Handle timestamp from Date and Time columns
                        date_str = row.get('Date', '')
                        time_str = row.get('Time', '')
                        if date_str and time_str:
                            try:
                                # Parse date format MM/DD/YYYY and time format HH:MM:SS AM/PM
                                datetime_str = f"{date_str} {time_str}"
                                timestamp = datetime.strptime(datetime_str, "%m/%d/%Y %I:%M:%S %p")
                            except:
                                timestamp = datetime.now()
                        else:
                            timestamp = datetime.now()
                        
                        # Generate dummy road creation date (random date in past 5 years)
                        road_c_date = datetime(
                            year=random.randint(2019, 2024),
                            month=random.randint(1, 12),
                            day=random.randint(1, 28)
                        ).date()
                        
                        # Random contractor
                        contractor = random.choice(contractors)
                        
                        # Handle frame data (limit to avoid memory issues)
                        frame_image_base64 = None
                        frame_number = None
                        
                        if 'Frame_Data' in row and row['Frame_Data'] and len(row['Frame_Data']) > 100:
                            # Only include frame data for 30% of records to save memory
                            if random.random() < 0.3:
                                frame_data = row['Frame_Data']
                                # Limit frame size to prevent memory issues
                                if len(frame_data) < 500000:  # 500KB limit
                                    frame_image_base64 = frame_data
                                    frame_number = int(row.get('Frame', random.randint(1, 1000)))
                        
                        # Create pothole object
                        pothole = Pothole(
                            latitude=str(latitude),
                            longitude=str(longitude),
                            num_potholes=num_potholes,
                            status=status,
                            severity=severity,
                            description=description,
                            timestamp=timestamp,
                            road_c_date=road_c_date,
                            contractor=contractor,
                            frame_image_base64=frame_image_base64,
                            frame_number=frame_number
                        )
                        
                        potholes_to_create.append(pothole)
                        imported += 1
                        
                        # Batch create every 50 records
                        if len(potholes_to_create) >= 50:
                            Pothole.objects.bulk_create(potholes_to_create, ignore_conflicts=True)
                            self.stdout.write(f"Created {len(potholes_to_create)} records... (Total: {imported})")
                            potholes_to_create = []
                            
                    except Exception as e:
                        self.stdout.write(f"Error processing row {processed}: {str(e)}")
                        continue
                
                # Create remaining records
                if potholes_to_create:
                    Pothole.objects.bulk_create(potholes_to_create, ignore_conflicts=True)
                    self.stdout.write(f"Created final batch of {len(potholes_to_create)} records")
                
                # Final statistics
                total_count = Pothole.objects.count()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n✅ Import completed successfully!"
                        f"\n📊 Processed: {processed} rows"
                        f"\n📊 Imported: {imported} valid records"
                        f"\n📊 Total in database: {total_count}"
                        f"\n📊 Status distribution: {dict(zip(status_choices, status_weights))}%"
                        f"\n📊 Contractors: {len(contractors)} different contractors"
                        f"\n📊 Frame data: ~30% of records include images"
                    )
                )
                
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f"CSV file not found: {csv_path}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error importing CSV: {str(e)}")
            )
