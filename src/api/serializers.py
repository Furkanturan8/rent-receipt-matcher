"""
Django REST Framework Serializers
"""
from rest_framework import serializers


class OCRDataSerializer(serializers.Serializer):
    """OCR output data serializer"""
    sender = serializers.CharField(required=False, allow_blank=True)
    sender_iban = serializers.CharField(required=False, allow_blank=True)
    recipient = serializers.CharField(required=False, allow_blank=True)
    receiver_iban = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=True)
    amount = serializers.CharField(required=False, allow_blank=True)
    amount_currency = serializers.CharField(required=False, default='TRY')
    date = serializers.CharField(required=False, allow_blank=True)
    bank = serializers.CharField(required=False, allow_blank=True)


class ProcessOCRRequestSerializer(serializers.Serializer):
    """Request serializer for OCR processing"""
    ocr_data = OCRDataSerializer(required=True)
    enable_matching = serializers.BooleanField(default=False)


class ProcessPDFRequestSerializer(serializers.Serializer):
    """Request serializer for PDF processing"""
    pdf_file = serializers.FileField(required=True)
    bank = serializers.ChoiceField(
        choices=['halkbank', 'kuveytturk', 'yapikredi', 'ziraatbank'],
        required=False,
        allow_blank=True
    )
    enable_matching = serializers.BooleanField(default=False)
    use_logo_detection = serializers.BooleanField(default=False)


class IntentResultSerializer(serializers.Serializer):
    """Intent classification result"""
    primary = serializers.CharField()
    confidence = serializers.FloatField()
    all_intents = serializers.ListField()
    is_multi_intent = serializers.BooleanField()
    detected_intents = serializers.ListField()


class NERResultSerializer(serializers.Serializer):
    """NER extraction result"""
    entities = serializers.DictField()
    extraction_method = serializers.DictField()
    confidence_scores = serializers.DictField()
    bert_entities = serializers.DictField()
    regex_entities = serializers.DictField()


class MatchingResultSerializer(serializers.Serializer):
    """Receipt matching result"""
    status = serializers.CharField()
    confidence = serializers.FloatField()
    owner_id = serializers.CharField(allow_null=True)
    customer_id = serializers.CharField(allow_null=True)
    property_id = serializers.CharField(allow_null=True)
    scores = serializers.DictField()
    messages = serializers.ListField()


class ProcessingResponseSerializer(serializers.Serializer):
    """Processing response serializer"""
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
    ocr_data = serializers.DictField()
    intent = IntentResultSerializer()
    ner = NERResultSerializer()
    final_entities = serializers.DictField()
    summary = serializers.CharField()
    matching = MatchingResultSerializer(required=False)


class ErrorResponseSerializer(serializers.Serializer):
    """Error response serializer"""
    error = serializers.CharField()
    detail = serializers.CharField(required=False)
    status = serializers.CharField(default='error')


class HealthCheckResponseSerializer(serializers.Serializer):
    """Health check response"""
    status = serializers.CharField()
    models_loaded = serializers.BooleanField()
    service = serializers.CharField()
    version = serializers.CharField()
