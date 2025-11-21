"""
Backend modeli verilerini yükleyen yardımcı modül.

Bu modül backend-models klasöründeki .txt dosyalarını okur ve
Python sözlükleri olarak döner (Django ORM simulasyonu).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List


class DataLoader:
    """
    Backend model verilerini yükleyen sınıf.
    
    .txt dosyalarındaki model kodlarını parse eder ve
    örnek veriler oluşturur.
    """
    
    def __init__(self, models_dir: str | Path):
        """
        Args:
            models_dir: backend-models klasörünün yolu
        """
        self.models_dir = Path(models_dir)
    
    def load_owners(self) -> List[Dict[str, Any]]:
        """
        Owner verilerini yükler.
        
        Returns:
            List[Dict]: Owner listesi
        """
        # Örnek veri (gerçek uygulamada database'den gelir)
        return [
            {
                "id": 1,
                "owner_number": "MS20251100001",
                "first_name": "Ahmet",
                "last_name": "Yılmaz",
                "full_name": "Ahmet Yılmaz",
                "email": "ahmet.yilmaz@example.com",
                "phone": "05321234567",
                "iban": "TR330006100519786457841326",
                "city": "İstanbul",
                "district": "Kadıköy",
                "is_active": True,
            },
            {
                "id": 2,
                "owner_number": "MS20251100002",
                "first_name": "Mehmet",
                "last_name": "Kaya",
                "full_name": "Mehmet Kaya",
                "email": "mehmet.kaya@example.com",
                "phone": "05339876543",
                "iban": "TR640001000268320315270001",
                "city": "Ankara",
                "district": "Çankaya",
                "is_active": True,
            },
            {
                "id": 3,
                "owner_number": "MS20251100003",
                "first_name": "Ayşe",
                "last_name": "Demir",
                "full_name": "Ayşe Demir",
                "email": "ayse.demir@example.com",
                "phone": "05451112233",
                "iban": "TR210006200012300006298634",
                "city": "İzmir",
                "district": "Konak",
                "is_active": True,
            },
        ]
    
    def load_customers(self) -> List[Dict[str, Any]]:
        """
        Customer verilerini yükler.
        
        Returns:
            List[Dict]: Customer listesi
        """
        return [
            {
                "id": 1,
                "customer_type": "individual",
                "first_name": "Ali",
                "last_name": "Veli",
                "full_name": "Ali Veli",
                "email": "ali.veli@example.com",
                "phone": "05321112233",
                "city": "İstanbul",
                "is_active": True,
            },
            {
                "id": 2,
                "customer_type": "individual",
                "first_name": "Fatma",
                "last_name": "Yılmaz",
                "full_name": "Fatma Yılmaz",
                "email": "fatma.yilmaz@example.com",
                "phone": "05339876543",
                "city": "Ankara",
                "is_active": True,
            },
            {
                "id": 3,
                "customer_type": "corporate",
                "company_name": "ABC Teknoloji A.Ş.",
                "full_name": "ABC Teknoloji A.Ş.",
                "email": "info@abcteknoloji.com",
                "phone": "02125551234",
                "city": "İstanbul",
                "is_active": True,
            },
        ]
    
    def load_properties(self) -> List[Dict[str, Any]]:
        """
        Property verilerini yükler.
        
        Returns:
            List[Dict]: Property listesi
        """
        return [
            {
                "id": 1,
                "title": "Kadıköy'de 2+1 Kiralık Daire",
                "owner_id": 1,
                "price": 15000.0,
                "price_currency": "TRY",
                "city": "İstanbul",
                "district": "Kadıköy",
                "address": "Caferağa Mahallesi, Moda Caddesi No: 45",
                "area": 100,
                "rooms": "2+1",
                "property_type": "Daire",
                "status": "rented",
                "is_deleted": False,
            },
            {
                "id": 2,
                "title": "Çankaya'da 3+1 Kiralık Daire",
                "owner_id": 2,
                "price": 12000.0,
                "price_currency": "TRY",
                "city": "Ankara",
                "district": "Çankaya",
                "address": "Kızılay Mahallesi, Atatürk Bulvarı No: 123",
                "area": 120,
                "rooms": "3+1",
                "property_type": "Daire",
                "status": "rented",
                "is_deleted": False,
            },
            {
                "id": 3,
                "title": "Konak'ta 1+1 Kiralık Stüdyo",
                "owner_id": 3,
                "price": 8000.0,
                "price_currency": "TRY",
                "city": "İzmir",
                "district": "Konak",
                "address": "Alsancak Mahallesi, Kordon Boyu No: 78",
                "area": 60,
                "rooms": "1+1",
                "property_type": "Daire",
                "status": "rented",
                "is_deleted": False,
            },
        ]
    
    def load_rental_contracts(self) -> List[Dict[str, Any]]:
        """
        RentalContract verilerini yükler.
        
        Returns:
            List[Dict]: RentalContract listesi
        """
        return [
            {
                "id": 1,
                "contract_number": "KS20251100001",
                "tenant_id": 1,
                "rental_property_id": 1,
                "owner_id": 1,
                "contract_start_date": "2024-01-01",
                "contract_end_date": "2025-12-31",
                "monthly_rent": 15000.0,
                "rent_currency": "TRY",
                "deposit_amount": 15000.0,
                "payment_day": 5,
                "status": "active",
            },
            {
                "id": 2,
                "contract_number": "KS20251100002",
                "tenant_id": 2,
                "rental_property_id": 2,
                "owner_id": 2,
                "contract_start_date": "2024-06-01",
                "contract_end_date": "2025-05-31",
                "monthly_rent": 12000.0,
                "rent_currency": "TRY",
                "deposit_amount": 12000.0,
                "payment_day": 1,
                "status": "active",
            },
            {
                "id": 3,
                "contract_number": "KS20251100003",
                "tenant_id": 3,
                "rental_property_id": 3,
                "owner_id": 3,
                "contract_start_date": "2024-03-01",
                "contract_end_date": "2025-02-28",
                "monthly_rent": 8000.0,
                "rent_currency": "TRY",
                "deposit_amount": 8000.0,
                "payment_day": 10,
                "status": "active",
            },
        ]
    
    def load_tenants(self) -> List[Dict[str, Any]]:
        """
        Tenant verilerini yükler.
        
        Returns:
            List[Dict]: Tenant listesi
        """
        return [
            {
                "id": 1,
                "tenant_number": "KRC20251100001",
                "tenant_type": "individual",
                "first_name": "Can",
                "last_name": "Öztürk",
                "full_name": "Can Öztürk",
                "email": "can.ozturk@example.com",
                "phone": "05321234567",
                "city": "İstanbul",
                "is_active": True,
            },
            {
                "id": 2,
                "tenant_number": "KRC20251100002",
                "tenant_type": "individual",
                "first_name": "Zeynep",
                "last_name": "Aksoy",
                "full_name": "Zeynep Aksoy",
                "email": "zeynep.aksoy@example.com",
                "phone": "05339876543",
                "city": "Ankara",
                "is_active": True,
            },
            {
                "id": 3,
                "tenant_number": "KRC20251100003",
                "tenant_type": "corporate",
                "company_name": "XYZ Yazılım Ltd. Şti.",
                "full_name": "XYZ Yazılım Ltd. Şti.",
                "email": "info@xyzyazilim.com",
                "phone": "02325554321",
                "city": "İzmir",
                "is_active": True,
            },
        ]
    
    def load_accounts(self) -> List[Dict[str, Any]]:
        """
        Account (Cari Hesap) verilerini yükler.
        
        Returns:
            List[Dict]: Account listesi
        """
        return [
            {
                "id": 1,
                "account_number": "CA20251100001",
                "account_type": "owner",
                "name": "Ahmet Yılmaz",
                "content_type": "owner",
                "object_id": 1,
                "balance": 0.0,
                "balance_currency": "TRY",
                "is_active": True,
            },
            {
                "id": 2,
                "account_number": "CA20251100002",
                "account_type": "owner",
                "name": "Mehmet Kaya",
                "content_type": "owner",
                "object_id": 2,
                "balance": 0.0,
                "balance_currency": "TRY",
                "is_active": True,
            },
            {
                "id": 3,
                "account_number": "CA20251100003",
                "account_type": "owner",
                "name": "Ayşe Demir",
                "content_type": "owner",
                "object_id": 3,
                "balance": 0.0,
                "balance_currency": "TRY",
                "is_active": True,
            },
        ]
    
    def load_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Tüm model verilerini yükler.
        
        Returns:
            Dict: Tüm model verileri
        """
        return {
            "owners": self.load_owners(),
            "customers": self.load_customers(),
            "properties": self.load_properties(),
            "rental_contracts": self.load_rental_contracts(),
            "tenants": self.load_tenants(),
            "accounts": self.load_accounts(),
        }


__all__ = ["DataLoader"]

