from django.shortcuts import render
from django.http import HttpResponse


def home_view(request):
    """Simple home page with navigation to registration and admin."""
    return render(request, 'home.html', {
        'user': request.user
    })
