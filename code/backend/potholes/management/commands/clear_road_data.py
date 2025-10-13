from django.core.management.base import BaseCommand
from django.db import transaction
from potholes.models import RoadHealth, ContractorMessage, MessageSchedule
from government.models import RoadSegment, GovUser


class Command(BaseCommand):
    help = 'Clear all road segment and contractor information data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all road and contractor data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This will delete ALL road segments, road health data, and contractor messages.\n'
                    'To confirm, run: python manage.py clear_road_data --confirm'
                )
            )
            return

        self.stdout.write('Starting data cleanup...')

        with transaction.atomic():
            # Clear primary database data
            self.stdout.write('Clearing contractor messages...')
            contractor_messages_count = ContractorMessage.objects.count()
            ContractorMessage.objects.all().delete()
            self.stdout.write(f'Deleted {contractor_messages_count} contractor messages')

            self.stdout.write('Clearing message schedules...')
            message_schedules_count = MessageSchedule.objects.count()
            MessageSchedule.objects.all().delete()
            self.stdout.write(f'Deleted {message_schedules_count} message schedules')

            self.stdout.write('Clearing road health data...')
            road_health_count = RoadHealth.objects.count()
            RoadHealth.objects.all().delete()
            self.stdout.write(f'Deleted {road_health_count} road health records')

        # Clear government database data (separate transaction for different database)
        with transaction.atomic(using='government'):
            self.stdout.write('Clearing road segments from government database...')
            road_segments_count = RoadSegment.objects.using('government').count()
            RoadSegment.objects.using('government').all().delete()
            self.stdout.write(f'Deleted {road_segments_count} road segments')

            # Optionally clear government users (uncomment if needed)
            # self.stdout.write('Clearing government users...')
            # gov_users_count = GovUser.objects.using('government').count()
            # GovUser.objects.using('government').all().delete()
            # self.stdout.write(f'Deleted {gov_users_count} government users')

        self.stdout.write(
            self.style.SUCCESS(
                '\nData cleanup completed successfully!\n'
                'All road segments, road health data, contractor messages, and schedules have been removed.\n'
                'You can now enter fresh data through the government authorization interface.'
            )
        )
