"""
Security utilities for file upload validation
"""
from PIL import Image
import io
import os


class FileSecurityValidator:
    """
    Validates uploaded files for security threats
    """
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Maximum image dimensions
    MAX_DIMENSION = 4096
    
    # Expected image formats for each extension
    EXTENSION_FORMAT_MAP = {
        '.jpg': ['jpeg'],
        '.jpeg': ['jpeg'],
        '.png': ['png'],
        '.bmp': ['bmp'],
        '.gif': ['gif']
    }
    
    @staticmethod
    def validate_file_size(file_obj):
        """
        Validate file size
        
        Args:
            file_obj: Django UploadedFile object
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if file_obj.size > FileSecurityValidator.MAX_FILE_SIZE:
            size_mb = round(file_obj.size / (1024 * 1024), 2)
            return False, f'File too large. Maximum: 10MB. Your file: {size_mb}MB'
        return True, None
    
    @staticmethod
    def validate_file_extension(filename):
        """
        Validate file extension
        
        Args:
            filename: Name of the file
            
        Returns:
            tuple: (is_valid, error_message, extension)
        """
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext not in FileSecurityValidator.ALLOWED_EXTENSIONS:
            return False, f'Invalid file type. Allowed: {", ".join(FileSecurityValidator.ALLOWED_EXTENSIONS)}', file_ext
        
        return True, None, file_ext
    
    @staticmethod
    def validate_image_content(file_obj, expected_extension):
        """
        Validate that file is actually an image and format matches extension
        
        Args:
            file_obj: Django UploadedFile object
            expected_extension: Expected file extension
            
        Returns:
            tuple: (is_valid, error_message, image_object)
        """
        try:
            # Read file content
            image_data = file_obj.read()
            file_obj.seek(0)  # Reset file pointer
            
            # Try to open as image
            img = Image.open(io.BytesIO(image_data))
            img.verify()  # Verify it's not corrupted
            
            # Reset and re-open for actual use
            file_obj.seek(0)
            img = Image.open(io.BytesIO(image_data))
            
            # Check format matches extension
            img_format = img.format.lower() if img.format else ''
            expected_formats = FileSecurityValidator.EXTENSION_FORMAT_MAP.get(expected_extension, [])
            
            if img_format not in expected_formats:
                return False, 'File extension does not match actual image format', None
            
            # Check dimensions
            width, height = img.size
            if width > FileSecurityValidator.MAX_DIMENSION or height > FileSecurityValidator.MAX_DIMENSION:
                return False, f'Image too large. Max: {FileSecurityValidator.MAX_DIMENSION}x{FileSecurityValidator.MAX_DIMENSION}. Yours: {width}x{height}', None
            
            # Reset file pointer
            file_obj.seek(0)
            
            return True, None, img
            
        except Exception as e:
            return False, 'Invalid or corrupted image file', None
    
    @staticmethod
    def sanitize_filename(filename):
        """
        Sanitize filename to prevent security issues
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename
        """
        import re
        import uuid
        from datetime import datetime
        
        # Remove any directory path components
        safe_filename = os.path.basename(filename)
        
        # Remove any non-alphanumeric characters except dots and dashes
        safe_filename = re.sub(r'[^\w\s.-]', '', safe_filename)
        
        # Limit filename length
        name_part, ext_part = os.path.splitext(safe_filename)
        name_part = name_part[:50]  # Limit to 50 chars
        
        # Add timestamp and random string
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_str = uuid.uuid4().hex[:8]
        
        return f"{timestamp}_{random_str}_{name_part}{ext_part}"
    
    @staticmethod
    def validate_path(file_path, allowed_directory):
        """
        Validate that file path is within allowed directory (prevent path traversal)
        
        Args:
            file_path: Path to validate
            allowed_directory: Directory that should contain the file
            
        Returns:
            bool: True if path is safe
        """
        from pathlib import Path
        
        real_allowed_dir = Path(allowed_directory).resolve()
        real_file_path = Path(file_path).resolve()
        
        return str(real_file_path).startswith(str(real_allowed_dir))


def validate_uploaded_image(file_obj):
    """
    Comprehensive validation of uploaded image file
    
    Args:
        file_obj: Django UploadedFile object
        
    Returns:
        dict: Validation result with 'valid', 'error', and 'sanitized_filename' keys
    """
    validator = FileSecurityValidator()
    
    # Validate file size
    is_valid, error = validator.validate_file_size(file_obj)
    if not is_valid:
        return {'valid': False, 'error': error}
    
    # Validate extension
    is_valid, error, extension = validator.validate_file_extension(file_obj.name)
    if not is_valid:
        return {'valid': False, 'error': error}
    
    # Validate image content
    is_valid, error, img = validator.validate_image_content(file_obj, extension)
    if not is_valid:
        return {'valid': False, 'error': error}
    
    # Sanitize filename
    safe_filename = validator.sanitize_filename(file_obj.name)
    
    return {
        'valid': True,
        'error': None,
        'sanitized_filename': safe_filename,
        'image': img
    }
