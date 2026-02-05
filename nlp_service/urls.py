"""
NLP Microservice URL Configuration
"""
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger/OpenAPI Schema
schema_view = get_schema_view(
    openapi.Info(
        title="NLP Receipt Processing Microservice API",
        default_version='v1',
        description="""
        Banking Receipt Processing Microservice with NLP
        
        Features:
        - Intent Classification (kira, aidat, kapora, depozito)
        - Named Entity Recognition
        - OCR processing
        - Batch processing support
        """,
        contact=openapi.Contact(email="contact@yourapp.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # NLP API (includes health check)
    path('', include('src.api.urls')),
    
    # API Documentation
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='api-redoc'),
]
