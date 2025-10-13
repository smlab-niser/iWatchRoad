from django.contrib import admin
from .models import GovUser, RoadSegment


@admin.register(GovUser)
class GovUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'email', 'department', 'is_active', 'created_at')
    list_filter = ('department', 'is_active', 'created_at')
    search_fields = ('username', 'full_name', 'email', 'department')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(RoadSegment)
class RoadSegmentAdmin(admin.ModelAdmin):
    list_display = ('contractor_name', 'road_creation_date', 'warranty_period', 'created_by', 'created_at')
    list_filter = ('road_creation_date', 'warranty_period', 'created_at')
    search_fields = ('contractor_name', 'created_by__username')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('created_by',)
