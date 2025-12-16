"""
Rule-based Chatbot for Real Estate Payment Management

Handles payment processing, tenant queries, and conversational responses.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List
from pathlib import Path

from .templates import ResponseTemplates
from ..pipeline.full_pipeline import ReceiptPipeline
from ..pipeline.database_loader import load_mock_database


class RealEstateChatbot:
    """
    Rule-based chatbot for real estate payment management.
    
    Features:
    - Receipt processing with NLP pipeline
    - Payment validation and matching
    - Tenant information queries
    - Template-based responses
    """
    
    def __init__(self, mock_db_path: Optional[str] = None):
        """
        Initialize chatbot.
        
        Args:
            mock_db_path: Path to mock database JSON file
        """
        self.templates = ResponseTemplates()
        self.pipeline = ReceiptPipeline(enable_matching=True, mock_db_path=mock_db_path)
        
        # Load database
        try:
            self.database = load_mock_database(mock_db_path)
        except Exception as e:
            print(f"⚠️  Database yüklenemedi: {e}")
            self.database = {"owners": [], "customers": [], "properties": []}
        
        self.conversation_history: List[Dict[str, str]] = []
    
    def process_receipt(self, pdf_path: str, bank: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a receipt PDF and generate response.
        
        Args:
            pdf_path: Path to receipt PDF file
            bank: Optional bank name hint
        
        Returns:
            Dict with processing result and chatbot response
        """
        try:
            # Process receipt through pipeline
            result = self.pipeline.process_from_file(pdf_path, bank=bank)
            
            # Generate response based on matching result
            response = self._generate_receipt_response(result)
            
            return {
                "success": True,
                "pipeline_result": result,
                "response": response,
                "status": result.get('matching', {}).get('status', 'unknown')
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"❌ Hata: Dekont işlenirken bir sorun oluştu.\n\nDetay: {str(e)}"
            }
    
    def _generate_receipt_response(self, result: Dict[str, Any]) -> str:
        """Generate chatbot response for receipt processing result."""
        intent = result.get('intent', {}).get('primary', 'unknown')
        matching = result.get('matching', {})
        ocr_data = result.get('ocr_data', {})
        
        status = matching.get('status', 'unknown')
        confidence = matching.get('confidence', 0)
        
        # Matched successfully
        if status == 'matched' and confidence >= 70:
            return self._format_success_response(intent, result)
        
        # Low confidence / manual review
        elif status == 'manual_review' or confidence < 70:
            return self._format_manual_review_response(result)
        
        # Rejected / no match
        elif status == 'rejected':
            return self._format_rejection_response(result)
        
        # Unknown status
        else:
            return self.templates.UNKNOWN
    
    def _format_success_response(self, intent: str, result: Dict[str, Any]) -> str:
        """Format successful payment response."""
        ocr_data = result.get('ocr_data', {})
        matching = result.get('matching', {})
        
        # Get matched entities
        owner_id = matching.get('owner_id')
        customer_id = matching.get('customer_id')
        property_id = matching.get('property_id')
        
        # Find entities in database
        owner = next((o for o in self.database['owners'] if o['id'] == owner_id), {})
        customer = next((c for c in self.database['customers'] if c['id'] == customer_id), {})
        property_obj = next((p for p in self.database['properties'] if p['id'] == property_id), {})
        
        data = {
            'sender': ocr_data.get('sender', 'Bilinmiyor'),
            'receiver': ocr_data.get('recipient', 'Bilinmiyor'),
            'amount': ocr_data.get('amount', '0'),
            'currency': ocr_data.get('amount_currency', 'TRY'),
            'date': ocr_data.get('date', 'Bilinmiyor'),
            'apt_no': property_obj.get('address', 'Bilinmiyor').split()[-1] if property_obj else 'Bilinmiyor',
            'period': result.get('ner', {}).get('entities', {}).get('period', 'Bilinmiyor'),
            'owner_name': owner.get('full_name', 'Bilinmiyor'),
            'customer_name': customer.get('full_name', 'Bilinmiyor'),
            'property_address': property_obj.get('address', 'Bilinmiyor'),
            'confidence': f"{matching.get('confidence', 0):.1f}"
        }
        
        return self.templates.format_payment_confirmed(intent, data)
    
    def _format_manual_review_response(self, result: Dict[str, Any]) -> str:
        """Format manual review response."""
        ocr_data = result.get('ocr_data', {})
        matching = result.get('matching', {})
        
        # Extract info
        extracted_info = (
            f"   • Gönderen: {ocr_data.get('sender', 'Bilinmiyor')}\n"
            f"   • Alıcı: {ocr_data.get('recipient', 'Bilinmiyor')}\n"
            f"   • Tutar: {ocr_data.get('amount', '0')} {ocr_data.get('amount_currency', 'TRY')}\n"
            f"   • Tarih: {ocr_data.get('date', 'Bilinmiyor')}"
        )
        
        # Get issues
        messages = matching.get('messages', [])
        issues = '\n'.join(f"   • {msg}" for msg in messages) if messages else "   • Eşleşme yapılamadı"
        
        data = {
            'confidence': f"{matching.get('confidence', 0):.1f}",
            'extracted_info': extracted_info,
            'issues': issues
        }
        
        return self.templates.format_manual_review(data)
    
    def _format_rejection_response(self, result: Dict[str, Any]) -> str:
        """Format rejection response."""
        ocr_data = result.get('ocr_data', {})
        
        data = {
            'sender': ocr_data.get('sender', 'Bilinmiyor'),
            'receiver': ocr_data.get('recipient', 'Bilinmiyor'),
            'amount': ocr_data.get('amount', '0'),
            'currency': ocr_data.get('amount_currency', 'TRY'),
            'date': ocr_data.get('date', 'Bilinmiyor')
        }
        
        return self.templates.format_payment_error('no_match', data)
    
    def query_tenant_info(self, tenant_name: Optional[str] = None, tenant_id: Optional[int] = None) -> str:
        """
        Query tenant/owner information.
        
        Args:
            tenant_name: Person name to search (customer or owner)
            tenant_id: Person ID to search
        
        Returns:
            Formatted person information
        """
        # Search in both customers and owners
        person = None
        person_type = None
        
        if tenant_id:
            # Try customers first
            person = next((c for c in self.database['customers'] if c['id'] == tenant_id), None)
            if person:
                person_type = 'customer'
            else:
                # Try owners
                person = next((o for o in self.database['owners'] if o['id'] == tenant_id), None)
                if person:
                    person_type = 'owner'
        elif tenant_name:
            # Try customers first
            person = next(
                (c for c in self.database['customers'] 
                 if tenant_name.upper() in c.get('full_name', '').upper()),
                None
            )
            if person:
                person_type = 'customer'
            else:
                # Try owners
                person = next(
                    (o for o in self.database['owners'] 
                     if tenant_name.upper() in o.get('full_name', '').upper()),
                    None
                )
                if person:
                    person_type = 'owner'
        else:
            return "❌ Lütfen kişi adını belirtin."
        
        if not person:
            return self.templates.TENANT_NOT_FOUND.format(search_term=tenant_name or tenant_id)
        
        # If it's a customer (tenant), find their property
        if person_type == 'customer':
            property_obj = next(
                (p for p in self.database['properties'] if p.get('customer_id') == person['id']),
                None
            )
            
            if not property_obj:
                return f"❌ {person.get('full_name')} için mülk kaydı bulunamadı."
            
            # Find owner
            owner = next(
                (o for o in self.database['owners'] if o['id'] == property_obj.get('owner_id')),
                {}
            )
            
            return self.templates.TENANT_INFO.format(
                full_name=person.get('full_name', 'Bilinmiyor'),
                email=person.get('email', 'Bilinmiyor'),
                phone=person.get('phone', 'Bilinmiyor'),
                property_address=property_obj.get('address', 'Bilinmiyor'),
                apt_no=property_obj.get('address', '').split()[-1] if property_obj else 'Bilinmiyor',
                rent_amount=property_obj.get('price', 0),
                owner_name=owner.get('full_name', 'Bilinmiyor'),
                owner_iban=owner.get('iban', 'Bilinmiyor'),
                payment_day='5'  # Default
            )
        
        # If it's an owner, show their properties
        else:
            properties = [p for p in self.database['properties'] if p.get('owner_id') == person['id']]
            
            if not properties:
                return f"❌ {person.get('full_name')} için mülk kaydı bulunamadı."
            
            # Format owner info
            result = f"""
👤 **{person.get('full_name', 'Bilinmiyor')} - Mülk Sahibi Bilgileri**

📧 **İletişim:**
   • Email: {person.get('email', 'Bilinmiyor')}
   • Telefon: {person.get('phone', 'Bilinmiyor')}
   • IBAN: {person.get('iban', 'Bilinmiyor')}

🏢 **Mülkleri ({len(properties)} adet):**
"""
            
            for idx, prop in enumerate(properties, 1):
                # Find tenant for this property
                tenant = next(
                    (c for c in self.database.get('customers', []) if c.get('id') == prop.get('customer_id')),
                    None
                )
                
                result += f"""
   {idx}. **{prop.get('title', 'Bilinmiyor')}**
      • Adres: {prop.get('address', 'Bilinmiyor')}
      • Kira: {prop.get('price', 0):,} TRY
      • Kiracı: {tenant.get('full_name', 'Boş') if tenant else 'Boş'}
"""
            
            return result
    
    def _extract_name_from_message(self, message: str) -> Optional[str]:
        """
        Extract person name from message using pattern matching.
        
        Args:
            message: User message
        
        Returns:
            Extracted name or None
        """
        import re
        
        # Normalize Turkish characters for matching
        message_normalized = message.upper()
        for tr_char, en_char in [("İ", "I"), ("Ş", "S"), ("Ğ", "G"), ("Ü", "U"), ("Ö", "O"), ("Ç", "C")]:
            message_normalized = message_normalized.replace(tr_char, en_char)
        
        # Try to match against known customers
        for customer in self.database.get('customers', []):
            customer_name = customer.get('full_name', '')
            customer_normalized = customer_name.upper()
            for tr_char, en_char in [("İ", "I"), ("Ş", "S"), ("Ğ", "G"), ("Ü", "U"), ("Ö", "O"), ("Ç", "C")]:
                customer_normalized = customer_normalized.replace(tr_char, en_char)
            
            # Check if customer name is in message
            if customer_normalized in message_normalized:
                return customer_name
            
            # Check for partial matches (first name or last name)
            name_parts = customer_normalized.split()
            for part in name_parts:
                if len(part) > 3 and part in message_normalized:
                    return customer_name
        
        # Pattern matching for Turkish names (if not found in database)
        # Try to extract capitalized words that look like names
        patterns = [
            r'([A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)+)',  # "Furkan Turan"
            r'([A-ZÇĞİÖŞÜ]{2,}(?:\s+[A-ZÇĞİÖŞÜ]{2,})+)',  # "FURKAN TURAN"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, message)
            if matches:
                return matches[0]
        
        return None
    
    def _detect_intent(self, message: str) -> str:
        """
        Detect user intent from message.
        
        Args:
            message: User message
        
        Returns:
            Intent string
        """
        message_lower = message.lower()
        
        # Intent keywords
        if any(word in message_lower for word in ['yardım', 'help', 'komut']):
            return 'help'
        
        elif any(word in message_lower for word in ['merhaba', 'selam', 'hoş geldin', 'hey', 'hi']):
            return 'greeting'
        
        elif any(word in message_lower for word in ['güle güle', 'hoşça kal', 'çık', 'bye']):
            return 'goodbye'
        
        elif any(word in message_lower for word in ['geçmiş ödeme', 'ödeme geçmiş', 'ödemeleri göster', 'ödeme listesi']):
            return 'payment_history'
        
        elif any(word in message_lower for word in ['ödeme durumu', 'durum', 'ödendiğini', 'ödendi mi']):
            return 'payment_status'
        
        elif any(word in message_lower for word in ['kiracı', 'kişi', 'hakkında', 'kimdir', 'kim', 'bilgi', 'getir']):
            return 'tenant_info'
        
        elif any(word in message_lower for word in ['liste', 'kiracılar', 'müşteriler']):
            return 'tenant_list'
        
        else:
            return 'unknown'
    
    def _query_payment_history(self, tenant_name: str) -> str:
        """Query payment history for a tenant."""
        # Find customer (search in customers only, not owners)
        customer = next(
            (c for c in self.database.get('customers', [])
             if tenant_name.upper() in c.get('full_name', '').upper()),
            None
        )
        
        if not customer:
            return self.templates.TENANT_NOT_FOUND.format(search_term=tenant_name)
        
        # Find property
        property_obj = next(
            (p for p in self.database.get('properties', [])
             if p.get('customer_id') == customer['id']),
            None
        )
        
        if not property_obj:
            return f"❌ {tenant_name} için mülk kaydı bulunamadı."
        
        # Mock payment records (in real system, query from payment history table)
        payment_records = """   • Kasım 2024: ✅ Ödendi (140 TRY) - 05/11/2024
   • Ekim 2024: ✅ Ödendi (140 TRY) - 05/10/2024
   • Eylül 2024: ✅ Ödendi (140 TRY) - 05/09/2024"""
        
        return self.templates.PAYMENT_HISTORY.format(
            tenant_name=tenant_name,
            full_name=customer.get('full_name', 'Bilinmiyor'),
            property_address=property_obj.get('address', 'Bilinmiyor'),
            rent_amount=property_obj.get('price', 0),
            payment_records=payment_records,
            total_payments=3,
            last_payment_date='05/11/2024',
            payment_status='✅ Düzenli Ödüyor'
        )
    
    def _query_payment_status(self, tenant_name: str, period: Optional[str] = None) -> str:
        """Query payment status for a specific period."""
        # Find customer (search in customers only, not owners)
        customer = next(
            (c for c in self.database.get('customers', [])
             if tenant_name.upper() in c.get('full_name', '').upper()),
            None
        )
        
        if not customer:
            return self.templates.TENANT_NOT_FOUND.format(search_term=tenant_name)
        
        # Find property
        property_obj = next(
            (p for p in self.database.get('properties', [])
             if p.get('customer_id') == customer['id']),
            None
        )
        
        if not property_obj:
            return f"❌ {tenant_name} için mülk kaydı bulunamadı."
        
        # Extract period from message or use current month
        if not period:
            from datetime import datetime
            period = datetime.now().strftime('%B %Y')  # e.g., "November 2024"
            # Convert to Turkish
            month_tr = {
                'January': 'Ocak', 'February': 'Şubat', 'March': 'Mart',
                'April': 'Nisan', 'May': 'Mayıs', 'June': 'Haziran',
                'July': 'Temmuz', 'August': 'Ağustos', 'September': 'Eylül',
                'October': 'Ekim', 'November': 'Kasım', 'December': 'Aralık'
            }
            for en, tr in month_tr.items():
                period = period.replace(en, tr)
        
        # Mock status (in real system, query from payments table)
        status = "✅ Ödendi"
        payment_date = "05/11/2024"
        amount = property_obj.get('price', 0)
        notes = "💡 Ödeme zamanında ve eksiksiz yapılmıştır."
        
        return self.templates.PAYMENT_STATUS.format(
            tenant_name=tenant_name,
            full_name=customer.get('full_name', 'Bilinmiyor'),
            property_address=property_obj.get('address', 'Bilinmiyor'),
            rent_amount=property_obj.get('price', 0),
            period=period,
            status=status,
            payment_date=payment_date,
            amount=amount,
            notes=notes
        )
    
    def _list_tenants(self) -> str:
        """List all tenants."""
        customers = self.database.get('customers', [])
        
        if not customers:
            return "❌ Veritabanında kiracı kaydı bulunamadı."
        
        result = "📋 **Kiracı Listesi**\n\n"
        
        for customer in customers:
            # Find property
            property_obj = next(
                (p for p in self.database.get('properties', [])
                 if p.get('customer_id') == customer['id']),
                None
            )
            
            result += f"👤 **{customer.get('full_name', 'Bilinmiyor')}**\n"
            result += f"   • Mülk: {property_obj.get('address', 'Bilinmiyor') if property_obj else 'Yok'}\n"
            result += f"   • Kira: {property_obj.get('price', 0) if property_obj else 0} TRY\n"
            result += f"   • İletişim: {customer.get('email', 'Bilinmiyor')}\n\n"
        
        return result
    
    def handle_message(self, message: str) -> str:
        """
        Handle user message and generate response.
        
        Args:
            message: User's text message
        
        Returns:
            Chatbot response
        """
        message_lower = message.lower().strip()
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": message})
        
        # Detect intent
        intent = self._detect_intent(message)
        
        # Extract name if present
        extracted_name = self._extract_name_from_message(message)
        
        # Handle based on intent
        if intent == 'help':
            response = self.templates.HELP_MENU
        
        elif intent == 'greeting':
            response = self.templates.WELCOME
        
        elif intent == 'goodbye':
            response = self.templates.GOODBYE
        
        elif intent == 'payment_history':
            if extracted_name:
                response = self._query_payment_history(extracted_name)
            else:
                response = "❓ Lütfen kiracı adını belirtin.\nÖrnek: 'Furkan Turan geçmiş ödemelerini göster'"
        
        elif intent == 'payment_status':
            if extracted_name:
                # Try to extract period (e.g., "Kasım ayı")
                import re
                period_match = re.search(r'(ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık)\s*(?:ayı)?', message_lower)
                period = period_match.group(1).capitalize() + " 2024" if period_match else None
                response = self._query_payment_status(extracted_name, period)
            else:
                response = "❓ Lütfen kiracı adını belirtin.\nÖrnek: 'Furkan Turan ödeme durumu'"
        
        elif intent == 'tenant_info':
            if extracted_name:
                response = self.query_tenant_info(tenant_name=extracted_name)
            else:
                response = "❓ Lütfen kiracı adını belirtin.\nÖrnek: 'Furkan Turan kimdir?'"
        
        elif intent == 'tenant_list':
            response = self._list_tenants()
        
        else:
            response = self.templates.UNKNOWN
        
        # Add to history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
    
    def get_welcome_message(self) -> str:
        """Get welcome message."""
        return self.templates.WELCOME
    
    def get_help_message(self) -> str:
        """Get help menu."""
        return self.templates.HELP_MENU


__all__ = ["RealEstateChatbot"]
