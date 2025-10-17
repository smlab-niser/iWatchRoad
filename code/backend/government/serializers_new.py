from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import GovUser, RoadSegment


class GovUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GovUser
        fields = ('id', 'username', 'email', 'full_name', 'department', 'created_at')
        read_only_fields = ('id', 'created_at')


class GovUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = GovUser
        fields = ('username', 'email', 'password', 'full_name', 'department')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = GovUser.objects.db_manager('government').create_user(**validated_data)
        user.set_password(password)
        user.save(using='government')
        return user


class GovAuthSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            # Since we're using a separate database, we need to manually authenticate
            try:
                user = GovUser.objects.using('government').get(username=username)
                if user.check_password(password):
                    if not user.is_active:
                        raise serializers.ValidationError('User account is disabled')
                    attrs['user'] = user
                    return attrs
                else:
                    raise serializers.ValidationError('Invalid credentials')
            except GovUser.DoesNotExist:
                raise serializers.ValidationError('Invalid credentials')
        else:
            raise serializers.ValidationError('Must include username and password')


class RoadSegmentSerializer(serializers.ModelSerializer):
    created_by = GovUserSerializer(read_only=True)

    class Meta:
        model = RoadSegment
        fields = [
            'id', 'points', 'contractor_name', 'road_creation_date', 
            'warranty_period', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')


class RoadSegmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoadSegment
        fields = ['points', 'contractor_name', 'road_creation_date', 'warranty_period']

    def validate_points(self, value):
        """Validate that points is a list of [lat, lng] coordinates"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Points must be a list of coordinates")
        
        if len(value) < 2:
            raise serializers.ValidationError("Road segment must have at least 2 points")
        
        for i, point in enumerate(value):
            if not isinstance(point, list) or len(point) != 2:
                raise serializers.ValidationError(f"Point {i+1} must be a [lat, lng] pair")
            
            try:
                lat, lng = float(point[0]), float(point[1])
                if not (-90 <= lat <= 90):
                    raise serializers.ValidationError(f"Invalid latitude in point {i+1}: {lat}")
                if not (-180 <= lng <= 180):
                    raise serializers.ValidationError(f"Invalid longitude in point {i+1}: {lng}")
            except (ValueError, TypeError):
                raise serializers.ValidationError(f"Point {i+1} coordinates must be numbers")
        
        return value

    def validate_warranty_period(self, value):
        """Validate warranty period is reasonable"""
        if value < 1:
            raise serializers.ValidationError("Warranty period must be at least 1 month")
        if value > 120:  # 10 years max
            raise serializers.ValidationError("Warranty period cannot exceed 120 months")
        return value

    def create(self, validated_data):
        """Create road segment with proper database routing"""
        road_segment = RoadSegment(**validated_data)
        road_segment.save(using='government')
        return road_segment
