from django.db import models
from django.utils import timezone


class Pothole(models.Model):
    """
    Model representing a pothole report with location, severity, and status information.
    """
    
    STATUS_CHOICES = [
        ('reported', 'Reported'),
        ('verified', 'Verified'),
        ('in_progress', 'In Progress'),
        ('fixed', 'Fixed'),
        ('closed', 'Closed'),
    ]
    
    # Location fields
    latitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7,
        help_text="Latitude coordinate of the pothole location"
    )
    longitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7,
        help_text="Longitude coordinate of the pothole location"
    )
    
    # Pothole details
    num_potholes = models.PositiveIntegerField(
        default=1,
        help_text="Number of potholes at this location"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='reported',
        help_text="Current status of the pothole report"
    )
    
    # Media
    image = models.ImageField(
        upload_to='pothole_images/',
        blank=True,
        null=True,
        help_text="Image of the pothole"
    )
    
    # Frame image file (preferred storage method)
    frame_image = models.ImageField(
        upload_to='pothole_frames/',
        blank=True,
        null=True,
        help_text="Frame image file"
    )
    
    # Base64 encoded image from CSV frames (deprecated, for backward compatibility)
    frame_image_base64 = models.TextField(
        blank=True,
        null=True,
        help_text="Base64 encoded image data from CSV frame (deprecated)"
    )
    
    # Frame number for reference
    frame_number = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Frame number from the original data collection"
    )
    
    # Timestamps
    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="When the pothole was reported"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional fields for better tracking
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Additional description of the pothole"
    )
    
    severity = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        default='medium',
        help_text="Severity level of the pothole"
    )
    
    # New fields for road completion date and contractor
    road_c_date = models.DateField(
        blank=True,
        null=True,
        help_text="Road completion date"
    )
    
    contractor = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Contractor responsible for the road"
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Pothole Report'
        verbose_name_plural = 'Pothole Reports'
    
    def __str__(self):
        return f"Pothole at ({self.latitude}, {self.longitude}) - {self.status}"
    
    @property
    def location_string(self):
        """Return a formatted string of the location coordinates."""
        return f"{self.latitude}, {self.longitude}"


# Road Health Models
class RoadHealth(models.Model):
    """Model to store road health analysis data"""
    
    HEALTH_STATUS_CHOICES = [
        ('critical', 'Critical'),  # >200 potholes, under warranty
        ('warning', 'Warning'),    # >200 potholes, not under warranty
        ('caution', 'Caution'),    # <200 potholes, under warranty
        ('good', 'Good'),          # <200 potholes, not under warranty
    ]
    
    # For segments without formal road segment data - use points directly
    points = models.JSONField(
        help_text="Array of [lat, lng] coordinates for the road segment"
    )
    
    pothole_count = models.PositiveIntegerField(default=0)
    is_under_warranty = models.BooleanField(default=False)
    health_status = models.CharField(
        max_length=20,
        choices=HEALTH_STATUS_CHOICES,
        default='good'
    )
    
    # Contractor information
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
        return f"Road Health - {self.health_status} ({self.pothole_count} potholes)"
    
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
