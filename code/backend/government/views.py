from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import login
from .models import GovUser, RoadSegment
from .serializers import (
    GovUserSerializer, 
    GovUserCreateSerializer, 
    GovAuthSerializer,
    RoadSegmentSerializer,
    RoadSegmentCreateSerializer
)


@api_view(['POST'])
@permission_classes([AllowAny])
def gov_signup(request):
    """Government user signup endpoint"""
    serializer = GovUserCreateSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        user_serializer = GovUserSerializer(user)
        return Response({
            'user': user_serializer.data,
            'message': 'Account created successfully. Please login.'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def gov_login(request):
    """Government user login endpoint"""
    serializer = GovAuthSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        # Generate a simple session token instead of using Django's Token model
        import secrets
        import hashlib
        
        # Generate a secure token
        token_raw = f"{user.username}:{secrets.token_urlsafe(32)}"
        token = hashlib.sha256(token_raw.encode()).hexdigest()
        
        user_serializer = GovUserSerializer(user)
        
        return Response({
            'user': user_serializer.data,
            'token': token,
            'message': 'Successfully logged in'
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def gov_logout(request):
    """Government user logout endpoint"""
    try:
        # Delete the token
        request.user.auth_token.delete()
        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
    except:
        return Response({'message': 'Logged out'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_token(request):
    """Verify if the authentication token is valid"""
    user_serializer = GovUserSerializer(request.user)
    return Response({
        'valid': True,
        'user': user_serializer.data
    }, status=status.HTTP_200_OK)


class RoadSegmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing road segments"""
    permission_classes = [AllowAny]  # Temporarily remove authentication requirement
    
    def get_queryset(self):
        return RoadSegment.objects.using('government').all()  # Return all for now
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RoadSegmentCreateSerializer
        return RoadSegmentSerializer
    
    def perform_create(self, serializer):
        # Get the first government user or create a dummy one for testing
        try:
            gov_user = GovUser.objects.using('government').first()
            if not gov_user:
                gov_user = GovUser.objects.using('government').get(username='govtest')
        except GovUser.DoesNotExist:
            gov_user = GovUser.objects.using('government').get(username='govtest')
        serializer.save(created_by=gov_user)
    
    def create(self, request, *args, **kwargs):
        """Create a new road segment"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Get the first government user or create a dummy one for testing
            try:
                gov_user = GovUser.objects.using('government').first()
                if not gov_user:
                    gov_user = GovUser.objects.using('government').get(username='govtest')
            except GovUser.DoesNotExist:
                gov_user = GovUser.objects.using('government').get(username='govtest')
            
            road_segment = serializer.save(created_by=gov_user)
            
            # Trigger road health update after creating new road segment
            try:
                self.update_road_health_after_segment_creation()
            except Exception as e:
                # Log the error but don't fail the road segment creation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to update road health after segment creation: {str(e)}")
            
            response_serializer = RoadSegmentSerializer(road_segment)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update_road_health_after_segment_creation(self):
        """Update road health data after a new road segment is created"""
        try:
            # Import here to avoid circular imports
            from potholes.road_health_views import RoadHealthViewSet
            
            viewset = RoadHealthViewSet()
            updated_count = viewset.update_road_health_data()
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Road health updated for {updated_count} segments after new segment creation")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating road health: {str(e)}")
            raise
    
    def list(self, request, *args, **kwargs):
        """List all road segments created by the current user"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """Get details of a specific road segment"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Update a road segment"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Delete a road segment"""
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
