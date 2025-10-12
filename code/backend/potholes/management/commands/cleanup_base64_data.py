from django.core.management.base import BaseCommand
from django.db import connection
from potholes.models import Pothole


class Command(BaseCommand):
    help = 'Remove base64 data after migration to files and analyze database size impact'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of base64 data'
        )
        parser.add_argument(
            '--analyze-only',
            action='store_true',
            help='Only analyze potential space savings without making changes'
        )

    def handle(self, *args, **options):
        if options['analyze_only']:
            self.analyze_space_usage()
            return
        
        if not options['confirm']:
            self.stdout.write(self.style.WARNING('Add --confirm to actually delete base64 data'))
            self.stdout.write('Add --analyze-only to see potential space savings')
            return
        
        # Only clear base64 for potholes that have image files
        potholes_with_files = Pothole.objects.filter(
            frame_image__isnull=False,
            frame_image_base64__isnull=False
        ).exclude(frame_image='').exclude(frame_image_base64='')
        
        count = potholes_with_files.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No base64 data to clean up'))
            return
        
        self.stdout.write(f'Found {count} records with both frame_image file and base64 data')
        
        # Calculate approximate size before cleanup
        total_base64_size = 0
        sample_size = min(100, count)
        sample_records = potholes_with_files[:sample_size]
        
        for record in sample_records:
            if record.frame_image_base64:
                total_base64_size += len(record.frame_image_base64)
        
        if sample_size > 0:
            avg_size = total_base64_size / sample_size
            estimated_total_size = (avg_size * count) / (1024 * 1024)  # Convert to MB
            self.stdout.write(f'Estimated space to be freed: {estimated_total_size:.2f} MB')
        
        # Clear base64 data
        updated = potholes_with_files.update(frame_image_base64=None)
        
        self.stdout.write(self.style.SUCCESS(f'Cleared base64 data from {updated} records'))
        self.stdout.write(self.style.SUCCESS('Database cleanup completed. Consider running VACUUM on SQLite or OPTIMIZE TABLE on MySQL.'))

    def analyze_space_usage(self):
        """Analyze current database space usage by base64 data."""
        self.stdout.write(self.style.HTTP_INFO('Analyzing database space usage...'))
        
        # Count records by type
        total_records = Pothole.objects.count()
        records_with_base64 = Pothole.objects.filter(
            frame_image_base64__isnull=False
        ).exclude(frame_image_base64='').count()
        
        records_with_files = Pothole.objects.filter(
            frame_image__isnull=False
        ).exclude(frame_image='').count()
        
        records_with_both = Pothole.objects.filter(
            frame_image_base64__isnull=False,
            frame_image__isnull=False
        ).exclude(frame_image_base64='').exclude(frame_image='').count()
        
        self.stdout.write(f'Total pothole records: {total_records}')
        self.stdout.write(f'Records with base64 data: {records_with_base64}')
        self.stdout.write(f'Records with frame image files: {records_with_files}')
        self.stdout.write(f'Records with both (can be cleaned): {records_with_both}')
        
        # Estimate size of base64 data
        if records_with_base64 > 0:
            sample_size = min(50, records_with_base64)
            sample_records = Pothole.objects.filter(
                frame_image_base64__isnull=False
            ).exclude(frame_image_base64='')[:sample_size]
            
            total_sample_size = 0
            for record in sample_records:
                if record.frame_image_base64:
                    total_sample_size += len(record.frame_image_base64)
            
            if sample_size > 0:
                avg_size = total_sample_size / sample_size
                estimated_total_size = (avg_size * records_with_base64) / (1024 * 1024)  # Convert to MB
                cleanable_size = (avg_size * records_with_both) / (1024 * 1024)  # Convert to MB
                
                self.stdout.write(f'Estimated total base64 data size: {estimated_total_size:.2f} MB')
                self.stdout.write(f'Estimated cleanable data size: {cleanable_size:.2f} MB')
                
                # Database file size (SQLite)
                if connection.vendor == 'sqlite':
                    try:
                        import os
                        db_path = connection.settings_dict['NAME']
                        if os.path.exists(db_path):
                            db_size = os.path.getsize(db_path) / (1024 * 1024)  # Convert to MB
                            self.stdout.write(f'Current database file size: {db_size:.2f} MB')
                            percentage = (cleanable_size / db_size) * 100 if db_size > 0 else 0
                            self.stdout.write(f'Cleanable data represents ~{percentage:.1f}% of database size')
                    except Exception as e:
                        self.stdout.write(f'Could not determine database file size: {e}')
                
        self.stdout.write(self.style.HTTP_INFO('Run with --confirm to clean up redundant base64 data'))
