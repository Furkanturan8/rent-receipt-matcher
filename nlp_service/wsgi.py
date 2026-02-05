"""
WSGI config for NLP Microservice
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nlp_service.settings')

application = get_wsgi_application()
