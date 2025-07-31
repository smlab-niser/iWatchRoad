import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from potholes.models import Pothole


class Command(BaseCommand):
    help = 'Populate database with sample pothole data for Bhubaneswar'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=15,
            help='Number of pothole records to create (default: 15)'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Bhubaneswar bounding box (approximate)
        # Center: 20.2961, 85.8245
        lat_min, lat_max = 20.2000, 20.4000
        lng_min, lng_max = 85.7000, 85.9000
        
        # Sample locations with realistic street names/areas in Bhubaneswar
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
        ]
        
        statuses = ['reported', 'verified', 'in_progress', 'fixed', 'closed']
        severities = ['low', 'medium', 'high', 'critical']
        
        descriptions = [
            "Large pothole causing traffic disruption",
            "Multiple small potholes in cluster",
            "Deep pothole near bus stop", 
            "Water-filled pothole after rain",
            "Pothole at road intersection",
            "Road surface deterioration",
            "Damaged asphalt creating hazard",
            "Pothole near market area",
            "Road cavity after utility work",
            "Weather-damaged road surface",
            "Heavy vehicle damage to road",
            "Pothole affecting two-wheeler traffic",
            "Road patch failure creating hole",
            "Drainage issue causing road damage",
            "Construction-related road damage"
        ]

        # Clear existing data
        Pothole.objects.all().delete()
        self.stdout.write(self.style.WARNING('Cleared existing pothole data'))

        created_potholes = []
        
        for i in range(count):
            # Use predefined locations first, then generate random ones
            if i < len(locations):
                location = locations[i]
                lat = location["lat"] + random.uniform(-0.005, 0.005)  # Add small variation
                lng = location["lng"] + random.uniform(-0.005, 0.005)
                area = location["area"]
            else:
                lat = random.uniform(lat_min, lat_max)
                lng = random.uniform(lng_min, lng_max)
                area = f"Area {i+1}"
            
            # Generate realistic timestamp (within last 30 days)
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            timestamp = timezone.now() - timedelta(days=days_ago, hours=hours_ago)
            
            # Weight status distribution (more recent reports, fewer fixed)
            status_weights = [0.3, 0.25, 0.2, 0.15, 0.1]  # reported, verified, in_progress, fixed, closed
            status = random.choices(statuses, weights=status_weights)[0]
            
            # Weight severity distribution (more medium/low, fewer critical)
            severity_weights = [0.4, 0.4, 0.15, 0.05]  # low, medium, high, critical
            severity = random.choices(severities, weights=severity_weights)[0]
            
            num_potholes = random.choices(
                [1, 2, 3, 4, 5], 
                weights=[0.5, 0.25, 0.15, 0.07, 0.03]
            )[0]
            
            description = f"{random.choice(descriptions)} in {area}"
            
            pothole = Pothole.objects.create(
                latitude=round(lat, 6),
                longitude=round(lng, 6),
                num_potholes=num_potholes,
                status=status,
                severity=severity,
                timestamp=timestamp,
                description=description,
                # Note: image field left empty, will use dummy URL in API response
            )
            
            created_potholes.append(pothole)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {count} pothole records for Bhubaneswar'
            )
        )
        
        # Print summary statistics
        for status in statuses:
            count_status = len([p for p in created_potholes if p.status == status])
            self.stdout.write(f'  {status.replace("_", " ").title()}: {count_status}')
        
        total_potholes = sum(p.num_potholes for p in created_potholes)
        self.stdout.write(f'Total potholes reported: {total_potholes}')
