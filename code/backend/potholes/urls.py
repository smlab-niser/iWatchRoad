from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .home_views import home_view
from . import upload_views

router = DefaultRouter()
router.register(r'potholes', views.PotholeViewSet)

urlpatterns = [
    path('', home_view, name='home'),
    path('api/', include(router.urls)),
    path('api/upload-videos/', upload_views.upload_videos, name='upload_videos'),
    path('api/upload-gps/', upload_views.upload_gps, name='upload_gps'),
    path('api/process-video/', upload_views.process_video, name='process_video'),
    path('api/cleanup-uploads/', upload_views.cleanup_uploads, name='cleanup_uploads'),
]
