# 🔗 Django Backend Entegrasyon Rehberi

## 📌 Genel Bakış

Bu NLP servisi, Django backend'inizde bir **microservice** gibi çalışır:

```
Frontend (React/Vue)
    ↓
Django Backend (views/models)
    ↓
NLP Service (src.api)
    ↓
Eğitilmiş Modeller (Intent + NER)
```

## 🏗️ Mimari

### 1. Servis Katmanı (Service Layer)
- **Dosya:** `src/api/services.py`
- **Amaç:** Business logic, model yönetimi
- **Pattern:** Singleton
- **Özellik:** Lazy loading (ilk istekte model yüklenir)

### 2. API Katmanı (API Layer)
- **Dosya:** `src/api/views.py`
- **Framework:** Django REST Framework
- **Endpoints:** 4 ana endpoint
- **Özellik:** Swagger/OpenAPI dökümantasyonu

### 3. Serializers
- **Dosya:** `src/api/serializers.py`
- **Amaç:** Request/response validation
- **Özellik:** Type-safe data handling

## 🎯 Kullanım Senaryoları

### Senaryo 1: Frontend'den Direkt API Çağrısı

```
Frontend → Django NLP API → Response
```

**Kullanım:**
```javascript
// Frontend (React/Vue)
const response = await fetch('/api/nlp/process-ocr/', {
  method: 'POST',
  body: JSON.stringify({ ocr_data: {...} })
});
```

**Django:** Sadece URL routing gerekir, başka bir şey yapmanıza gerek yok.

### Senaryo 2: Django View'de İşleme

```
Frontend → Django View → NLP Service → Django View → Response
```

**Kullanım:**
```python
# Django View
from src.api.services import nlp_service

def process_receipt(request):
    ocr_data = request.data.get('ocr_data')
    
    # NLP ile işle
    result = nlp_service.process_ocr_output(ocr_data)
    
    # Database'e kaydet
    Receipt.objects.create(
        ocr_data=ocr_data,
        nlp_result=result,
        intent=result['intent']['primary']
    )
    
    return JsonResponse(result)
```

### Senaryo 3: Asenkron İşleme (Celery)

```
Frontend → Django View → Celery Task → NLP Service
```

**Kullanım:**
```python
# tasks.py
from celery import shared_task
from src.api.services import nlp_service

@shared_task
def process_receipt_async(receipt_id):
    receipt = Receipt.objects.get(id=receipt_id)
    result = nlp_service.process_ocr_output(receipt.ocr_data)
    
    receipt.nlp_result = result
    receipt.save()
    
    return result

# View
def upload_receipt(request):
    receipt = Receipt.objects.create(ocr_data=request.data)
    process_receipt_async.delay(receipt.id)
    return JsonResponse({'status': 'processing', 'id': receipt.id})
```

### Senaryo 4: Django Signal ile Otomatik İşleme

```
Model Save → Signal → NLP Service
```

**Kullanım:**
```python
# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Receipt)
def auto_process(sender, instance, created, **kwargs):
    if created and instance.ocr_data:
        result = nlp_service.process_ocr_output(instance.ocr_data)
        instance.nlp_result = result
        instance.save()
```

## 📊 Veri Akışı Örnekleri

### Örnek 1: Kiracı Dekont Yükleme

```
1. Kiracı PDF yükler
   ↓
2. Frontend → Django Upload View
   ↓
3. Django → OCR Service (başka servis)
   ↓
4. OCR sonuç → Django
   ↓
5. Django → NLP Service (bizim servisimiz)
   ↓
6. NLP sonuç → Database
   ↓
7. Response → Frontend
```

**Kod:**
```python
@api_view(['POST'])
def upload_receipt(request):
    pdf_file = request.FILES['pdf']
    
    # 1. OCR (başka servisiniz)
    ocr_data = your_ocr_service.extract(pdf_file)
    
    # 2. NLP (bizim servisimiz)
    nlp_result = nlp_service.process_ocr_output(ocr_data)
    
    # 3. Save
    receipt = Receipt.objects.create(
        pdf_file=pdf_file,
        ocr_data=ocr_data,
        nlp_result=nlp_result,
        tenant_id=request.user.id
    )
    
    return Response({
        'receipt_id': receipt.id,
        'intent': nlp_result['intent']['primary'],
        'amount': nlp_result['final_entities']['amount']
    })
```

