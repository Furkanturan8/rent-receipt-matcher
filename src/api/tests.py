"""
Django Tests for NLP API
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
import json


class HealthCheckTests(TestCase):
    """Health check endpoint tests"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/api/nlp/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('service', response.data)


class ProcessOCRTests(TestCase):
    """OCR processing endpoint tests"""
    
    def setUp(self):
        self.client = APIClient()
        self.valid_ocr_data = {
            "ocr_data": {
                "sender": "FURKAN TURAN",
                "sender_iban": "TR660001200146300002247852",
                "recipient": "Mustafa Derin",
                "receiver_iban": "TR090020200008733123900001",
                "description": "Çiçek Apt. No:8, Haziran kira ödemesi, 15000 TL",
                "amount": "15000.00",
                "amount_currency": "TRY",
                "date": "20/11/2025"
            },
            "enable_matching": False
        }
    
    def test_valid_ocr_processing(self):
        """Test valid OCR data processing"""
        response = self.client.post(
            '/api/nlp/process-ocr/',
            data=json.dumps(self.valid_ocr_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('intent', response.data)
        self.assertIn('ner', response.data)
        self.assertIn('final_entities', response.data)
    
    def test_missing_description(self):
        """Test OCR data without description"""
        invalid_data = {
            "ocr_data": {
                "sender": "FURKAN TURAN"
            },
            "enable_matching": False
        }
        response = self.client.post(
            '/api/nlp/process-ocr/',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class BatchProcessTests(TestCase):
    """Batch processing endpoint tests"""
    
    def setUp(self):
        self.client = APIClient()
        self.batch_data = {
            "receipts": [
                {
                    "id": "receipt_001",
                    "ocr_data": {
                        "description": "Haziran kira 5000 TL Daire 5"
                    }
                },
                {
                    "id": "receipt_002",
                    "ocr_data": {
                        "description": "Temmuz aidat 500 TL"
                    }
                }
            ],
            "enable_matching": False
        }
    
    def test_batch_processing(self):
        """Test batch processing"""
        response = self.client.post(
            '/api/nlp/batch-process-ocr/',
            data=json.dumps(self.batch_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 2)
        self.assertIn('results', response.data)
