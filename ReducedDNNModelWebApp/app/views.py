from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
from pathlib import Path
from datetime import datetime
import re
from .model_optimizer import model_optimizer
from .cleanup import cleanup_media_directories

# Create your views here.

@ensure_csrf_cookie
def Home(request):
    # Clean up old files when user visits home page
    print("=" * 60)
    print("Home page accessed - Running cleanup...")
    print("=" * 60)
    try:
        # Clean files immediately on page refresh (0 hours = delete all files)
        deleted, size_freed = cleanup_media_directories(max_age_hours=0)  # 0 = immediate cleanup
        size_mb = size_freed / (1024 * 1024)
        print(f"Cleanup completed: {deleted} files deleted, {size_mb:.2f} MB freed")
    except Exception as e:
        print(f"Cleanup error: {str(e)}")
        import traceback
        traceback.print_exc()
    print("=" * 60)
    return render(request, 'home.html')


def process_model(request):
    """
    Handle model upload, optimization (pruning/quantization), and return download link
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Only POST method is allowed'
        }, status=405)
    
    # Validate technique selection
    technique = request.POST.get('technique', '').lower()
    if technique not in ['pruning', 'quantization', 'crd']:
        return JsonResponse({
            'success': False,
            'error': 'Invalid technique. Choose "pruning", "quantization", or "crd"'
        }, status=400)
    
    # Check if both model and architecture files were uploaded
    if 'model' not in request.FILES:
        return JsonResponse({
            'success': False,
            'error': 'No model weights file uploaded'
        }, status=400)
    
    if 'architecture' not in request.FILES:
        return JsonResponse({
            'success': False,
            'error': 'No architecture file uploaded'
        }, status=400)
    
    model_file = request.FILES['model']
    architecture_file = request.FILES['architecture']
    
    # Validate model file extension
    allowed_model_extensions = ['.pth', '.pt']
    model_ext = os.path.splitext(model_file.name)[1].lower()
    
    if model_ext not in allowed_model_extensions:
        return JsonResponse({
            'success': False,
            'error': f'Invalid model file type. Allowed types: {", ".join(allowed_model_extensions)}'
        }, status=400)
    
    # Validate architecture file extension
    arch_ext = os.path.splitext(architecture_file.name)[1].lower()
    if arch_ext != '.py':
        return JsonResponse({
            'success': False,
            'error': 'Invalid architecture file type. Must be a .py file'
        }, status=400)
    
    try:
        # Create directories for uploads and processed models
        upload_dir = Path(settings.MEDIA_ROOT) / 'model_uploads'
        processed_dir = Path(settings.MEDIA_ROOT) / 'processed_models'
        arch_dir = Path(settings.MEDIA_ROOT) / 'architectures'
        upload_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        arch_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitize filenames
        safe_model_filename = os.path.basename(model_file.name)
        safe_model_filename = re.sub(r'[^\w\s.-]', '', safe_model_filename)
        model_name_part, model_ext_part = os.path.splitext(safe_model_filename)
        model_name_part = model_name_part[:50]
        
        safe_arch_filename = os.path.basename(architecture_file.name)
        safe_arch_filename = re.sub(r'[^\w\s.-]', '', safe_arch_filename)
        arch_name_part, arch_ext_part = os.path.splitext(safe_arch_filename)
        arch_name_part = arch_name_part[:50]
        
        # Add timestamp to prevent overwriting
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_model_filename = f"{timestamp}_{model_name_part}{model_ext_part}"
        unique_arch_filename = f"{timestamp}_{arch_name_part}{arch_ext_part}"
        
        # Save uploaded model weights file
        fs_model = FileSystemStorage(location=upload_dir)
        model_filename = fs_model.save(unique_model_filename, model_file)
        input_path = upload_dir / model_filename
        
        # Save uploaded architecture file
        fs_arch = FileSystemStorage(location=arch_dir)
        arch_filename = fs_arch.save(unique_arch_filename, architecture_file)
        arch_path = arch_dir / arch_filename
        
        # Create output filename
        technique_suffix = '_pruned' if technique == 'pruning' else '_quantized'
        output_filename = f"{timestamp}_{model_name_part}{technique_suffix}{model_ext_part}"
        output_path = processed_dir / output_filename
        
        # Get class name and init params from form
        class_name = request.POST.get('class_name', '').strip()
        init_params_json = request.POST.get('init_params', '').strip()
        
        if not class_name:
            # Clean up uploaded files
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(arch_path):
                os.remove(arch_path)
            return JsonResponse({
                'success': False,
                'error': 'Model class name is required'
            }, status=400)
        
        # Parse init params JSON
        init_params = {}
        if init_params_json:
            try:
                import json
                init_params = json.loads(init_params_json)
                if not isinstance(init_params, dict):
                    raise ValueError("Init params must be a JSON object")
            except (json.JSONDecodeError, ValueError) as e:
                # Clean up uploaded files
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(arch_path):
                    os.remove(arch_path)
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid JSON format for init params: {str(e)}'
                }, status=400)
        
        # Get optimization parameters
        kwargs = {}
        kwargs['architecture_path'] = str(arch_path)
        kwargs['class_name'] = class_name
        kwargs['init_params'] = init_params
        
        if technique == 'pruning':
            pruning_amount = int(request.POST.get('pruning_amount', 50))
            # Validate pruning amount is between 0 and 99
            if pruning_amount < 0 or pruning_amount > 99:
                # Clean up uploaded files
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(arch_path):
                    os.remove(arch_path)
                return JsonResponse({
                    'success': False,
                    'error': 'Pruning amount must be between 0 and 99'
                }, status=400)
            kwargs['pruning_amount'] = pruning_amount
        elif technique == 'quantization':
            quantization_type = request.POST.get('quantization_type', 'dynamic')
            kwargs['quantization_type'] = quantization_type
        elif technique == 'crd':
            # Get student model parameters
            student_class_name = request.POST.get('student_class_name', '').strip()
            student_init_params_json = request.POST.get('student_init_params', '').strip()
            
            if not student_class_name:
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(arch_path):
                    os.remove(arch_path)
                return JsonResponse({
                    'success': False,
                    'error': 'Student model class name is required for CRD'
                }, status=400)
            
            # Parse student init params
            student_init_params = {}
            if student_init_params_json:
                try:
                    import json
                    student_init_params = json.loads(student_init_params_json)
                    if not isinstance(student_init_params, dict):
                        raise ValueError("Student init params must be a JSON object")
                except (json.JSONDecodeError, ValueError) as e:
                    if os.path.exists(input_path):
                        os.remove(input_path)
                    if os.path.exists(arch_path):
                        os.remove(arch_path)
                    return JsonResponse({
                        'success': False,
                        'error': f'Invalid JSON format for student init params: {str(e)}'
                    }, status=400)
            
            # Handle training script file
            if 'training_script' not in request.FILES:
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(arch_path):
                    os.remove(arch_path)
                return JsonResponse({
                    'success': False,
                    'error': 'Training script file is required for CRD'
                }, status=400)
            
            training_script_file = request.FILES['training_script']
            
            # Validate training script extension
            training_ext = os.path.splitext(training_script_file.name)[1].lower()
            if training_ext != '.py':
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(arch_path):
                    os.remove(arch_path)
                return JsonResponse({
                    'success': False,
                    'error': 'Training script must be a .py file'
                }, status=400)
            
            # Save training script
            training_dir = Path(settings.MEDIA_ROOT) / 'training_scripts'
            training_dir.mkdir(parents=True, exist_ok=True)
            
            safe_training_filename = os.path.basename(training_script_file.name)
            safe_training_filename = re.sub(r'[^\w\s.-]', '', safe_training_filename)
            unique_training_filename = f"{timestamp}_{safe_training_filename}"
            
            fs_training = FileSystemStorage(location=training_dir)
            training_filename = fs_training.save(unique_training_filename, training_script_file)
            training_path = training_dir / training_filename
            
            kwargs['student_class_name'] = student_class_name
            kwargs['student_init_params'] = student_init_params
            kwargs['training_script_path'] = str(training_path)
        
        # Process the model
        result = model_optimizer.optimize_model(
            str(input_path),
            str(output_path),
            technique=technique,
            **kwargs
        )
        
        # Save a copy of the architecture file with the processed model
        # This ensures we can view architecture later even after cleanup
        if result['success']:
            arch_copy_name = output_filename.replace('.pth', '_arch.py').replace('.pt', '_arch.py')
            arch_copy_path = processed_dir / arch_copy_name
            import shutil
            shutil.copy2(str(arch_path), str(arch_copy_path))
        
        # Clean up uploaded files
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(arch_path):
                os.remove(arch_path)
        except Exception as cleanup_error:
            print(f"Warning: Failed to delete uploaded files: {cleanup_error}")
        
        if result['success']:
            result['download_filename'] = output_filename
            return JsonResponse(result, status=200)
        else:
            return JsonResponse(result, status=500)
            
    except Exception as e:
        # Clean up files on error
        try:
            if 'input_path' in locals() and os.path.exists(input_path):
                os.remove(input_path)
            if 'arch_path' in locals() and os.path.exists(arch_path):
                os.remove(arch_path)
        except:
            pass
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


def download_model(request, filename):
    """
    Handle model download
    """
    try:
        processed_dir = Path(settings.MEDIA_ROOT) / 'processed_models'
        file_path = processed_dir / filename
        
        # Security: Verify the file path is within processed directory
        real_processed_dir = processed_dir.resolve()
        real_file_path = file_path.resolve()
        
        if not str(real_file_path).startswith(str(real_processed_dir)):
            return JsonResponse({
                'success': False,
                'error': 'Invalid file path'
            }, status=400)
        
        if not os.path.exists(file_path):
            return JsonResponse({
                'success': False,
                'error': 'File not found'
            }, status=404)
        
        # Return file as download
        response = FileResponse(open(file_path, 'rb'), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Download error: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def view_architecture(request, filename):
    """View the architecture summary of a processed model"""
    try:
        # Construct full file path
        processed_dir = os.path.join(settings.MEDIA_ROOT, 'processed_models')
        file_path = os.path.join(processed_dir, filename)
        
        # Security check
        if not os.path.abspath(file_path).startswith(os.path.abspath(processed_dir)):
            return JsonResponse({
                'success': False,
                'error': 'Invalid file path'
            }, status=400)
        
        if not os.path.exists(file_path):
            return JsonResponse({
                'success': False,
                'error': 'File not found'
            }, status=404)
        
        # Find the corresponding architecture file
        # The architecture file is saved as: modelname_arch.py
        arch_filename = filename.replace('.pth', '_arch.py').replace('.pt', '_arch.py')
        architecture_path = os.path.join(processed_dir, arch_filename)
        
        if not os.path.exists(architecture_path):
            return JsonResponse({
                'success': False,
                'error': 'Architecture file not found. It may have been cleaned up.'
            }, status=404)
        
        # Generate architecture summary
        architecture_summary = model_optimizer.get_model_architecture(file_path, architecture_path)
        
        return JsonResponse({
            'success': True,
            'architecture': architecture_summary
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Failed to load architecture: {str(e)}'
        }, status=500)


