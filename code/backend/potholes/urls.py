from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .home_views import home_view
from . import upload_views
from .road_health_views import RoadHealthViewSet, ContractorMessageViewSet, update_road_health_after_upload

router = DefaultRouter()
router.register(r'potholes', views.PotholeViewSet)
router.register(r'road-health', RoadHealthViewSet)
router.register(r'contractor-messages', ContractorMessageViewSet)

urlpatterns = [
    path('', home_view, name='home'),
    path('api/', include(router.urls)),
    path('api/upload-videos/', upload_views.upload_videos, name='upload_videos'),
    path('api/upload-gps/', upload_views.upload_gps, name='upload_gps'),
    path('api/process-video/', upload_views.process_video, name='process_video'),
    path('api/cleanup-uploads/', upload_views.cleanup_uploads, name='cleanup_uploads'),
    path('api/road-health/update/', update_road_health_after_upload, name='update_road_health'),
]
