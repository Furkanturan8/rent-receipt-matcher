"""
Fuzzy matching ve benzerlik hesaplama fonksiyonları.

Levenshtein distance ve Jaccard similarity kullanır.
"""

from __future__ import annotations

from typing import List, Tuple


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    İki string arasındaki Levenshtein distance'ı hesaplar.
    
    Parametreler:
        s1: İlk string.
        s2: İkinci string.
    
    Dönen:
        Levenshtein distance (0 = aynı, daha büyük = daha farklı).
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def levenshtein_similarity(s1: str, s2: str) -> float:
    """
    Levenshtein distance'a göre benzerlik skoru (0-1 arası).
    
    Parametreler:
        s1: İlk string.
        s2: İkinci string.
    
    Dönen:
        Benzerlik skoru (1.0 = aynı, 0.0 = tamamen farklı).
    """
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    
    distance = levenshtein_distance(s1, s2)
    return 1.0 - (distance / max_len)


def jaccard_similarity(s1: str, s2: str, n_gram: int = 2) -> float:
    """
    Jaccard similarity hesaplar (n-gram bazlı).
    
    Parametreler:
        s1: İlk string.
        s2: İkinci string.
        n_gram: N-gram boyutu (varsayılan: 2, bigram).
    
    Dönen:
        Jaccard similarity skoru (0-1 arası).
    """
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    
    def get_ngrams(text: str, n: int) -> set:
        """String'den n-gram'ları çıkarır."""
        if len(text) < n:
            return {text}
        return {text[i:i+n] for i in range(len(text) - n + 1)}
    
    set1 = get_ngrams(s1.lower(), n_gram)
    set2 = get_ngrams(s2.lower(), n_gram)
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    if union == 0:
        return 1.0
    
    return intersection / union


def name_similarity(name1: str, name2: str) -> float:
    """
    İsim benzerliği hesaplar (Levenshtein + Jaccard hibrit).
    
    Parametreler:
        name1: İlk isim.
        name2: İkinci isim.
    
    Dönen:
        Hibrit benzerlik skoru (0-1 arası).
    """
    if not name1 or not name2:
        return 0.0
    
    # Her iki yöntemi de kullan ve ortalamasını al
    lev_sim = levenshtein_similarity(name1, name2)
    jac_sim = jaccard_similarity(name1, name2)
    
    # Ağırlıklı ortalama (Levenshtein daha önemli)
    return (lev_sim * 0.6 + jac_sim * 0.4)


def extract_address_keywords(address: str) -> List[str]:
    """
    Adres metninden önemli keywords çıkarır (mahalle, sokak, daire no).
    
    Parametreler:
        address: Adres metni.
    
    Dönen:
        Keywords listesi.
    """
    if not address:
        return []
    
    keywords = []
    address_upper = address.upper()
    
    # Mahalle, sokak, cadde, daire, kat gibi önemli kelimeleri bul
    patterns = [
        r"([A-ZÇĞİÖŞÜ\s]+)\s+MAH[\.]?",
        r"([A-ZÇĞİÖŞÜ\s]+)\s+SOK[\.]?",
        r"([A-ZÇĞİÖŞÜ\s]+)\s+CAD[\.]?",
        r"DAİRE[:\s]*([0-9]+)",
        r"KAT[:\s]*([0-9]+)",
        r"NO[:\s]*([0-9]+)",
    ]
    
    import re
    for pattern in patterns:
        matches = re.findall(pattern, address_upper)
        keywords.extend([m.strip() for m in matches if m.strip()])
    
    return keywords


def address_similarity(address1: str, address2: str) -> float:
    """
    İki adres arasındaki benzerliği hesaplar (keyword bazlı).
    
    Parametreler:
        address1: İlk adres.
        address2: İkinci adres.
    
    Dönen:
        Benzerlik skoru (0-1 arası).
    """
    if not address1 or not address2:
        return 0.0
    
    keywords1 = set(extract_address_keywords(address1))
    keywords2 = set(extract_address_keywords(address2))
    
    if not keywords1 and not keywords2:
        # Keyword yoksa, genel Levenshtein kullan
        return levenshtein_similarity(address1, address2)
    
    if not keywords1 or not keywords2:
        return 0.0
    
    # Jaccard similarity
    intersection = len(keywords1 & keywords2)
    union = len(keywords1 | keywords2)
    
    if union == 0:
        return 0.0
    
    return intersection / union


__all__ = [
    "levenshtein_distance",
    "levenshtein_similarity",
    "jaccard_similarity",
    "name_similarity",
    "address_similarity",
    "extract_address_keywords",
]

