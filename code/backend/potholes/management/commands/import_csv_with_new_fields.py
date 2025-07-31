import csv
import random
from datetime import datetime, date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from potholes.models import Pothole

# Increase CSV field size limit to handle large base64 image data
try:
    csv.field_size_limit(131072 * 100)  # Set to a large but reasonable size
except OverflowError:
    csv.field_size_limit(131072)


class Command(BaseCommand):
    help = 'Import pothole data from CSV with new fields'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            default='pothole_gps_merged.csv',
            help='Path to the CSV file to import'
        )

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        
        # Sample contractors for dummy data
        contractors = [
            'ABC Construction Ltd.',
            'Roadway Solutions Inc.',
            'City Infrastructure Corp.',
            'Highway Masters LLC',
            'Urban Development Co.',
            'Prime Builders Ltd.',
            'Metro Construction',
            'Elite Road Works',
            'Superior Infrastructure',
            'Diamond Construction'
        ]
        
        # Generate road completion dates (random dates in the past 2-5 years)
        def get_random_completion_date():
            end_date = date.today()
            start_date = end_date - timedelta(days=365 * 5)  # 5 years ago
            time_between = end_date - start_date
            days_between = time_between.days
            random_days = random.randrange(days_between)
            return start_date + timedelta(days=random_days)
        
        imported_count = 0
        skipped_count = 0
        
        try:
            with open(csv_path, mode='r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                self.stdout.write(f"Starting import from {csv_path}")
                self.stdout.write(f"CSV columns: {reader.fieldnames}")
                
                for row_num, row in enumerate(reader, start=1):
                    try:
                        # Parse date and time
                        date_str = row.get('Date', '').strip()
                        time_str = row.get('Time', '').strip()
                        
                        if not date_str or not time_str:
                            self.stdout.write(f"Row {row_num}: Missing date or time, skipping")
                            skipped_count += 1
                            continue
                        
                        # Parse datetime
                        datetime_str = f"{date_str} {time_str}"
                        try:
                            # Try multiple datetime formats
                            for fmt in ['%m/%d/%Y %I:%M:%S %p', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y %H:%M:%S']:
                                try:
                                    timestamp = datetime.strptime(datetime_str, fmt)
                                    break
                                except ValueError:
                                    continue
                            else:
                                raise ValueError(f"Could not parse datetime: {datetime_str}")
                            
                            timestamp = timezone.make_aware(timestamp)
                        except Exception as e:
                            self.stdout.write(f"Row {row_num}: Error parsing datetime '{datetime_str}': {e}")
                            skipped_count += 1
                            continue
                        
                        # Parse coordinates
                        try:
                            latitude = float(row.get('Latitude', 0))
                            longitude = float(row.get('Longitude', 0))
                        except (ValueError, TypeError):
                            self.stdout.write(f"Row {row_num}: Invalid coordinates")
                            skipped_count += 1
                            continue
                        
                        # Parse pothole count
                        try:
                            num_potholes = int(row.get('Pothole_Count', 1))
                        except (ValueError, TypeError):
                            num_potholes = 1
                        
                        # Parse pothole grade and map to severity
                        grade = row.get('Pothole_Grade', 'Medium').strip()
                        severity_mapping = {
                            'Low Severity': 'low',
                            'Medium Severity': 'medium', 
                            'High Severity': 'high',
                            'Critical Severity': 'critical',
                            'Low': 'low',
                            'Medium': 'medium',
                            'High': 'high',
                            'Critical': 'critical'
                        }
                        severity = severity_mapping.get(grade, 'medium')
                        
                        # Get frame data (base64 image) - handle large data
                        frame_data = row.get('Frame_Data', '').strip()
                        # Only store frame data if it's valid base64 and not too large
                        if frame_data and len(frame_data) > 100:  # Must be more than 100 chars to be valid
                            # Validate it looks like base64
                            if frame_data.startswith('/9j/') or frame_data.startswith('iVBOR'):  # JPEG or PNG base64
                                # Limit size to prevent database issues
                                if len(frame_data) > 500000:  # 500KB limit
                                    frame_data = frame_data[:500000]
                            else:
                                frame_data = None
                        else:
                            frame_data = None
                        
                        frame_number = row.get('Frame', '')
                        if frame_number:
                            try:
                                frame_number = int(frame_number)
                            except ValueError:
                                frame_number = None
                        
                        # Generate dummy data for new fields
                        road_c_date = get_random_completion_date()
                        contractor = random.choice(contractors)
                        
                        # Create pothole record
                        pothole = Pothole.objects.create(
                            latitude=latitude,
                            longitude=longitude,
                            num_potholes=num_potholes,
                            status='reported',  # Default status
                            timestamp=timestamp,
                            severity=severity,
                            frame_image_base64=frame_data if frame_data else None,
                            frame_number=frame_number,
                            description=f"Pothole detected from video analysis. Grade: {grade}",
                            road_c_date=road_c_date,
                            contractor=contractor
                        )
                        
                        imported_count += 1
                        
                        if imported_count % 100 == 0:
                            self.stdout.write(f"Imported {imported_count} records...")
                    
                    except Exception as e:
                        self.stdout.write(f"Row {row_num}: Error importing: {e}")
                        skipped_count += 1
                        continue
                
        except FileNotFoundError:
            self.stdout.write(f"Error: CSV file '{csv_path}' not found")
            return
        except Exception as e:
            self.stdout.write(f"Error reading CSV file: {e}")
            return
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nImport completed!\n"
                f"Imported: {imported_count} records\n"
                f"Skipped: {skipped_count} records\n"
                f"Total potholes in database: {Pothole.objects.count()}"
            )
        )
