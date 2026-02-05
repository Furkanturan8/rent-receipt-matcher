"""
Django REST Framework Views
"""
import os
import tempfile
import logging
from pathlib import Path

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, JSONParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import (
    ProcessOCRRequestSerializer,
    ProcessPDFRequestSerializer,
    ProcessingResponseSerializer,
    ErrorResponseSerializer,
    HealthCheckResponseSerializer
)
from .services import nlp_service

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Health check endpoint
    GET /api/nlp/health
    """
    
    @swagger_auto_schema(
        operation_description="Service health check",
        responses={
            200: HealthCheckResponseSerializer,
        }
    )
    def get(self, request):
        """Health check"""
        try:
            health_data = nlp_service.health_check()
            return Response(health_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return Response(
                {'status': 'unhealthy', 'error': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class ProcessOCRView(APIView):
    """
    Process OCR output
    POST /api/nlp/process-ocr
    """
    parser_classes = [JSONParser]
    
    @swagger_auto_schema(
        operation_description="Process OCR output through NLP pipeline",
        request_body=ProcessOCRRequestSerializer,
        responses={
            200: ProcessingResponseSerializer,
            400: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        }
    )
    def post(self, request):
        """Process OCR data"""
        serializer = ProcessOCRRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid request', 'detail': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            ocr_data = serializer.validated_data['ocr_data']
            enable_matching = serializer.validated_data.get('enable_matching', False)
            
            # Process
            result = nlp_service.process_ocr_output(
                ocr_data=ocr_data,
                enable_matching=enable_matching
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}", exc_info=True)
            return Response(
                {'error': 'Processing failed', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProcessPDFView(APIView):
    """
    Process PDF file
    POST /api/nlp/process-pdf
    """
    parser_classes = [MultiPartParser]
    
    @swagger_auto_schema(
        operation_description="Process PDF receipt file through full pipeline (OCR + NLP)",
        manual_parameters=[
            openapi.Parameter(
                'pdf_file',
                openapi.IN_FORM,
                description="PDF file to process",
                type=openapi.TYPE_FILE,
                required=True
            ),
            openapi.Parameter(
                'bank',
                openapi.IN_FORM,
                description="Bank hint (halkbank, kuveytturk, yapikredi, ziraatbank)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'enable_matching',
                openapi.IN_FORM,
                description="Enable receipt matching",
                type=openapi.TYPE_BOOLEAN,
                required=False,
                default=False
            ),
            openapi.Parameter(
                'use_logo_detection',
                openapi.IN_FORM,
                description="Use logo detection for bank identification",
                type=openapi.TYPE_BOOLEAN,
                required=False,
                default=False
            ),
        ],
        responses={
            200: ProcessingResponseSerializer,
            400: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        }
    )
    def post(self, request):
        """Process PDF file"""
        # Validate file
        pdf_file = request.FILES.get('pdf_file')
        if not pdf_file:
            return Response(
                {'error': 'No PDF file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file extension
        if not pdf_file.name.endswith('.pdf'):
            return Response(
                {'error': 'File must be a PDF'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get optional parameters
        bank = request.data.get('bank', None)
        enable_matching = request.data.get('enable_matching', 'false').lower() == 'true'
        use_logo_detection = request.data.get('use_logo_detection', 'false').lower() == 'true'
        
        # Save to temp file
        temp_pdf = None
        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(
                suffix='.pdf',
                delete=False
            ) as temp_file:
                for chunk in pdf_file.chunks():
                    temp_file.write(chunk)
                temp_pdf = temp_file.name
            
            logger.info(f"Processing PDF: {pdf_file.name} (temp: {temp_pdf})")
            
            # Process
            result = nlp_service.process_pdf(
                pdf_path=temp_pdf,
                bank=bank,
                enable_matching=enable_matching,
                use_logo_detection=use_logo_detection
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"PDF processing failed: {e}", exc_info=True)
            return Response(
                {'error': 'Processing failed', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        finally:
            # Clean up temp file
            if temp_pdf and os.path.exists(temp_pdf):
                try:
                    os.unlink(temp_pdf)
                    logger.debug(f"Cleaned up temp file: {temp_pdf}")
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")


class BatchProcessOCRView(APIView):
    """
    Batch process multiple OCR outputs
    POST /api/nlp/batch-process-ocr
    """
    parser_classes = [JSONParser]
    
    @swagger_auto_schema(
        operation_description="Batch process multiple OCR outputs",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'receipts': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_STRING),
                            'ocr_data': openapi.Schema(type=openapi.TYPE_OBJECT)
                        }
                    )
                ),
                'enable_matching': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False)
            }
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'processed': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'results': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT)
                    )
                }
            ),
            400: ErrorResponseSerializer,
        }
    )
    def post(self, request):
        """Batch process OCR data"""
        receipts = request.data.get('receipts', [])
        enable_matching = request.data.get('enable_matching', False)
        
        if not receipts or not isinstance(receipts, list):
            return Response(
                {'error': 'Invalid request', 'detail': 'receipts must be a non-empty array'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = []
        processed = 0
        
        for receipt in receipts:
            receipt_id = receipt.get('id', f'receipt_{processed}')
            ocr_data = receipt.get('ocr_data')
            
            if not ocr_data:
                results.append({
                    'id': receipt_id,
                    'status': 'error',
                    'error': 'Missing ocr_data'
                })
                continue
            
            try:
                result = nlp_service.process_ocr_output(
                    ocr_data=ocr_data,
                    enable_matching=enable_matching
                )
                results.append({
                    'id': receipt_id,
                    'status': 'success',
                    'data': result
                })
                processed += 1
                
            except Exception as e:
                logger.error(f"Failed to process receipt {receipt_id}: {e}")
                results.append({
                    'id': receipt_id,
                    'status': 'error',
                    'error': str(e)
                })
        
        return Response(
            {
                'status': 'completed',
                'processed': processed,
                'total': len(receipts),
                'results': results
            },
            status=status.HTTP_200_OK
        )
