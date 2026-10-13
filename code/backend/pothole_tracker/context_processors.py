"""
Context processors for the pothole_tracker project.
"""
from django.conf import settings


def pre_url(request):
    """
    Add PRE_URL to the template context.
    """
    return {
        'PRE_URL': '/' + settings.PRE_URL.strip('/') + '/' if settings.PRE_URL else '/',
    }
