from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .home_views import home_view
from . import upload_views
from .road_health_views import RoadHealthViewSet, ContractorMessageViewSet, update_road_health_after_upload
from .report_view import report_pothole
from .evidence_views import upload_evidence

router = DefaultRouter()
router.register(r'potholes', views.PotholeViewSet)
router.register(r'road-health', RoadHealthViewSet)
router.register(r'contractor-messages', ContractorMessageViewSet)

urlpatterns = [
    path('', home_view, name='home'),
    # NOTE: must precede the router. DefaultRouter's detail route is
    # `potholes/(?P<pk>[^/.]+)/`, which would otherwise swallow
    # `potholes/report/` as a lookup for pk="report".
    path('api/potholes/report/', report_pothole, name='pothole_report'),
    path('api/potholes/evidence/', upload_evidence, name='pothole_evidence'),
    path('api/', include(router.urls)),
    path('api/upload-videos/', upload_views.upload_videos, name='upload_videos'),
    path('api/upload-gps/', upload_views.upload_gps, name='upload_gps'),
    path('api/process-video/', upload_views.process_video, name='process_video'),
    path('api/cleanup-uploads/', upload_views.cleanup_uploads, name='cleanup_uploads'),
    path('api/road-health/update/', update_road_health_after_upload, name='update_road_health'),
]
