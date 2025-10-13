from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
import random
from decimal import Decimal

from potholes.models import RoadHealth, Pothole
from government.models import RoadSegment


class Command(BaseCommand):
    help = 'Generate sample road health data based on existing road segments and potholes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--segments',
            type=int,
            default=20,
            help='Number of road health segments to create'
        )

    def handle(self, *args, **options):
        segments_count = options['segments']
        
        self.stdout.write(f"🏥 Creating {segments_count} road health segments...")
        
        # Sample road segments around Bhubaneswar
        sample_segments = [
            {
                'points': [[20.2961, 85.8245], [20.2971, 85.8255], [20.2981, 85.8265]],
                'name': 'Kalinga Stadium Road',
                'contractor': 'ABC Construction Ltd.',
                'contractor_email': 'abc@construction.com',
                'contractor_phone': '+91-9876543210'
            },
            {
                'points': [[20.3012, 85.8302], [20.3022, 85.8312], [20.3032, 85.8322]],
                'name': 'KIIT Road',
                'contractor': 'XYZ Infrastructure',
                'contractor_email': 'xyz@infrastructure.com',
                'contractor_phone': '+91-9876543211'
            },
            {
                'points': [[20.2850, 85.8180], [20.2860, 85.8190], [20.2870, 85.8200]],
                'name': 'Patia Ring Road',
                'contractor': 'PQR Builders',
                'contractor_email': 'pqr@builders.com',
                'contractor_phone': '+91-9876543212'
            },
            {
                'points': [[20.2750, 85.8080], [20.2760, 85.8090], [20.2770, 85.8100]],
                'name': 'Nayapalli Road',
                'contractor': 'LMN Construction',
                'contractor_email': 'lmn@construction.com',
                'contractor_phone': '+91-9876543213'
            },
            {
                'points': [[20.3150, 85.8350], [20.3160, 85.8360], [20.3170, 85.8370]],
                'name': 'Chandrasekharpur Road',
                'contractor': 'DEF Roadworks',
                'contractor_email': 'def@roadworks.com',
                'contractor_phone': '+91-9876543214'
            },
        ]
        
        # Extended sample segments
        extended_segments = []
        base_lat = 20.2961
        base_lng = 85.8245
        
        for i in range(segments_count):
            if i < len(sample_segments):
                segment = sample_segments[i].copy()
            else:
                # Generate new segments around Bhubaneswar
                lat_offset = random.uniform(-0.05, 0.05)
                lng_offset = random.uniform(-0.05, 0.05)
                
                start_lat = base_lat + lat_offset
                start_lng = base_lng + lng_offset
                
                points = []
                for j in range(3):
                    points.append([
                        start_lat + (j * 0.001),
                        start_lng + (j * 0.001)
                    ])
                
                contractors = [
                    'Alpha Construction Ltd.',
                    'Beta Infrastructure Pvt.',
                    'Gamma Roadworks Inc.',
                    'Delta Builders Co.',
                    'Epsilon Engineering',
                    'Zeta Construction',
                    'Eta Infrastructure',
                    'Theta Builders',
                    'Iota Roadworks',
                    'Kappa Construction'
                ]
                
                contractor_name = random.choice(contractors)
                contractor_id = f"CONT{1000 + i}"
                
                segment = {
                    'points': points,
                    'name': f'Road Segment {i + 1}',
                    'contractor': contractor_name,
                    'contractor_email': f"{contractor_name.lower().replace(' ', '').replace('.', '')}@email.com",
                    'contractor_phone': f"+91-98765432{10 + (i % 90)}"
                }
            
            extended_segments.append(segment)
        
        created_count = 0
        
        for i, segment_data in enumerate(extended_segments):
            # Count potholes in this area (simplified: within bounding box)
            points = segment_data['points']
            if not points:
                continue
                
            lats = [point[0] for point in points]
            lngs = [point[1] for point in points]
            
            min_lat, max_lat = min(lats), max(lats)
            min_lng, max_lng = min(lngs), max(lngs)
            
            # Add buffer around the segment
            buffer = 0.005  # roughly 500 meters
            
            pothole_count = Pothole.objects.filter(
                latitude__gte=Decimal(str(min_lat - buffer)),
                latitude__lte=Decimal(str(max_lat + buffer)),
                longitude__gte=Decimal(str(min_lng - buffer)),
                longitude__lte=Decimal(str(max_lng + buffer))
            ).count()
            
            # If no potholes found, generate realistic count
            if pothole_count == 0:
                # Generate realistic pothole counts
                weights = [0.4, 0.3, 0.2, 0.1]  # More likely to have fewer potholes
                pothole_ranges = [
                    random.randint(5, 50),    # Low
                    random.randint(51, 150),  # Medium
                    random.randint(151, 250), # High
                    random.randint(251, 400)  # Critical
                ]
                pothole_count = random.choices(pothole_ranges, weights=weights)[0]
            
            # Random warranty status (70% chance of being under warranty for newer roads)
            is_under_warranty = random.random() < 0.7
            
            # Determine health status
            if pothole_count >= 200:
                health_status = 'critical' if is_under_warranty else 'warning'
            else:
                health_status = 'caution' if is_under_warranty else 'good'
            
            # Create road health record
            road_health = RoadHealth.objects.create(
                points=points,
                pothole_count=pothole_count,
                is_under_warranty=is_under_warranty,
                health_status=health_status,
                contractor_id=f"CONT{1000 + i}",
                contractor_name=segment_data['contractor'],
                contractor_email=segment_data['contractor_email'],
                contractor_phone=segment_data['contractor_phone']
            )
            
            created_count += 1
            
            if (created_count % 5) == 0:
                self.stdout.write(f"  Created {created_count} road health segments...")
        
        # Statistics
        total_segments = RoadHealth.objects.count()
        status_stats = {}
        for status_choice, _ in RoadHealth.HEALTH_STATUS_CHOICES:
            count = RoadHealth.objects.filter(health_status=status_choice).count()
            status_stats[status_choice] = count
        
        critical_segments = RoadHealth.objects.filter(health_status='critical').count()
        warning_segments = RoadHealth.objects.filter(health_status='warning').count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Successfully created {created_count} road health segments!\n" +
                f"\n📊 Statistics:\n" +
                f"   Total segments: {total_segments}\n" +
                f"   Critical (Red): {status_stats.get('critical', 0)}\n" +
                f"   Warning (Orange): {status_stats.get('warning', 0)}\n" +
                f"   Caution (Yellow): {status_stats.get('caution', 0)}\n" +
                f"   Good (Green): {status_stats.get('good', 0)}\n" +
                f"\n🚨 Segments needing immediate attention: {critical_segments + warning_segments}\n" +
                f"🏗️ Contractors: {len(set([rh.contractor_name for rh in RoadHealth.objects.all()]))}\n" +
                f"📍 Coverage: Bhubaneswar area\n"
            )
        )