### Örnek 2: Toplu Dekont İşleme

```python
@api_view(['POST'])
def batch_upload(request):
    receipts = request.data['receipts']  # Liste
    
    # Batch processing
    batch_data = {
        'receipts': [
            {'id': r['id'], 'ocr_data': r['ocr_data']}
            for r in receipts
        ]
    }
    
    # NLP API'yi çağır (internal)
    from src.api.views import BatchProcessOCRView
    view = BatchProcessOCRView.as_view()
    
    # VEYA direkt service kullan
    results = []
    for receipt in receipts:
        result = nlp_service.process_ocr_output(receipt['ocr_data'])
        results.append(result)
    
    return Response({'results': results})
```

## 🔐 Güvenlik ve Yetkilendirme

### Authentication

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}

# View'lerde
from rest_framework.permissions import IsAuthenticated

class ProcessOCRView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Sadece authenticated kullanıcılar erişebilir
        ...
```

### Tenant Isolation

```python
# Multi-tenant için
class Receipt(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    # ...

@api_view(['POST'])
def process_receipt(request):
    # Kullanıcının tenant'ı
    tenant = request.user.tenant
    
    result = nlp_service.process_ocr_output(request.data['ocr_data'])
    
    # Tenant ile kaydet
    Receipt.objects.create(
        tenant=tenant,
        nlp_result=result
    )
```

## ⚡ Performans Optimizasyonu

### 1. Model Caching

```python
# Servis zaten singleton + lazy loading kullanıyor
# İlk istekte yüklenir, sonra cached
nlp_service.process_ocr_output(...)  # 10-15s (ilk)
nlp_service.process_ocr_output(...)  # 100-300ms (sonraki)
```

### 2. Async Processing

```python
# Uzun işlemler için Celery kullanın
@shared_task
def process_pdf_async(pdf_path):
    return nlp_service.process_pdf(pdf_path)

# View'de
task = process_pdf_async.delay(pdf_path)
return Response({'task_id': task.id})
```

### 3. Batch Processing

```python
# Tek tek yerine batch kullanın
# ❌ Yavaş
for receipt in receipts:
    nlp_service.process_ocr_output(receipt.ocr_data)

# ✅ Hızlı
from src.api.views import BatchProcessOCRView
# veya direkt servisi liste ile çağırın
```

## 🐛 Hata Yönetimi

### Try-Catch Pattern

```python
from src.api.services import nlp_service

def safe_process(ocr_data):
    try:
        result = nlp_service.process_ocr_output(ocr_data)
        return {'status': 'success', 'data': result}
    
    except ValueError as e:
        # Validation hatası
        return {'status': 'error', 'message': 'Invalid data'}
    
    except Exception as e:
        # Genel hata
        logger.error(f"NLP processing failed: {e}")
        return {'status': 'error', 'message': 'Processing failed'}
```

### Graceful Degradation

```python
def process_receipt(request):
    ocr_data = request.data['ocr_data']
    
    try:
        # NLP ile işle
        result = nlp_service.process_ocr_output(ocr_data)
    except Exception as e:
        # NLP başarısız olsa da OCR'ı kaydet
        logger.warning(f"NLP failed, saving OCR only: {e}")
        result = None
    
    # Her durumda kaydet
    receipt = Receipt.objects.create(
        ocr_data=ocr_data,
        nlp_result=result
    )
    
    return Response({'id': receipt.id})
```

## 📦 Database Schema Önerisi

```python
class Receipt(models.Model):
    """Dekont modeli"""
    # Relations
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True)
    
    # Files
    pdf_file = models.FileField(upload_to='receipts/')
    
    # OCR
    ocr_data = models.JSONField()
    
    # NLP Results
    nlp_result = models.JSONField(null=True)
    intent = models.CharField(max_length=50)  # kira_odemesi, aidat_odemesi, etc.
    confidence = models.FloatField()
    
    # Extracted Entities
    sender_name = models.CharField(max_length=200)
    receiver_name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(null=True)
    apt_no = models.CharField(max_length=20, null=True)
    period = models.CharField(max_length=100, null=True)
    
    # Matching
    matched_owner = models.ForeignKey(Owner, on_delete=models.SET_NULL, null=True)
    match_confidence = models.FloatField(null=True)
    match_status = models.CharField(max_length=20)  # matched, manual, unmatched
    
    # Metadata
    processed_at = models.DateTimeField(auto_now_add=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    verified_at = models.DateTimeField(null=True)
    
    class Meta:
        ordering = ['-processed_at']
        indexes = [
            models.Index(fields=['tenant', '-processed_at']),
            models.Index(fields=['intent', 'match_status']),
        ]
```

## 🧪 Test Örnekleri

### Unit Test

```python
from django.test import TestCase
from src.api.services import nlp_service

class NLPServiceTest(TestCase):
    def test_process_ocr(self):
        ocr_data = {
            'description': 'Haziran kira 5000 TL'
        }
        
        result = nlp_service.process_ocr_output(ocr_data)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['intent']['primary'], 'kira_odemesi')
        self.assertGreater(result['intent']['confidence'], 0.7)
