from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Count, Q
from django.core.mail import send_mail
from django.conf import settings
import logging

# Twilio imports for SMS
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logging.warning("Twilio not installed. SMS functionality will be disabled.")

from .models import RoadHealth, ContractorMessage, MessageSchedule, Pothole
from .road_health_serializers import (
    RoadHealthSerializer, 
    ContractorMessageSerializer,
    ContractorMessageCreateSerializer,
    MessageScheduleSerializer
)
from government.models import RoadSegment

logger = logging.getLogger(__name__)


def send_notification_message(message_obj):
    """
    Send notification via both email and SMS
    Returns a dict with success status for each method
    """
    results = {
        'email': {'success': False, 'error': None},
        'sms': {'success': False, 'error': None}
    }
    
    # Send Email
    if message_obj.contractor_email:
        try:
            # Get location description from road health data
            road_location = f"Road Segment ID: {message_obj.road_health.id}"
            if message_obj.road_health.points:
                # Get first and last coordinates for reference
                first_point = message_obj.road_health.points[0] if message_obj.road_health.points else None
                if first_point:
                    road_location = f"Road Segment (Lat: {first_point[0]:.6f}, Lng: {first_point[1]:.6f})"
            
            send_mail(
                subject='Road Maintenance Message - RoadWatch',
                message=f"""
Road Maintenance Alert

Location: {road_location}
Status: {message_obj.road_health.get_health_status_display()}
Pothole Count: {message_obj.road_health.pothole_count}
Under Warranty: {'Yes' if message_obj.road_health.is_under_warranty else 'No'}

Message: {message_obj.message}

Please take appropriate action as soon as possible.

Best regards,
RoadWatch Team
                """.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[message_obj.contractor_email],
                fail_silently=False,
            )
            results['email']['success'] = True
        except Exception as e:
            error_msg = f"Failed to send email to {message_obj.contractor_email}: {str(e)}"
            logger.error(error_msg)
            results['email']['error'] = str(e)
    
    # Send SMS
    if message_obj.contractor_phone and TWILIO_AVAILABLE:
        try:
            if all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                
                # Format phone number (ensure it starts with +)
                phone = message_obj.contractor_phone
                if not phone.startswith('+'):
                    phone = '+91' + phone.lstrip('+').lstrip('0')  # Assuming Indian numbers, adjust as needed
                
                # Shorter message for SMS
                sms_message = f"RoadWatch Alert: Road Segment ID {message_obj.road_health.id} needs attention. {message_obj.road_health.pothole_count} potholes. Check email for details."
                
                client.messages.create(
                    body=sms_message,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=phone
                )
                results['sms']['success'] = True
            else:
                results['sms']['error'] = "Twilio credentials not configured"
        except Exception as e:
            error_msg = f"Failed to send SMS to {message_obj.contractor_phone}: {str(e)}"
            logger.error(error_msg)
            results['sms']['error'] = str(e)
    elif message_obj.contractor_phone and not TWILIO_AVAILABLE:
        results['sms']['error'] = "Twilio library not available"
    
    return results


