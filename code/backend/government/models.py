from django.contrib.auth.models import AbstractUser
from django.db import models
import json


class GovUser(AbstractUser):
    """Government user model extending Django's AbstractUser"""
    full_name = models.CharField(max_length=200)
    department = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Fix reverse accessor conflicts with default User model
    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='gov_user_set',
        related_query_name='gov_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='gov_user_set',
        related_query_name='gov_user',
    )

    def __str__(self):
        return f"{self.username} ({self.full_name})"


class RoadSegment(models.Model):
    """Model for road segments created by government users"""
    points = models.JSONField(help_text="Array of [lat, lng] coordinates")
    contractor_id = models.CharField(max_length=100, default='', help_text="Unique contractor identification number")
    contractor_name = models.CharField(max_length=200)
    contractor_email = models.EmailField(default='', help_text="Contractor's email address")
    contractor_phone = models.CharField(max_length=20, default='', help_text="Contractor's phone number")
    road_creation_date = models.DateField()
    warranty_period = models.PositiveIntegerField(help_text="Warranty period in months")
    money_sanctioned = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Amount sanctioned for the project")
    created_by = models.ForeignKey(GovUser, on_delete=models.CASCADE, related_name='road_segments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Road Segment by {self.contractor_name} ({self.created_at.date()})"

    @property
    def points_list(self):
        """Return points as a list of [lat, lng] coordinates"""
        if isinstance(self.points, str):
            return json.loads(self.points)
        return self.points

    def save(self, *args, **kwargs):
        # Ensure points is properly formatted JSON
        if isinstance(self.points, list):
            # Validate that points are [lat, lng] pairs
            for point in self.points:
                if not isinstance(point, list) or len(point) != 2:
                    raise ValueError("Each point must be a [lat, lng] pair")
        super().save(*args, **kwargs)
