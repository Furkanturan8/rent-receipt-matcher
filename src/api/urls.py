"""
URL Configuration for NLP API
"""
from django.urls import path
from .views import (
    HealthCheckView,
    ProcessOCRView,
    ProcessPDFView,
    BatchProcessOCRView
)

urlpatterns = [
    # Health check
    path('health/', HealthCheckView.as_view(), name='nlp-health'),
    
    # Processing endpoints (v1)
    path('api/v1/process-ocr/', ProcessOCRView.as_view(), name='nlp-process-ocr'),
    path('api/v1/process-pdf/', ProcessPDFView.as_view(), name='nlp-process-pdf'),
    path('api/v1/batch-process-ocr/', BatchProcessOCRView.as_view(), name='nlp-batch-process-ocr'),
]