class RoadHealthViewSet(viewsets.ModelViewSet):
    """ViewSet for Road Health data"""
    
    queryset = RoadHealth.objects.all()
    serializer_class = RoadHealthSerializer
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get road health analytics"""
        queryset = self.get_queryset()
        
        analytics = {
            'total_segments': queryset.count(),
            'by_status': {},
            'critical_segments': queryset.filter(health_status='critical').count(),
            'segments_needing_attention': queryset.filter(
                health_status__in=['critical', 'warning']
            ).count()
        }
        
        # Count by health status
        for status_choice, _ in RoadHealth.HEALTH_STATUS_CHOICES:
            count = queryset.filter(health_status=status_choice).count()
            analytics['by_status'][status_choice] = count
        
        return Response(analytics)
    
    @action(detail=False, methods=['post'])
    def update_all(self, request):
        """Update road health data for all segments"""
        try:
            updated_count = self.update_road_health_data()
            return Response({
                'message': f'Updated {updated_count} road health segments',
                'updated_count': updated_count
            })
        except Exception as e:
            logger.error(f"Error updating road health data: {str(e)}")
            return Response(
                {'error': 'Failed to update road health data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def refresh_from_segments(self, request):
        """Refresh road health data from current road segments"""
        try:
            # Clear existing data and rebuild from road segments
            updated_count = self.update_road_health_data()
            
            # Get updated statistics
            analytics = self.get_analytics_data()
            
            return Response({
                'message': f'Refreshed road health data for {updated_count} segments',
                'updated_count': updated_count,
                'analytics': analytics
            })
        except Exception as e:
            logger.error(f"Error refreshing road health data: {str(e)}")
            return Response(
                {'error': 'Failed to refresh road health data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_analytics_data(self):
        """Get current road health analytics"""
        queryset = self.get_queryset()
        
        analytics = {
            'total_segments': queryset.count(),
            'by_status': {},
            'critical_segments': queryset.filter(health_status='critical').count(),
            'segments_needing_attention': queryset.filter(
                health_status__in=['critical', 'warning']
            ).count()
        }
        
        # Count by health status
        for status_choice, _ in RoadHealth.HEALTH_STATUS_CHOICES:
            count = queryset.filter(health_status=status_choice).count()
            analytics['by_status'][status_choice] = count
        
        return analytics
    
    def update_road_health_data(self):
        """Update road health data based on current pothole data and existing road segments"""
        updated_count = 0
        
        # Clear existing road health data to rebuild from scratch
        RoadHealth.objects.all().delete()
        
        # Get all road segments from government app
        road_segments = RoadSegment.objects.all()
        
        if not road_segments.exists():
            logger.warning("No road segments found. Please create road segments through Government Authorization first.")
            return 0
        
        for segment in road_segments:
            # Skip segments without valid points data
            if not segment.points or len(segment.points) < 2:
                logger.warning(f"Skipping segment {segment.id} - invalid points data")
                continue
                
            try:
                # Extract coordinates from segment points
                lats = [float(point[0]) for point in segment.points if len(point) >= 2]
                lngs = [float(point[1]) for point in segment.points if len(point) >= 2]
                
                if not lats or not lngs:
                    logger.warning(f"Skipping segment {segment.id} - no valid coordinates")
                    continue
                    
                min_lat, max_lat = min(lats), max(lats)
                min_lng, max_lng = min(lngs), max(lngs)
                
                # Add buffer around the segment for pothole detection (approximately 100m)
                buffer = 0.001  # roughly 100 meters
                
                # Count total potholes within this road segment area
                potholes_in_area = Pothole.objects.filter(
                    latitude__gte=min_lat - buffer,
                    latitude__lte=max_lat + buffer,
                    longitude__gte=min_lng - buffer,
                    longitude__lte=max_lng + buffer
                )
                
                # Sum up all potholes in the area
                pothole_count = sum(pothole.num_potholes for pothole in potholes_in_area)
                
                # Check if under warranty based on road creation date and warranty period
                is_under_warranty = False
                if segment.road_creation_date and segment.warranty_period:
                    warranty_end_date = segment.road_creation_date + timedelta(days=segment.warranty_period * 30)
                    is_under_warranty = timezone.now().date() <= warranty_end_date
                
                # Determine health status based on business rules
                if pothole_count >= 200:
                    health_status = 'critical' if is_under_warranty else 'warning'
                else:
                    health_status = 'caution' if is_under_warranty else 'good'
                
                # Create road health record
                road_health = RoadHealth.objects.create(
                    points=segment.points,
                    pothole_count=pothole_count,
                    is_under_warranty=is_under_warranty,
                    health_status=health_status,
                    contractor_id=segment.contractor_id,
                    contractor_name=segment.contractor_name,
                    contractor_email=segment.contractor_email,
                    contractor_phone=segment.contractor_phone,
                )
                
                updated_count += 1
                
                # Schedule automatic messages if needed
                if road_health.should_trigger_alert():
                    self.schedule_auto_messages(road_health)
                    
                logger.info(f"Updated road health for segment {segment.id}: {health_status} ({pothole_count} potholes)")
                
            except Exception as e:
                logger.error(f"Error processing segment {segment.id}: {str(e)}")
                continue
        
        logger.info(f"Successfully updated road health data for {updated_count} segments")
        return updated_count
    
    def schedule_auto_messages(self, road_health):
        """Schedule automatic messages for critical/warning road segments"""
        schedule, created = MessageSchedule.objects.get_or_create(
            road_health=road_health,
            defaults={
                'next_auto_message_due': timezone.now() + timedelta(days=5),
                'auto_message_enabled': True,
                'message_frequency_days': 5
            }
        )
        
        # Check if it's time to send an auto message
        if (schedule.next_auto_message_due and 
            schedule.next_auto_message_due <= timezone.now() and
            schedule.auto_message_enabled):
            
            self.send_auto_message(road_health, schedule)
    
    def send_auto_message(self, road_health, schedule):
        """Send automatic message to contractor"""
        message_text = "Repair the road, it is very hectic to travel"
        
        try:
            # Create message record
            message = ContractorMessage.objects.create(
                road_health=road_health,
                contractor_email=road_health.contractor_email,
                contractor_phone=road_health.contractor_phone,
                message=message_text,
                message_type='auto',
                status='pending'
            )
            
            # Send notifications using the new function
            results = send_notification_message(message)
            
            # Update message status based on results
            if results['email']['success'] or results['sms']['success']:
                message.status = 'sent'
                message.sent_at = timezone.now()
            else:
                message.status = 'failed'
            
            message.save()
            
            # Update schedule
            schedule.last_auto_message_sent = timezone.now()
            schedule.next_auto_message_due = timezone.now() + timedelta(days=schedule.message_frequency_days)
            schedule.save()
            
            logger.info(f"Auto message sent to {road_health.contractor_email} - Email: {results['email']['success']}, SMS: {results['sms']['success']}")
            
        except Exception as e:
            logger.error(f"Error sending auto message: {str(e)}")


class ContractorMessageViewSet(viewsets.ModelViewSet):
    """ViewSet for Contractor Messages"""
    
    queryset = ContractorMessage.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ContractorMessageCreateSerializer
        return ContractorMessageSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        segment_id = self.request.query_params.get('segment_id')
        if segment_id:
            queryset = queryset.filter(road_health_id=segment_id)
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create and send a manual message to contractor"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = serializer.save()
        
        # Send notifications using the new function
        results = send_notification_message(message)
        
        # Update message status based on results
        if results['email']['success'] or results['sms']['success']:
            message.status = 'sent'
            message.sent_at = timezone.now()
        else:
            message.status = 'failed'
        
        message.save()
        
        # Include notification results in response
        response_data = ContractorMessageSerializer(message).data
        response_data['notification_results'] = results
        
        return Response(
            response_data,
            status=status.HTTP_201_CREATED
        )


@api_view(['POST'])
def update_road_health_after_upload(request):
    """API endpoint to update road health after new data upload"""
    try:
        viewset = RoadHealthViewSet()
        updated_count = viewset.update_road_health_data()
        
        return Response({
            'message': f'Road health updated for {updated_count} segments',
            'updated_count': updated_count
        })
    except Exception as e:
        logger.error(f"Error updating road health after upload: {str(e)}")
        return Response(
            {'error': 'Failed to update road health data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
