"""
Views for dashcam video processing and file uploads
"""
import os
import tempfile
import shutil
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.management import call_command
from django.conf import settings
import json


@csrf_exempt
@require_http_methods(["POST"])
def upload_videos(request):
    """Upload multiple video files"""
    try:
        uploaded_files = []
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', 'videos')
        os.makedirs(upload_dir, exist_ok=True)
        
        for file in request.FILES.getlist('files'):
            if file.name.lower().endswith(('.mp4', '.avi', '.mov')):
                # Save file
                file_path = os.path.join(upload_dir, file.name)
                with open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                uploaded_files.append(file_path)
            else:
                return JsonResponse({
                    'error': f'Invalid file type: {file.name}. Only video files are allowed.'
                }, status=400)
        
        return JsonResponse({
            'success': True,
            'uploaded_files': uploaded_files,
            'message': f'Successfully uploaded {len(uploaded_files)} video files'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def upload_gps(request):
    """Upload multiple GPS .git files"""
    try:
        uploaded_files = []
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', 'gps')
        os.makedirs(upload_dir, exist_ok=True)
        
        for file in request.FILES.getlist('files'):
            if file.name.lower().endswith('.git'):
                # Save file
                file_path = os.path.join(upload_dir, file.name)
                with open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                uploaded_files.append(file_path)
            else:
                return JsonResponse({
                    'error': f'Invalid file type: {file.name}. Only .git files are allowed.'
                }, status=400)
        
        return JsonResponse({
            'success': True,
            'uploaded_files': uploaded_files,
            'upload_directory': upload_dir,
            'message': f'Successfully uploaded {len(uploaded_files)} GPS files'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def process_video(request):
    """Process a single video with GPS data"""
    try:
        data = json.loads(request.body)
        video_path = data.get('video_path')
        gps_directory = data.get('gps_directory')
        distance_threshold = data.get('distance_threshold', 2.5)
        
        if not video_path or not gps_directory:
            return JsonResponse({
                'error': 'video_path and gps_directory are required'
            }, status=400)
        
        if not os.path.exists(video_path):
            return JsonResponse({
                'error': f'Video file not found: {video_path}'
            }, status=400)
        
        if not os.path.exists(gps_directory):
            return JsonResponse({
                'error': f'GPS directory not found: {gps_directory}'
            }, status=400)
        
        # Call the Django management command to process the video
        call_command(
            'process_dashcam_video',
            video_path=video_path,
            gps_directory=gps_directory,
            distance_threshold=distance_threshold
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Video processing completed successfully',
            'video_path': video_path,
            'gps_directory': gps_directory
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt  
@require_http_methods(["POST"])
def cleanup_uploads(request):
    """Clean up uploaded files after processing"""
    try:
        upload_base_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        if os.path.exists(upload_base_dir):
            shutil.rmtree(upload_base_dir)
            os.makedirs(upload_base_dir, exist_ok=True)
        
        return JsonResponse({
            'success': True,
            'message': 'Upload directory cleaned successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
