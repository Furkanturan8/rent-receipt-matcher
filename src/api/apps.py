"""
Django App Configuration for NLP Service
"""
from django.apps import AppConfig


class NlpApiConfig(AppConfig):
    """NLP API service configuration"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.api'
    verbose_name = 'NLP Receipt Processing Service'
    
    def ready(self):
        """Initialize models on startup"""
        # Models will be loaded on first request to save startup time
        pass
