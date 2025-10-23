from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
from pathlib import Path
from .utils import model_manager

# Create your views here.

@ensure_csrf_cookie
def Home(request):
    """Render the home page with CSRF token"""
    return render(request, 'home.html')


def classify_image(request):
    """
    API endpoint for image classification
    
    Expected POST data:
        - image: Image file
        - model: 'heavy' or 'light'
    
    Returns:
        JSON response with classification results
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Only POST method is allowed'
        }, status=405)
    
    # Validate model selection
    model_name = request.POST.get('model', '').lower()
    if model_name not in ['heavy', 'light']:
        return JsonResponse({
            'success': False,
            'error': 'Invalid model selection. Choose "heavy" or "light"'
        }, status=400)
    
    # Check if image was uploaded
    if 'image' not in request.FILES:
        return JsonResponse({
            'success': False,
            'error': 'No image file uploaded'
        }, status=400)
    
    image_file = request.FILES['image']
    
    # Security validation: File size limit (10MB)
    max_file_size = 10 * 1024 * 1024  # 10MB in bytes
    if image_file.size > max_file_size:
        return JsonResponse({
            'success': False,
            'error': f'File too large. Maximum size is 10MB. Your file: {round(image_file.size / (1024 * 1024), 2)}MB'
        }, status=400)
    
    # Validate file extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
    file_ext = os.path.splitext(image_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return JsonResponse({
            'success': False,
            'error': f'Invalid file type. Allowed types: {", ".join(allowed_extensions)}'
        }, status=400)
    
    # Security: Validate file is actually an image by checking magic bytes
    try:
        from PIL import Image
        import io
        
        # Read file content
        image_data = image_file.read()
        image_file.seek(0)  # Reset file pointer
        
        # Try to open as image - this validates it's a real image
        img = Image.open(io.BytesIO(image_data))
        img.verify()  # Verify it's not corrupted
        
        # Reset and re-open for actual use
        image_file.seek(0)
        img = Image.open(io.BytesIO(image_data))
        
        # Additional check: ensure image format matches extension
        img_format = img.format.lower() if img.format else ''
        expected_formats = {
            '.jpg': ['jpeg'],
            '.jpeg': ['jpeg'],
            '.png': ['png'],
            '.bmp': ['bmp'],
            '.gif': ['gif']
        }
        
        if img_format not in expected_formats.get(file_ext, []):
            return JsonResponse({
                'success': False,
                'error': 'File extension does not match actual image format. Possible spoofing attempt.'
            }, status=400)
        
        # Reset file pointer again for saving
        image_file.seek(0)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Invalid or corrupted image file. Please upload a valid image.'
        }, status=400)
    
    try:
        # Save uploaded image with sanitized filename
        upload_dir = Path(settings.MEDIA_ROOT) / 'uploads'
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Security: Sanitize filename to prevent path traversal
        import re
        import uuid
        from datetime import datetime
        
        # Remove any directory path components
        safe_filename = os.path.basename(image_file.name)
        # Remove any non-alphanumeric characters except dots and dashes
        safe_filename = re.sub(r'[^\w\s.-]', '', safe_filename)
        # Limit filename length
        name_part, ext_part = os.path.splitext(safe_filename)
        name_part = name_part[:50]  # Limit to 50 chars
        
        # Add timestamp and random string to prevent overwriting
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_str = uuid.uuid4().hex[:8]
        unique_filename = f"{timestamp}_{random_str}_{name_part}{ext_part}"
        
        # Save the file
        fs = FileSystemStorage(location=upload_dir)
        filename = fs.save(unique_filename, image_file)
        image_path = upload_dir / filename
        
        # Security: Verify the saved file path is within upload directory
        real_upload_dir = upload_dir.resolve()
        real_image_path = image_path.resolve()
        
        if not str(real_image_path).startswith(str(real_upload_dir)):
            # Path traversal attempt detected
            if os.path.exists(image_path):
                os.remove(image_path)
            return JsonResponse({
                'success': False,
                'error': 'Invalid file path. Security violation detected.'
            }, status=400)
        
        # Classify the image
        result = model_manager.classify_image(str(image_path), model_name)
        
        # Add filename to result
        result['filename'] = filename
        
        # Clean up uploaded file after classification to save memory
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as cleanup_error:
            # Log the error but don't fail the request
            print(f"Warning: Failed to delete uploaded file {image_path}: {cleanup_error}")
        
        if result['success']:
            return JsonResponse(result, status=200)
        else:
            return JsonResponse(result, status=500)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


def get_model_status(request):
    """
    API endpoint to check if models are loaded and available
    
    Returns:
        JSON response with model availability status
    """
    try:
        heavy_info = model_manager.get_model_info('heavy')
        light_info = model_manager.get_model_info('light')
        
        return JsonResponse({
            'success': True,
            'models': {
                'heavy': heavy_info,
                'light': light_info
            },
            'device': str(model_manager.device)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def cleanup_old_uploads(max_age_seconds=3600):
    """
    Utility function to clean up old uploaded files
    
    Args:
        max_age_seconds: Delete files older than this many seconds (default: 1 hour)
    
    This can be called periodically or manually to clean up any files
    that weren't deleted during normal processing
    """
    import time
    
    upload_dir = Path(settings.MEDIA_ROOT) / 'uploads'
    if not upload_dir.exists():
        return
    
    current_time = time.time()
    deleted_count = 0
    
    try:
        for file_path in upload_dir.glob('*'):
            if file_path.is_file():
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age_seconds:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                    except Exception as e:
                        print(f"Failed to delete {file_path}: {e}")
        
        print(f"Cleaned up {deleted_count} old uploaded files")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
