from rest_framework import serializers
from .models import RoadHealth, ContractorMessage, MessageSchedule


class RoadHealthSerializer(serializers.ModelSerializer):
    """Serializer for Road Health data"""
    
    contractor_info = serializers.SerializerMethodField()
    
    class Meta:
        model = RoadHealth
        fields = [
            'id',
            'points',
            'pothole_count',
            'is_under_warranty',
            'health_status',
            'contractor_info',
            'last_updated',
            'created_at'
        ]
        read_only_fields = ['id', 'last_updated', 'created_at']
    
    def get_contractor_info(self, obj):
        """Return contractor information if available"""
        if obj.contractor_name:
            return {
                'contractor_id': obj.contractor_id,
                'contractor_name': obj.contractor_name,
                'contractor_email': obj.contractor_email,
                'contractor_phone': obj.contractor_phone,
            }
        return None


class ContractorMessageSerializer(serializers.ModelSerializer):
    """Serializer for Contractor Messages"""
    
    class Meta:
        model = ContractorMessage
        fields = [
            'id',
            'road_health',
            'contractor_email',
            'contractor_phone',
            'message',
            'message_type',
            'status',
            'sent_at',
            'created_at'
        ]
        read_only_fields = ['id', 'sent_at', 'created_at']


class ContractorMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating contractor messages"""
    
    segment_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ContractorMessage
        fields = [
            'segment_id',
            'message',
            'message_type'
        ]
    
    def create(self, validated_data):
        segment_id = validated_data.pop('segment_id')
        try:
            road_health = RoadHealth.objects.get(id=segment_id)
            
            # Get contractor info from road health
            validated_data['road_health'] = road_health
            validated_data['contractor_email'] = road_health.contractor_email
            validated_data['contractor_phone'] = road_health.contractor_phone
            
            return super().create(validated_data)
        except RoadHealth.DoesNotExist:
            raise serializers.ValidationError("Road health segment not found")


class MessageScheduleSerializer(serializers.ModelSerializer):
    """Serializer for Message Schedule"""
    
    class Meta:
        model = MessageSchedule
        fields = [
            'id',
            'road_health',
            'last_auto_message_sent',
            'next_auto_message_due',
            'auto_message_enabled',
            'message_frequency_days',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
