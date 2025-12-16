"""
Dekont eşleştirme ana modülü.

OCR çıktısını database kayıtlarıyla eşleştirir.
Mock data'daki öncelik sırasına göre implement edilmiştir.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .fuzzy import address_similarity, name_similarity
from .normalizers import normalize_amount, normalize_iban, normalize_name


@dataclass
class ReceiptMatchResult:
    """Dekont eşleştirme sonucu."""
    
    # Eşleşen kayıtlar
    owner_id: Optional[int] = None
    customer_id: Optional[int] = None
    property_id: Optional[int] = None
    
    # Eşleştirme durumu
    match_status: str = "pending"  # pending, matched, manual_review, rejected
    confidence_score: float = 0.0  # 0-100 arası
    
    # Eşleştirme detayları
    matching_details: Dict[str, Any] = field(default_factory=dict)
    
    # Her kriter için skorlar
    iban_match_score: float = 0.0
    amount_match_score: float = 0.0
    name_match_score: float = 0.0
    address_match_score: float = 0.0
    sender_match_score: float = 0.0
    
    # Eşleştirme mesajları
    messages: List[str] = field(default_factory=list)


# Mock data'daki öncelik sırası ve güven skorları
MATCHING_CRITERIA = {
    "iban": {"priority": 1, "weight": 95, "threshold": 0.95},
    "amount": {"priority": 2, "weight": 85, "threshold": 0.80},
    "name": {"priority": 3, "weight": 75, "threshold": 0.70},
    "address": {"priority": 4, "weight": 70, "threshold": 0.60},
    "sender": {"priority": 5, "weight": 60, "threshold": 0.60},
}


def match_receipt(
    ocr_data: Dict[str, Any],
    owners: List[Dict[str, Any]],
    customers: List[Dict[str, Any]],
    properties: List[Dict[str, Any]],
    min_confidence: float = 70.0,
) -> ReceiptMatchResult:
    """
    OCR çıktısını database kayıtlarıyla eşleştirir.
    
    Mock data'daki öncelik sırasına göre:
    1. IBAN eşleşmesi (güven: 95)
    2. Tutar eşleşmesi (güven: 85, ±%5 tolerans)
    3. İsim benzerliği (güven: 75)
    4. Adres bilgisi (güven: 70)
    5. Gönderen bilgisi (güven: 60)
    
    Parametreler:
        ocr_data: OCR'dan çıkarılan veri (extract_fields çıktısı).
        owners: Mülk sahipleri listesi.
        customers: Müşteriler listesi.
        properties: Mülkler listesi.
        min_confidence: Minimum güven skoru (varsayılan: 70).
    
    Dönen:
        ReceiptMatchResult objesi.
    """
    result = ReceiptMatchResult()
    result.matching_details = {
        "ocr_data": ocr_data,
        "criteria_scores": {},
        "candidates": [],
    }
    
    # OCR verilerini normalize et
    receiver_iban = normalize_iban(ocr_data.get("receiver_account") or ocr_data.get("receiver_iban", ""))
    receiver_name = normalize_name(ocr_data.get("receiver_name") or ocr_data.get("recipient", ""))
    sender_name = normalize_name(ocr_data.get("sender_name") or ocr_data.get("sender", ""))
    amount = normalize_amount(ocr_data.get("amount_text") or ocr_data.get("amount", ""))
    description = ocr_data.get("description", "")
    
    # Aday kayıtları bul
    candidates = _find_candidates(
        receiver_iban=receiver_iban,
        receiver_name=receiver_name,
        amount=amount,
        description=description,
        owners=owners,
        properties=properties,
    )
    
    if not candidates:
        result.messages.append("Eşleşen kayıt bulunamadı")
        result.match_status = "manual_review"
        return result
    
    # En iyi eşleşmeyi bul
    best_match = None
    best_score = 0.0
    
    for candidate in candidates:
        scores = _calculate_match_scores(
            ocr_data=ocr_data,
            receiver_iban=receiver_iban,
            receiver_name=receiver_name,
            sender_name=sender_name,
            amount=amount,
            description=description,
            owner=candidate["owner"],
            property_obj=candidate.get("property"),
            customers=customers,
        )
        
        # Toplam güven skorunu hesapla
        total_score = _calculate_total_confidence(scores)
        candidate["total_score"] = total_score
        candidate["scores"] = scores
        # Customer ID'yi candidate'a ekle
        if "_customer_id" in scores:
            candidate["customer_id"] = scores["_customer_id"]
        
        if total_score > best_score:
            best_score = total_score
            best_match = candidate
        
        # Debug: skorları kaydet
        result.matching_details["criteria_scores"][f"candidate_{len(result.matching_details.get('candidates', []))}"] = {
            "owner_id": candidate["owner"]["id"],
            "property_id": candidate.get("property", {}).get("id"),
            "scores": scores,
            "total_score": total_score,
        }
    
    # Güven skoru 0-100 arası olmalı
    best_score_percent = best_score  # Zaten 0-100 arası hesaplanıyor
    
    if best_match and best_score_percent >= min_confidence:
        # Eşleştirme başarılı
        result.owner_id = best_match["owner"]["id"]
        result.property_id = best_match.get("property", {}).get("id")
        result.customer_id = best_match.get("customer_id")
        result.confidence_score = best_score_percent
        
        # Skorları kaydet
        scores = best_match.get("scores", {})
        result.iban_match_score = scores.get("iban", 0.0)
        result.amount_match_score = scores.get("amount", 0.0)
        result.name_match_score = scores.get("name", 0.0)
        result.address_match_score = scores.get("address", 0.0)
        result.sender_match_score = scores.get("sender", 0.0)
        
        result.matching_details["best_match"] = best_match
        result.matching_details["all_candidates"] = candidates
        
        if best_score_percent >= 90:
            result.match_status = "matched"
            result.messages.append(f"Yüksek güvenle eşleştirildi (skor: {best_score_percent:.1f}/100)")
        else:
            result.match_status = "matched"
            result.messages.append(f"Eşleştirildi (skor: {best_score_percent:.1f}/100)")
    else:
        # Manuel inceleme gerekli
        result.match_status = "manual_review"
        if best_match:
            result.owner_id = best_match["owner"]["id"]
            result.property_id = best_match.get("property", {}).get("id")
            result.customer_id = best_match.get("customer_id")
            result.confidence_score = best_score_percent
            
            # Skorları kaydet
            scores = best_match.get("scores", {})
            result.iban_match_score = scores.get("iban", 0.0)
            result.amount_match_score = scores.get("amount", 0.0)
            result.name_match_score = scores.get("name", 0.0)
            result.address_match_score = scores.get("address", 0.0)
            result.sender_match_score = scores.get("sender", 0.0)
            
            result.messages.append(f"Düşük güven skoru (skor: {best_score_percent:.1f}/100), manuel inceleme gerekli")
        else:
            result.messages.append("Eşleşen kayıt bulunamadı")
    
    return result


def _find_candidates(
    receiver_iban: str,
    receiver_name: str,
    amount: Optional[float],
    description: str,
    owners: List[Dict[str, Any]],
    properties: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """IBAN veya isim bazlı aday kayıtları bulur."""
    candidates = []
    
    for owner in owners:
        owner_iban = normalize_iban(owner.get("iban", ""))
        owner_name = normalize_name(owner.get("full_name", ""))
        
        # IBAN eşleşmesi varsa direkt ekle
        if receiver_iban and owner_iban and receiver_iban == owner_iban:
            # Bu owner'a ait property'leri bul
            owner_properties = [p for p in properties if p.get("owner_id") == owner["id"]]
            
            if owner_properties:
                for prop in owner_properties:
                    candidates.append({
                        "owner": owner,
                        "property": prop,
                        "match_reason": "iban_exact",
                    })
            else:
                candidates.append({
                    "owner": owner,
                    "match_reason": "iban_exact",
                })
        
        # İsim benzerliği yüksekse ekle
        elif receiver_name and owner_name:
            similarity = name_similarity(receiver_name, owner_name)
            if similarity >= 0.7:
                owner_properties = [p for p in properties if p.get("owner_id") == owner["id"]]
                for prop in owner_properties:
                    candidates.append({
                        "owner": owner,
                        "property": prop,
                        "match_reason": f"name_similarity_{similarity:.2f}",
                    })
    
    return candidates


def _calculate_match_scores(
    ocr_data: Dict[str, Any],
    receiver_iban: str,
    receiver_name: str,
    sender_name: str,
    amount: Optional[float],
    description: str,
    owner: Dict[str, Any],
    property_obj: Optional[Dict[str, Any]],
    customers: List[Dict[str, Any]],
) -> Dict[str, float]:
    """Her kriter için skorları hesaplar."""
    scores = {
        "iban": 0.0,
        "amount": 0.0,
        "name": 0.0,
        "address": 0.0,
        "sender": 0.0,
    }
    
    # 1. IBAN eşleşmesi
    owner_iban = normalize_iban(owner.get("iban", ""))
    if receiver_iban and owner_iban:
        if receiver_iban == owner_iban:
            scores["iban"] = 1.0
        else:
            # Kısmi eşleşme (son 4 hanesi gibi)
            if len(receiver_iban) >= 4 and len(owner_iban) >= 4:
                if receiver_iban[-4:] == owner_iban[-4:]:
                    scores["iban"] = 0.5
    
    # 2. Tutar eşleşmesi
    if amount and property_obj:
        property_price = property_obj.get("price")
        if property_price:
            # ±%5 tolerans
            tolerance = property_price * 0.05
            diff = abs(amount - property_price)
            if diff <= tolerance:
                scores["amount"] = 1.0 - (diff / tolerance) * 0.2  # 0.8-1.0 arası
            elif diff <= tolerance * 2:
                scores["amount"] = 0.5
    
    # 3. İsim benzerliği
    owner_name = normalize_name(owner.get("full_name", ""))
    if receiver_name and owner_name:
        scores["name"] = name_similarity(receiver_name, owner_name)
    
    # 4. Adres bilgisi
    if description and property_obj:
        property_address = property_obj.get("address", "")
        if property_address:
            scores["address"] = address_similarity(description, property_address)
    
    # 5. Gönderen bilgisi (Customer eşleşmesi)
    best_customer_id = None
    if sender_name:
        for customer in customers:
            customer_name = normalize_name(customer.get("full_name", ""))
            if customer_name:
                similarity = name_similarity(sender_name, customer_name)
                if similarity > scores["sender"]:
                    scores["sender"] = similarity
                    best_customer_id = customer.get("id")
    
    # Customer ID'yi scores'a ekle (result'a aktarmak için)
    if best_customer_id is not None:
        scores["_customer_id"] = best_customer_id
    
    # _customer_id'yi scores'tan çıkar (sadece internal kullanım için)
    # Ama döndürmeden önce kopyala
    return scores


def _calculate_total_confidence(scores: Dict[str, float]) -> float:
    """
    Toplam güven skorunu hesaplar (ağırlıklı ortalama).
    
    Skor 0-100 arası döner (mock data'daki gibi).
    """
    total_weight = 0.0
    weighted_sum = 0.0
    
    for criterion, score in scores.items():
        if criterion in MATCHING_CRITERIA:
            weight = MATCHING_CRITERIA[criterion]["weight"]
            total_weight += weight
            # Score 0-1 arası, weight 0-100 arası
            # Sonuç 0-100 arası olmalı
            weighted_sum += score * weight
    
    if total_weight == 0:
        return 0.0
    
    # Ağırlıklı ortalama
    # weighted_sum: 0-385 arası (tüm kriterler maksimum)
    # total_weight: 385 (tüm ağırlıkların toplamı)
    # Sonuç: 0-1 arası, 100 ile çarpıp 0-100 yap
    normalized_score = weighted_sum / total_weight
    return normalized_score * 100.0


__all__ = [
    "match_receipt",
    "ReceiptMatchResult",
    "MATCHING_CRITERIA",
]

