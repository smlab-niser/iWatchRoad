from django.db import models
from government.models import RoadSegment
import json


class RoadHealth(models.Model):
    """Model to store road health analysis data"""
    
    HEALTH_STATUS_CHOICES = [
        ('critical', 'Critical'),  # >200 potholes, under warranty
        ('warning', 'Warning'),    # >200 potholes, not under warranty
        ('caution', 'Caution'),    # <200 potholes, under warranty
        ('good', 'Good'),          # <200 potholes, not under warranty
    ]
    
    segment = models.OneToOneField(
        RoadSegment,
        on_delete=models.CASCADE,
        related_name='health_data',
        null=True,
        blank=True
    )
    
    # For segments without formal road segment data
    points = models.JSONField(
        help_text="Array of [lat, lng] coordinates for the road segment",
        null=True,
        blank=True
    )
    
    pothole_count = models.PositiveIntegerField(default=0)
    is_under_warranty = models.BooleanField(default=False)
    health_status = models.CharField(
        max_length=20,
        choices=HEALTH_STATUS_CHOICES,
        default='good'
    )
    
    # Contractor information (may come from segment or separate source)
    contractor_id = models.CharField(max_length=100, blank=True, null=True)
    contractor_name = models.CharField(max_length=200, blank=True, null=True)
    contractor_email = models.EmailField(blank=True, null=True)
    contractor_phone = models.CharField(max_length=20, blank=True, null=True)
    
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-last_updated']
        verbose_name = 'Road Health Data'
        verbose_name_plural = 'Road Health Data'
    
    def __str__(self):
        segment_info = f"Segment {self.segment.id}" if self.segment else "Custom Area"
        return f"{segment_info} - {self.health_status} ({self.pothole_count} potholes)"
    
    def update_health_status(self):
        """Update health status based on pothole count and warranty status"""
        if self.pothole_count >= 200:
            self.health_status = 'critical' if self.is_under_warranty else 'warning'
        else:
            self.health_status = 'caution' if self.is_under_warranty else 'good'
        self.save()
    
    def should_trigger_alert(self):
        """Check if this road health status should trigger contractor alerts"""
        return self.health_status in ['critical', 'warning']


class ContractorMessage(models.Model):
    """Model to track messages sent to contractors"""
    
    MESSAGE_TYPE_CHOICES = [
        ('auto', 'Automatic'),
        ('manual', 'Manual'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    road_health = models.ForeignKey(
        RoadHealth,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    
    contractor_email = models.EmailField()
    contractor_phone = models.CharField(max_length=20)
    message = models.TextField()
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPE_CHOICES,
        default='manual'
    )
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # For tracking automatic message frequency
    last_auto_message = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contractor Message'
        verbose_name_plural = 'Contractor Messages'
    
    def __str__(self):
        return f"{self.message_type.title()} message to {self.contractor_email} - {self.status}"


class MessageSchedule(models.Model):
    """Model to track automatic message scheduling"""
    
    road_health = models.OneToOneField(
        RoadHealth,
        on_delete=models.CASCADE,
        related_name='message_schedule'
    )
    
    last_auto_message_sent = models.DateTimeField(null=True, blank=True)
    next_auto_message_due = models.DateTimeField(null=True, blank=True)
    auto_message_enabled = models.BooleanField(default=True)
    message_frequency_days = models.PositiveIntegerField(default=5)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Message Schedule'
        verbose_name_plural = 'Message Schedules'
    
    def __str__(self):
        return f"Schedule for {self.road_health} - Next: {self.next_auto_message_due}"
