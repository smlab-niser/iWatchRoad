from rest_framework import serializers
from .models import Pothole


class PotholeSerializer(serializers.ModelSerializer):
    """
    Serializer for Pothole model with full CRUD operations.
    """
    location_string = serializers.ReadOnlyField()
    
    class Meta:
        model = Pothole
        fields = [
            'id',
            'latitude',
            'longitude',
            'location_string',
            'num_potholes',
            'status',
            'severity',
            'image',
            'frame_image_base64',
            'frame_number',
            'timestamp',
            'created_at',
            'updated_at',
            'description',
            'road_c_date',
            'contractor',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'location_string']


class PotholeListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing potholes (without heavy fields like description).
    """
    location_string = serializers.ReadOnlyField()
    
    class Meta:
        model = Pothole
        fields = [
            'id',
            'latitude',
            'longitude',
            'location_string',
            'num_potholes',
            'status',
            'severity',
            'timestamp',
            'image',
            'frame_image_base64',
            'frame_number',
            'road_c_date',
            'contractor',
        ]


class PotholeCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new pothole reports.
    """
    
    class Meta:
        model = Pothole
        fields = [
            'latitude',
            'longitude',
            'num_potholes',
            'status',
            'severity',
            'description',
            'image',
            'road_c_date',
            'contractor',
        ]
    
    def validate_latitude(self, value):
        """Validate latitude is within valid range."""
        if not -90 <= value <= 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90 degrees.")
        return value
    
    def validate_longitude(self, value):
        """Validate longitude is within valid range."""
        if not -180 <= value <= 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180 degrees.")
        return value
    
    def validate_num_potholes(self, value):
        """Validate number of potholes is reasonable."""
        if value < 1:
            raise serializers.ValidationError("Number of potholes must be at least 1.")
        if value > 100:
            raise serializers.ValidationError("Number of potholes seems unreasonably high. Please verify.")
        return value


class PotholeUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating pothole reports (excludes location changes).
    """
    
    class Meta:
        model = Pothole
        fields = [
            'num_potholes',
            'status',
            'severity',
            'description',
            'image',
            'road_c_date',
            'contractor',
        ]
    
    def validate_num_potholes(self, value):
        """Validate number of potholes is reasonable."""
        if value < 1:
            raise serializers.ValidationError("Number of potholes must be at least 1.")
        if value > 100:
            raise serializers.ValidationError("Number of potholes seems unreasonably high. Please verify.")
        return value
