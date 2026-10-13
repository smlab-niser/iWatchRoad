from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Pothole
from .serializers import (
    PotholeSerializer, 
    PotholeListSerializer, 
    PotholeCreateSerializer,
    PotholeUpdateSerializer,
    PotholeFrameSerializer
)


class PotholePagination(PageNumberPagination):
    """Custom pagination to limit memory usage."""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


class MapPinPagination(PageNumberPagination):
    """Ultra-lightweight pagination for the map pin endpoint."""
    page_size = 2000
    page_size_query_param = 'page_size'
    max_page_size = 5000


class PotholeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing pothole reports with full CRUD operations.
    
    Provides endpoints for:
    - List all potholes (GET /api/potholes/)
    - Create new pothole (POST /api/potholes/)
    - Retrieve specific pothole (GET /api/potholes/{id}/)
    - Update pothole (PUT/PATCH /api/potholes/{id}/)
    - Delete pothole (DELETE /api/potholes/{id}/)
    - Filter by status, severity, location (GET /api/potholes/?status=reported)
    - Search by area (GET /api/potholes/in_area/)
    """
    
    # Memory optimization: defer base64 field by default
    queryset = Pothole.objects.select_related()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'severity', 'num_potholes']
    search_fields = ['description']
    ordering_fields = ['timestamp', 'created_at', 'num_potholes', 'severity']
    ordering = ['-timestamp']
    # Temporarily disable pagination to fix frontend compatibility
    # pagination_class = PotholePagination
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return PotholeListSerializer
        elif self.action == 'create':
            return PotholeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PotholeUpdateSerializer
        elif self.action == 'frame_image':
            return PotholeFrameSerializer
        return PotholeSerializer
    
    def list(self, request, *args, **kwargs):
        """
        List potholes with optional filtering.
        
        Query parameters:
        - status: Filter by status (reported, verified, in_progress, fixed, closed)
        - severity: Filter by severity (low, medium, high, critical)
        - num_potholes: Filter by number of potholes
        - lat_min, lat_max, lng_min, lng_max: Bounding box filter
        - search: Search in description
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Bounding box filtering
        lat_min = request.query_params.get('lat_min')
        lat_max = request.query_params.get('lat_max')
        lng_min = request.query_params.get('lng_min')
        lng_max = request.query_params.get('lng_max')
        
        if all([lat_min, lat_max, lng_min, lng_max]):
            try:
                queryset = queryset.filter(
                    latitude__gte=float(lat_min),
                    latitude__lte=float(lat_max),
                    longitude__gte=float(lng_min),
                    longitude__lte=float(lng_max)
                )
            except ValueError:
                return Response(
                    {"error": "Invalid coordinate values"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def in_area(self, request):
        """
        Get potholes within a specific area (bounding box).
        
        Required query parameters:
        - lat_center: Center latitude
        - lng_center: Center longitude  
        - radius: Radius in kilometers (approximate)
        """
        try:
            lat_center = float(request.query_params.get('lat_center'))
            lng_center = float(request.query_params.get('lng_center'))
            radius = float(request.query_params.get('radius', 5))  # Default 5km
        except (TypeError, ValueError):
            return Response(
                {"error": "lat_center, lng_center, and radius parameters are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Simple bounding box approximation (not precise for large distances)
        lat_delta = radius / 111.0  # Approximate km per degree latitude
        lng_delta = radius / (111.0 * abs(lat_center))  # Adjust for longitude
        
        queryset = self.get_queryset().filter(
            latitude__gte=lat_center - lat_delta,
            latitude__lte=lat_center + lat_delta,
            longitude__gte=lng_center - lng_delta,
            longitude__lte=lng_center + lng_delta
        )
        
        serializer = PotholeListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def map_pins(self, request):
        """
        Ultra-lightweight endpoint for map rendering (mobile app).
        Returns only id, latitude, longitude, severity -- nothing else.
        Paginated at 2000 records per page to minimise round-trips.
        """
        queryset = self.get_queryset().only('id', 'latitude', 'longitude', 'severity')
        paginator = MapPinPagination()
        page = paginator.paginate_queryset(queryset, request)
        records = page if page is not None else queryset
        data = [
            {
                'id': p.id,
                'latitude': str(p.latitude),
                'longitude': str(p.longitude),
                'severity': p.severity,
            }
            for p in records
        ]
        if page is not None:
            return paginator.get_paginated_response(data)
        return Response(data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get statistics about potholes.
        """
        queryset = self.get_queryset()
        
        stats = {
            'total_reports': queryset.count(),
            'total_potholes': sum(p.num_potholes for p in queryset),
            'by_status': {},
            'by_severity': {},
        }
        
        # Count by status
        for status_choice, _ in Pothole.STATUS_CHOICES:
            count = queryset.filter(status=status_choice).count()
            stats['by_status'][status_choice] = count
        
        # Count by severity
        severity_choices = [choice[0] for choice in Pothole._meta.get_field('severity').choices]
        for severity_choice in severity_choices:
            count = queryset.filter(severity=severity_choice).count()
            stats['by_severity'][severity_choice] = count
        
        return Response(stats)
    
    @action(detail=True, methods=['get'])
    def frame_image(self, request, pk=None):
        """
        Get the frame image reference for a specific pothole.

        Returns a URL to the JPEG on disk. The image bytes are served by nginx
        from MEDIA_ROOT, never through Django and never inlined in JSON.
        """
        try:
            # Get only the required fields to minimize memory usage
            pothole = Pothole.objects.only('id', 'frame_number', 'frame_image').get(pk=pk)

            if not pothole.frame_image:
                return Response(
                    {'error': 'No frame image available for this pothole'},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response({
                'id': pothole.id,
                'frame_number': pothole.frame_number,
                'frame_image_url': request.build_absolute_uri(pothole.frame_image.url),
            })
        except Pothole.DoesNotExist:
            return Response(
                {'error': 'Pothole not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update only the status of a pothole report.
        
        Body: {"status": "verified"}
        """
        pothole = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Pothole.STATUS_CHOICES):
            return Response(
                {"error": f"Invalid status. Must be one of: {list(dict(Pothole.STATUS_CHOICES).keys())}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pothole.status = new_status
        pothole.save()
        
        serializer = self.get_serializer(pothole)
        return Response(serializer.data)