```

### Integration Test

```python
from rest_framework.test import APITestCase

class APIIntegrationTest(APITestCase):
    def test_process_ocr_endpoint(self):
        response = self.client.post('/api/nlp/process-ocr/', {
            'ocr_data': {
                'description': 'Haziran kira 5000 TL'
            }
        }, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('intent', response.data)
```

## 📊 Monitoring

### Logging

```python
import logging

logger = logging.getLogger('nlp_service')

@api_view(['POST'])
def process_receipt(request):
    logger.info(f"Processing receipt for user {request.user.id}")
    
    start_time = time.time()
    result = nlp_service.process_ocr_output(request.data['ocr_data'])
    duration = time.time() - start_time
    
    logger.info(f"Processed in {duration:.2f}s, intent: {result['intent']['primary']}")
    
    return Response(result)
```

### Metrics

```python
from django.db.models import Count, Avg
from datetime import timedelta
from django.utils import timezone

# Günlük istatistikler
today = timezone.now().date()
stats = Receipt.objects.filter(
    processed_at__date=today
).aggregate(
    total=Count('id'),
    avg_confidence=Avg('confidence')
)

# Intent dağılımı
intent_stats = Receipt.objects.values('intent').annotate(
    count=Count('id')
).order_by('-count')
```

## 🚀 Production Checklist

- [ ] Authentication aktif
- [ ] Rate limiting yapılandırıldı
- [ ] CORS ayarları yapıldı
- [ ] Logging aktif
- [ ] Error handling eklendi
- [ ] Database indexler eklendi
- [ ] Celery kuruldu (opsiyonel)
- [ ] Monitoring kuruldu
- [ ] Backup stratejisi var
- [ ] Load testing yapıldı

## 📚 Kaynaklar

- [API Dökümantasyonu](README.md)
- [Hızlı Başlangıç](QUICKSTART.md)
- [Örnek Kodlar](example_integration.py)
- [Django Settings](django_settings_example.py)

## ❓ SSS

### S: Modeller her istekte yükleniyor mu?
C: Hayır, singleton pattern + lazy loading ile ilk istekte yüklenir, sonra cache'lenir.

### S: Birden fazla worker ile çalışır mı?
C: Evet, her worker kendi model instance'ını yükler. RAM kullanımını göz önünde bulundurun.

### S: Asenkron işleme gerekli mi?
C: PDF işleme için önerilir (2-5s). OCR output için gerekli değil (<300ms).

### S: Multi-tenant nasıl yapılır?
C: Her tenant için ayrı Receipt row'u oluşturun, tenant_id ile filtreleyin.

### S: Matching database nereden geliyor?
C: `src/pipeline/database_loader.py` kullanır veya kendi database'inizi bağlayın.
