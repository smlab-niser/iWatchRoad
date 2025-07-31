from django.contrib import admin
from .models import Pothole


@admin.register(Pothole)
class PotholeAdmin(admin.ModelAdmin):
    """
    Admin interface for Pothole model.
    """
    list_display = [
        'id',
        'location_string',
        'num_potholes',
        'status',
        'severity',
        'timestamp',
        'created_at',
    ]
    
    list_filter = [
        'status',
        'severity',
        'timestamp',
        'created_at',
    ]
    
    search_fields = [
        'description',
        'latitude',
        'longitude',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'location_string',
    ]
    
    fieldsets = (
        ('Location', {
            'fields': ('latitude', 'longitude', 'location_string')
        }),
        ('Pothole Details', {
            'fields': ('num_potholes', 'status', 'severity', 'description')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Timestamps', {
            'fields': ('timestamp', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
