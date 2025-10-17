from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'road-segments', views.RoadSegmentViewSet, basename='road-segments')

urlpatterns = [
    # Authentication endpoints
    path('auth/signup/', views.gov_signup, name='gov-signup'),
    path('auth/login/', views.gov_login, name='gov-login'),
    path('auth/logout/', views.gov_logout, name='gov-logout'),
    path('auth/verify/', views.verify_token, name='verify-token'),
    
    # Include router URLs for road segments
    path('', include(router.urls)),
]
