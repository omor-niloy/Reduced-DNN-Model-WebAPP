from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    
    def ready(self):
        """
        Run cleanup when Django starts
        """
        # Only run in the main process (not in reloader process)
        import os
        if os.environ.get('RUN_MAIN') == 'true':
            from .cleanup import cleanup_media_directories
            print("=" * 60)
            print("Starting Django server - Cleaning up old media files...")
            print("=" * 60)
            cleanup_media_directories(max_age_hours=1)
            print("=" * 60)
