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
    
    # Base64 encoded image from CSV frames
    frame_image_base64 = models.TextField(
        blank=True,
        null=True,
        help_text="Base64 encoded image data from CSV frame"
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
