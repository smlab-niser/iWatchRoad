import random
from datetime import datetime, date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from potholes.models import Pothole
import base64


class Command(BaseCommand):
    help = 'Generate large amount of dummy pothole data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=1500,
            help='Number of pothole records to create (default: 1500)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating new records'
        )

    def handle(self, *args, **options):
        count = options['count']
        clear_existing = options['clear']
        
        if clear_existing:
            self.stdout.write("Clearing existing pothole data...")
            deleted_count = Pothole.objects.count()
            Pothole.objects.all().delete()
            self.stdout.write(f"Deleted {deleted_count} existing records")
        
        self.stdout.write(f"Generating {count} dummy pothole records...")
        
        # Bhubaneswar and surrounding areas bounding box (expanded)
        lat_min, lat_max = 20.1500, 20.4500
        lng_min, lng_max = 85.6500, 85.9500
        
        # Sample locations with realistic areas around Bhubaneswar
        locations = [
            {"lat": 20.2961, "lng": 85.8245, "area": "Master Canteen Square"},
            {"lat": 20.3009, "lng": 85.8066, "area": "Rajmahal Square"},
            {"lat": 20.2843, "lng": 85.8280, "area": "Kalpana Square"},
            {"lat": 20.2765, "lng": 85.8432, "area": "Station Square"},
            {"lat": 20.3152, "lng": 85.8134, "area": "Jayadev Vihar"},
            {"lat": 20.3211, "lng": 85.8298, "area": "Saheed Nagar"},
            {"lat": 20.2890, "lng": 85.8156, "area": "IRC Village"},
            {"lat": 20.2456, "lng": 85.8378, "area": "Unit 4 Market"},
            {"lat": 20.2634, "lng": 85.8289, "area": "Unit 1 Market"},
            {"lat": 20.3087, "lng": 85.7934, "area": "Patia"},
            {"lat": 20.2723, "lng": 85.7845, "area": "Old Town"},
            {"lat": 20.3234, "lng": 85.8567, "area": "Chandrasekharpur"},
            {"lat": 20.2567, "lng": 85.8123, "area": "Laxmisagar"},
            {"lat": 20.2812, "lng": 85.8567, "area": "VSS Nagar"},
            {"lat": 20.3456, "lng": 85.8234, "area": "Niladri Vihar"},
            {"lat": 20.3678, "lng": 85.8456, "area": "Kalinga Nagar"},
            {"lat": 20.1987, "lng": 85.7654, "area": "Nayapalli"},
            {"lat": 20.2345, "lng": 85.8901, "area": "Rasulgarh"},
            {"lat": 20.3567, "lng": 85.7890, "area": "Kiit University"},
            {"lat": 20.2890, "lng": 85.9012, "area": "Mancheswar"},
            {"lat": 20.2134, "lng": 85.8567, "area": "Khandagiri"},
            {"lat": 20.1876, "lng": 85.8234, "area": "Udayagiri"},
            {"lat": 20.3789, "lng": 85.8123, "area": "Tomando"},
            {"lat": 20.2567, "lng": 85.7432, "area": "Jatni"},
            {"lat": 20.4123, "lng": 85.8765, "area": "Khordha"},
            {"lat": 20.3245, "lng": 85.9234, "area": "Cuttack Road"},
            {"lat": 20.2789, "lng": 85.7123, "area": "Balianta"},
            {"lat": 20.3456, "lng": 85.8890, "area": "Pahala"},
            {"lat": 20.2123, "lng": 85.7890, "area": "Bhimpur"},
            {"lat": 20.3678, "lng": 85.7567, "area": "Tankapani Road"},
        ]
        
        # Status distribution (more reported and verified)
        statuses = [
            ('reported', 40),
            ('verified', 30),
            ('in_progress', 15),
            ('fixed', 12),
            ('closed', 3)
        ]
        
        # Severity distribution (realistic distribution)
        severities = [
            ('low', 30),
            ('medium', 40),
            ('high', 25),
            ('critical', 5)
        ]
        
        # Contractors list (expanded)
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
            'Diamond Construction',
            'Golden Gate Builders',
            'Royal Infrastructure',
            'Mega Projects Ltd.',
            'Swift Construction',
            'Pioneer Roadways',
            'Modern Infrastructure',
            'Classic Builders',
            'Advanced Construction',
            'Supreme Infrastructure',
            'Perfect Roadworks',
            'Odisha Public Works Dept.',
            'NHAI Contractors',
            'State Highway Division',
            'Municipal Corporation',
            'Smart City Mission',
            'KIIFB Projects',
            'L&T Infrastructure',
            'Shapoorji Pallonji',
            'GMR Infrastructure',
            'IRB Infrastructure'
        ]
        
        # Description templates
        description_templates = [
            "Large pothole causing traffic disruption near {area}",
            "Multiple potholes detected on main road in {area}",
            "Deep pothole affecting vehicle movement in {area}",
            "Road surface damage reported by citizens in {area}",
            "Monsoon-related road deterioration in {area}",
            "Heavy vehicle damage causing potholes in {area}",
            "Construction work aftermath in {area}",
            "Drainage overflow damage on road in {area}",
            "Emergency repair needed for road in {area}",
            "Safety hazard due to road condition in {area}",
            "Regular maintenance required in {area}",
            "Citizen complaint about road quality in {area}",
            "Video analysis detected damage in {area}",
            "AI surveillance system alert for {area}",
            "Municipal inspection identified issues in {area}"
        ]
        
        # Generate dummy base64 image data (small placeholder)
        def generate_dummy_frame_data():
            # Create a simple 1x1 pixel JPEG in base64
            import io
            try:
                # Simple base64 encoded 1x1 pixel JPEG
                dummy_b64 = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
                return dummy_b64 if random.random() < 0.7 else None  # 70% chance to have frame data
            except:
                return None
        
        # Helper function to get weighted random choice
        def weighted_choice(choices):
            total = sum(weight for choice, weight in choices)
            r = random.randint(1, total)
            upto = 0
            for choice, weight in choices:
                if upto + weight >= r:
                    return choice
                upto += weight
            return choices[-1][0]  # fallback
        
        # Generate road completion dates (random dates in the past 2-8 years)
        def get_random_completion_date():
            end_date = date.today()
            start_date = end_date - timedelta(days=365 * 8)  # 8 years ago
            time_between = end_date - start_date
            days_between = time_between.days
            random_days = random.randrange(days_between)
            return start_date + timedelta(days=random_days)
        
        # Generate timestamps (mostly recent, some older)
        def get_random_timestamp():
            now = timezone.now()
            # 70% in last 6 months, 20% in last year, 10% older
            rand = random.random()
            if rand < 0.7:  # Last 6 months
                days_back = random.randint(0, 180)
            elif rand < 0.9:  # Last year
                days_back = random.randint(180, 365)
            else:  # Older
                days_back = random.randint(365, 1095)  # Up to 3 years
            
            timestamp = now - timedelta(days=days_back)
            # Add random time of day
            random_time = timedelta(
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59)
            )
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0) + random_time
        
        created_count = 0
        batch_size = 100
        potholes_to_create = []
        
        for i in range(count):
            # Use predefined locations 40% of the time, random coordinates 60%
            if random.random() < 0.4 and locations:
                location = random.choice(locations)
                # Add small variation to coordinates
                latitude = location['lat'] + random.uniform(-0.002, 0.002)
                longitude = location['lng'] + random.uniform(-0.002, 0.002)
                area = location['area']
            else:
                # Generate random coordinates within Bhubaneswar area
                latitude = random.uniform(lat_min, lat_max)
                longitude = random.uniform(lng_min, lng_max)
                area = "Random Location"
            
            # Generate other fields
            num_potholes = random.choices(
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                weights=[40, 25, 15, 8, 5, 3, 2, 1, 0.5, 0.5]
            )[0]
            
            status = weighted_choice(statuses)
            severity = weighted_choice(severities)
            contractor = random.choice(contractors)
            road_c_date = get_random_completion_date()
            timestamp = get_random_timestamp()
            
            # Generate description
            description = random.choice(description_templates).format(area=area)
            if num_potholes > 1:
                description = f"{description} (Count: {num_potholes})"
            
            # Generate frame data (not for all records to save space)
            frame_data = generate_dummy_frame_data()
            frame_number = random.randint(1, 10000) if frame_data else None
            
            pothole = Pothole(
                latitude=round(latitude, 7),
                longitude=round(longitude, 7),
                num_potholes=num_potholes,
                status=status,
                severity=severity,
                timestamp=timestamp,
                description=description,
                contractor=contractor,
                road_c_date=road_c_date,
                frame_image_base64=frame_data,
                frame_number=frame_number
            )
            
            potholes_to_create.append(pothole)
            
            # Create in batches for better performance
            if len(potholes_to_create) >= batch_size:
                Pothole.objects.bulk_create(potholes_to_create)
                created_count += len(potholes_to_create)
                potholes_to_create = []
                
                if created_count % 500 == 0:
                    self.stdout.write(f"Created {created_count} records...")
        
        # Create remaining records
        if potholes_to_create:
            Pothole.objects.bulk_create(potholes_to_create)
            created_count += len(potholes_to_create)
        
        # Generate statistics
        total_count = Pothole.objects.count()
        status_stats = {}
        severity_stats = {}
        
        for status, _ in statuses:
            status_stats[status] = Pothole.objects.filter(status=status).count()
        
        for severity, _ in severities:
            severity_stats[severity] = Pothole.objects.filter(severity=severity).count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Successfully created {created_count} dummy pothole records!\n"
                f"📊 Database Statistics:\n"
                f"   Total Potholes: {total_count}\n"
                f"\n📈 Status Distribution:\n" +
                "\n".join([f"   {status.capitalize()}: {count}" for status, count in status_stats.items()]) +
                f"\n\n🚨 Severity Distribution:\n" +
                "\n".join([f"   {severity.capitalize()}: {count}" for severity, count in severity_stats.items()]) +
                f"\n\n🏗️ Contractors: {len(contractors)} different contractors assigned\n"
                f"🗓️ Date Range: {road_c_date.year} to {date.today().year}\n"
                f"🖼️ Frame Data: ~70% of records include frame images\n"
                f"📍 Coverage: Bhubaneswar and surrounding areas\n"
            )
        )
