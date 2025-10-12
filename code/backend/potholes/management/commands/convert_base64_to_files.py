import base64
import os
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import models
from potholes.models import Pothole


class Command(BaseCommand):
    help = 'Convert base64 frame images to actual image files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of records to process in each batch'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be converted without actually doing it'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Find potholes with base64 data but no frame_image file
        potholes = Pothole.objects.filter(
            frame_image_base64__isnull=False
        ).exclude(frame_image_base64='').filter(
            models.Q(frame_image='') | models.Q(frame_image__isnull=True)
        )
        
        total_count = potholes.count()
        self.stdout.write(f'Found {total_count} potholes to convert')
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('No potholes need conversion'))
            return
        
        converted = 0
        errors = 0
        
        # Process in batches to manage memory
        for i in range(0, total_count, batch_size):
            batch = potholes[i:i + batch_size]
            self.stdout.write(f'Processing batch {i//batch_size + 1}: {i+1}-{min(i+batch_size, total_count)}')
            
            for pothole in batch:
                try:
                    if not dry_run:
                        # Decode base64
                        try:
                            image_data = base64.b64decode(pothole.frame_image_base64)
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'Error decoding base64 for pothole {pothole.id}: {e}'))
                            errors += 1
                            continue
                        
                        # Create filename
                        frame_num = pothole.frame_number or 'unknown'
                        filename = f"pothole_{pothole.id}_frame_{frame_num}.jpg"
                        
                        # Create file
                        image_file = ContentFile(image_data, name=filename)
                        
                        # Save to ImageField
                        pothole.frame_image.save(filename, image_file, save=False)
                        
                        # Clear base64 data to free memory immediately
                        pothole.frame_image_base64 = None
                        pothole.save()
                    
                    converted += 1
                    
                    if converted % 50 == 0:
                        self.stdout.write(f'Converted {converted}/{total_count} images...')
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error converting pothole {pothole.id}: {e}'))
                    errors += 1
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'DRY RUN: Would convert {converted} images'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully converted {converted} images to files'))
            if errors > 0:
                self.stdout.write(self.style.WARNING(f'{errors} errors occurred during conversion'))
