"""
URL configuration for pothole_tracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

PRE_URL = settings.PRE_URL
admin.site.site_url = "/" + settings.PRE_URL

urlpatterns = [
    path(PRE_URL + 'admin/', admin.site.urls),
    path(PRE_URL + 'accounts/', include('accounts.urls')),
    path(PRE_URL + 'gov-api/', include('government.urls')),
    path(PRE_URL + '', include('potholes.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve static files - for both development and production
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Serve assets from staticfiles directory
from django.views.static import serve
from django.urls import re_path
import os

urlpatterns += [
    re_path(r'^' + PRE_URL + r'assets/(?P<path>.*)$', serve, {
        'document_root': os.path.join(settings.STATIC_ROOT, 'assets'),
    }),
]
