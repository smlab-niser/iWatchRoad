import csv
import os
import base64
from io import BytesIO
from PIL import Image
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from potholes.models import Pothole

# Set high CSV field size limit for very large base64 images
csv.field_size_limit(10000000)  # 10MB limit per field

class Command(BaseCommand):
    help = 'Import pothole data from final CSV file with full frame images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default='pothole_gps_final.csv',
            help='CSV file name (should be in backend directory)'
        )
        parser.add_argument(
            '--compress-images',
            action='store_true',
            help='Compress base64 images to reduce size'
        )

    def compress_base64_image(self, base64_data, quality=85, max_size=(800, 600)):
        """Compress a base64 image to reduce its size"""
        try:
            # Decode base64 to image
            image_data = base64.b64decode(base64_data)
            image = Image.open(BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Compress and encode back to base64
            output = BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            compressed_data = base64.b64encode(output.getvalue()).decode('utf-8')
            
            return compressed_data
        except Exception as e:
            self.stdout.write(f'Image compression failed: {str(e)}')
            return None

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        csv_path = os.path.join(settings.BASE_DIR, csv_file)
        
        if not os.path.exists(csv_path):
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {csv_path}')
            )
            return

        imported_count = 0
        skipped_count = 0
        error_count = 0

        self.stdout.write(f'Starting import from {csv_path}...')
        self.stdout.write(f'Image compression: {"Enabled" if options["compress_images"] else "Disabled"}')

        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Print the headers to understand the CSV structure
                self.stdout.write(f'CSV Headers: {reader.fieldnames}')
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 since header is row 1
                    try:
                        # Parse date and time
                        date_str = row.get('Date', '').strip()
                        time_str = row.get('Time', '').strip()
                        
                        if not date_str or not time_str:
                            self.stdout.write(f'Row {row_num}: Missing date or time')
                            skipped_count += 1
                            continue
                            
                        datetime_str = f"{date_str} {time_str}"
                        
                        # Handle different date formats
                        timestamp = None
                        for date_format in ['%m/%d/%Y %I:%M:%S %p', '%d/%m/%Y %I:%M:%S %p', '%Y-%m-%d %H:%M:%S']:
                            try:
                                timestamp = datetime.strptime(datetime_str, date_format)
                                break
                            except ValueError:
                                continue
                        
                        if not timestamp:
                            self.stdout.write(f'Row {row_num}: Invalid date format: {datetime_str}')
                            skipped_count += 1
                            continue

                        # Get coordinates
                        try:
                            latitude = float(row.get('Latitude', 0))
                            longitude = float(row.get('Longitude', 0))
                        except (ValueError, TypeError):
                            self.stdout.write(f'Row {row_num}: Invalid coordinates')
                            skipped_count += 1
                            continue

                        # Get frame number
                        frame_number = None
                        try:
                            frame_str = row.get('Frame', '').strip()
                            if frame_str and frame_str.isdigit():
                                frame_number = int(frame_str)
                        except (ValueError, TypeError):
                            pass
                        
                        # Get video name
                        video_name = row.get('Video_Name', '').strip()
                        
                        # Get base64 image data
                        frame_image_base64 = row.get('Frame_Data', '').strip()
                        
                        # Process base64 image
                        if frame_image_base64:
                            # Clean base64 data
                            if 'base64,' in frame_image_base64:
                                frame_image_base64 = frame_image_base64.split('base64,')[1]
                            
                            # Compress if requested and image is very large
                            if options['compress_images'] and len(frame_image_base64) > 1000000:  # > 1MB
                                self.stdout.write(f'Row {row_num}: Compressing large image...')
                                compressed = self.compress_base64_image(frame_image_base64)
                                if compressed:
                                    frame_image_base64 = compressed
                                    self.stdout.write(f'Row {row_num}: Image compressed from {len(row.get("Frame_Data", ""))} to {len(frame_image_base64)} chars')
                            
                            # Keep full size for best quality (no truncation)
                            # Only limit if absolutely necessary for database constraints
                            if len(frame_image_base64) > 5000000:  # 5MB limit
                                self.stdout.write(f'Row {row_num}: Image extremely large, limiting to 5MB...')
                                frame_image_base64 = frame_image_base64[:5000000]

                        # Parse pothole grade to severity
                        pothole_grade = row.get('Pothole_Grade', '').strip()
                        
                        # Handle multiple grades
                        grades = [grade.strip() for grade in pothole_grade.split(',')]
                        
                        # Determine severity based on highest grade
                        severity = 'low'
                        if any('High' in grade or 'Critical' in grade for grade in grades):
                            severity = 'high'
                        elif any('Medium' in grade or 'Moderate' in grade for grade in grades):
                            severity = 'medium'
                        elif any('Low' in grade for grade in grades):
                            severity = 'low'

                        # Get pothole count
                        try:
                            pothole_count = int(row.get('Pothole_Count', 1))
                        except (ValueError, TypeError):
                            pothole_count = 1

                        # Check if pothole already exists at this exact location and time
                        existing = Pothole.objects.filter(
                            latitude=str(latitude),
                            longitude=str(longitude),
                            timestamp=timestamp
                        ).first()

                        if existing:
                            # Update existing pothole
                            if pothole_count > existing.num_potholes:
                                existing.num_potholes = pothole_count
                                existing.severity = severity
                            
                            # Update frame data if available and not already set
                            if frame_number and not existing.frame_number:
                                existing.frame_number = frame_number
                            if frame_image_base64 and not existing.frame_image_base64:
                                existing.frame_image_base64 = frame_image_base64
                            
                            existing.save()
                            skipped_count += 1
                        else:
                            # Create description including video name if available
                            description = f"GPS detected pothole. Grade: {pothole_grade}"
                            if video_name:
                                description += f" (Video: {video_name})"
                            
                            # Create new pothole entry
                            Pothole.objects.create(
                                timestamp=timestamp,
                                latitude=str(latitude),
                                longitude=str(longitude),
                                num_potholes=pothole_count,
                                severity=severity,
                                status='reported',
                                description=description,
                                frame_number=frame_number,
                                frame_image_base64=frame_image_base64
                            )
                            imported_count += 1
                            
                            if imported_count % 50 == 0:
                                self.stdout.write(f'Imported {imported_count} potholes...')

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Row {row_num}: Error processing - {str(e)}')
                        )
                        error_count += 1
                        continue

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to read CSV file: {str(e)}')
            )
            return

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nImport completed!\n'
                f'✓ Successfully imported: {imported_count} potholes\n'
                f'- Skipped (duplicates/updates): {skipped_count}\n'
                f'- Errors: {error_count}\n'
                f'- Total in database: {Pothole.objects.count()}'
            )
        )
