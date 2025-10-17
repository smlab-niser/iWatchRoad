from django.shortcuts import render
from django.http import HttpResponse, FileResponse, Http404
from django.conf import settings
from django.templatetags.static import static
from django.template.loader import get_template
import os


def home_view(request):
    """Serve the static index.html file from staticfiles directory."""
    # Path to the static index.html file
    static_index_path = os.path.join(settings.STATIC_ROOT, 'index.html')
    
    # Check if the file exists
    if os.path.exists(static_index_path):
        # Read the HTML content
        with open(static_index_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Return as HttpResponse with proper content type
        return HttpResponse(html_content, content_type='text/html')
    else:
        # Fallback to the Django template if static file doesn't exist
        return render(request, 'home.html', {
            'user': request.user
        })
