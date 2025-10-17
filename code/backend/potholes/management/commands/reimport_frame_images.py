import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from potholes.models import Pothole

# Set high CSV field size limit for very large base64 images
csv.field_size_limit(10000000)  # 10MB limit per field

class Command(BaseCommand):
    help = 'Re-import frame images from CSV without truncation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default='sample_data.csv',
            help='CSV file name (should be in backend directory)'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        csv_path = os.path.join(settings.BASE_DIR, csv_file)
        
        if not os.path.exists(csv_path):
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {csv_path}')
            )
            return

        updated_count = 0
        skipped_count = 0
        error_count = 0

        self.stdout.write(f'Starting frame image re-import from {csv_path}...')

        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Print the headers to understand the CSV structure
                self.stdout.write(f'CSV Headers: {reader.fieldnames}')
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 since header is row 1
                    try:
                        # Get frame number to find matching pothole
                        frame_number = None
                        try:
                            frame_str = row.get('Frame', '').strip()
                            if frame_str and frame_str.isdigit():
                                frame_number = int(frame_str)
                        except (ValueError, TypeError):
                            skipped_count += 1
                            continue
                        
                        if not frame_number:
                            skipped_count += 1
                            continue
                        
                        # Get base64 image data
                        frame_image_base64 = row.get('Frame_Data', '').strip()
                        
                        if not frame_image_base64:
                            skipped_count += 1
                            continue
                        
                        # Clean base64 data
                        if 'base64,' in frame_image_base64:
                            frame_image_base64 = frame_image_base64.split('base64,')[1]
                        
                        # Find pothole with this frame number
                        pothole = Pothole.objects.filter(frame_number=frame_number).first()
                        
                        if pothole:
                            # Check if current image is truncated (exactly 500000 chars)
                            if pothole.frame_image_base64 and len(pothole.frame_image_base64) == 500000:
                                # Update with full image data (no truncation)
                                pothole.frame_image_base64 = frame_image_base64
                                pothole.save()
                                updated_count += 1
                                
                                if updated_count % 10 == 0:
                                    self.stdout.write(f'Updated {updated_count} frame images...')
                                    
                                self.stdout.write(f'Row {row_num}: Updated frame {frame_number} - Size: {len(frame_image_base64)} chars')
                            else:
                                skipped_count += 1
                        else:
                            self.stdout.write(f'Row {row_num}: No pothole found with frame number {frame_number}')
                            skipped_count += 1

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
                f'\nFrame image re-import completed!\n'
                f'✓ Successfully updated: {updated_count} frame images\n'
                f'- Skipped: {skipped_count}\n'
                f'- Errors: {error_count}'
            )
        )
