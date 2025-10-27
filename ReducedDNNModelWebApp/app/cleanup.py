"""
Utility functions for cleaning up temporary files
"""
import os
import time
import shutil
from pathlib import Path
from django.conf import settings


def cleanup_media_directories(max_age_hours=1):
    """
    Clean up old files from media directories and __pycache__ directories
    
    Args:
        max_age_hours: Delete files older than this many hours
    """
    directories = [
        Path(settings.MEDIA_ROOT) / 'model_uploads',
        Path(settings.MEDIA_ROOT) / 'processed_models',
        Path(settings.MEDIA_ROOT) / 'architectures',
        Path(settings.MEDIA_ROOT) / 'training_scripts',
    ]
    
    print(f"Checking directories for files older than {max_age_hours} hours ({max_age_hours * 3600} seconds):")
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    total_deleted = 0
    total_size_freed = 0
    
    for directory in directories:
        print(f"\nChecking: {directory}")
        if not directory.exists():
            print(f"  → Directory does not exist, skipping")
            continue
        
        try:
            files_in_dir = list(directory.glob('*'))
            print(f"  → Found {len(files_in_dir)} item(s)")
            
            for file_path in files_in_dir:
                if file_path.is_file():
                    file_age = current_time - os.path.getmtime(file_path)
                    file_age_minutes = file_age / 60
                    print(f"    • {file_path.name} - Age: {file_age_minutes:.1f} minutes ({file_age:.0f} seconds)")
                    
                    if file_age > max_age_seconds:
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            total_deleted += 1
                            total_size_freed += file_size
                            print(f"      ✓ DELETED (size: {file_size / (1024*1024):.2f} MB)")
                        except Exception as e:
                            print(f"      ✗ Failed to delete: {e}")
                    else:
                        print(f"      ○ Too new, keeping")
        except Exception as e:
            print(f"  → Error cleaning directory: {e}")
    
    # Clean up __pycache__ directories
    print(f"\n\nCleaning up __pycache__ directories:")
    pycache_deleted = 0
    pycache_size_freed = 0
    
    # Search for __pycache__ in media directory and its subdirectories
    media_root = Path(settings.MEDIA_ROOT)
    if media_root.exists():
        for pycache_dir in media_root.rglob('__pycache__'):
            if pycache_dir.is_dir():
                try:
                    # Calculate directory size
                    dir_size = sum(f.stat().st_size for f in pycache_dir.rglob('*') if f.is_file())
                    
                    # Remove the directory
                    shutil.rmtree(pycache_dir)
                    pycache_deleted += 1
                    pycache_size_freed += dir_size
                    print(f"  ✓ Removed: {pycache_dir.relative_to(media_root)} (size: {dir_size / 1024:.2f} KB)")
                except Exception as e:
                    print(f"  ✗ Failed to remove {pycache_dir.relative_to(media_root)}: {e}")
    
    # Clean up .pyc files in architectures directory
    architectures_dir = Path(settings.MEDIA_ROOT) / 'architectures'
    if architectures_dir.exists():
        pyc_files = list(architectures_dir.glob('*.pyc'))
        if pyc_files:
            print(f"\n\nCleaning up .pyc files in architectures:")
            for pyc_file in pyc_files:
                try:
                    file_size = os.path.getsize(pyc_file)
                    os.remove(pyc_file)
                    total_deleted += 1
                    total_size_freed += file_size
                    print(f"  ✓ Removed: {pyc_file.name} (size: {file_size / 1024:.2f} KB)")
                except Exception as e:
                    print(f"  ✗ Failed to remove {pyc_file.name}: {e}")
    
    if total_deleted > 0 or pycache_deleted > 0:
        total_size_mb = (total_size_freed + pycache_size_freed) / (1024 * 1024)
        print(f"\n✓ Cleanup complete: {total_deleted} file(s) and {pycache_deleted} __pycache__ dir(s) deleted, {total_size_mb:.2f} MB freed")
    else:
        print("\n○ Cleanup complete: No old files to delete")
    
    return total_deleted + pycache_deleted, total_size_freed + pycache_size_freed


def cleanup_all_media():
    """
    Delete all files in media directories (use with caution!)
    """
    directories = [
        Path(settings.MEDIA_ROOT) / 'model_uploads',
        Path(settings.MEDIA_ROOT) / 'processed_models',
        Path(settings.MEDIA_ROOT) / 'architectures',
    ]
    
    total_deleted = 0
    
    for directory in directories:
        if not directory.exists():
            continue
        
        try:
            for file_path in directory.glob('*'):
                if file_path.is_file():
                    try:
                        os.remove(file_path)
                        total_deleted += 1
                        print(f"Deleted: {file_path.name}")
                    except Exception as e:
                        print(f"Failed to delete {file_path}: {e}")
        except Exception as e:
            print(f"Error cleaning directory {directory}: {e}")
    
    print(f"All media cleanup complete: {total_deleted} file(s) deleted")
    return total_deleted
