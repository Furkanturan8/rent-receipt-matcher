"""
PDF'lerden logo ve görsel tabanlı banka tespiti yapan modül.

PDF'den görselleri çıkarır, referans logolar ile karşılaştırarak bankayı tespit eder.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import cv2
    import numpy as np
    from PIL import Image

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


# Referans logoların saklanacağı dizin
LOGO_DIR = Path(__file__).parent.parent.parent.parent / "assets" / "logos"

# Her banka için logo dosya adları
BANK_LOGOS: Dict[str, List[str]] = {
    "halkbank": ["halkbank_logo.png", "halkbank_logo.jpg"],
    "yapikredi": ["yapikredi_logo.png", "yapikredi_logo.jpg"],
    "kuveytturk": ["kuveytturk_logo.png", "kuveytturk_logo.jpg"],
    "ziraatbank": ["ziraatbank_logo.png", "ziraatbank_logo.jpg"],
    "vakifbank": ["vakifbank_logo.png", "vakifbank_logo.jpg"],
}


def extract_images_from_pdf(pdf_path: str | Path) -> List[np.ndarray]:
    """
    PDF'den görselleri çıkarır.

    Parametreler:
        pdf_path: PDF dosyasının yolu.

    Dönen:
        Görsel dizilerinin listesi (numpy array formatında).
    """
    if not PYMUPDF_AVAILABLE:
        return []

    images = []
    pdf_document = fitz.open(pdf_path)

    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        image_list = page.get_images(full=True)

        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]

                # PIL Image'a dönüştür
                image = Image.open(io.BytesIO(image_bytes))
                # RGB formatına çevir
                if image.mode != "RGB":
                    image = image.convert("RGB")

                # NumPy array'e dönüştür
                img_array = np.array(image)
                images.append(img_array)
            except Exception:
                # Görsel çıkarılamazsa devam et
                continue

    pdf_document.close()
    return images


def load_reference_logo(bank_name: str) -> Optional[np.ndarray]:
    """
    Referans logo dosyasını yükler.

    Parametreler:
        bank_name: Banka adı (ör. "halkbank").

    Dönen:
        Logo görseli (numpy array) veya None.
    """
    if not CV2_AVAILABLE:
        return None

    logo_files = BANK_LOGOS.get(bank_name, [])
    for logo_file in logo_files:
        logo_path = LOGO_DIR / logo_file
        if logo_path.exists():
            try:
                img = cv2.imread(str(logo_path))
                if img is not None:
                    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            except Exception:
                continue
    return None


def template_match(image: np.ndarray, template: np.ndarray, threshold: float = 0.6) -> float:
    """
    Template matching kullanarak görsel benzerliğini hesaplar.

    Parametreler:
        image: Aranacak görsel (PDF'den çıkarılan).
        template: Referans logo (template).
        threshold: Minimum benzerlik eşiği (0-1 arası).

    Dönen:
        Benzerlik skoru (0-1 arası).
    """
    if not CV2_AVAILABLE:
        return 0.0

    try:
        # Görselleri gri tonlamaya çevir
        img_gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
        template_gray = cv2.cvtColor(template, cv2.COLOR_RGB2GRAY) if len(template.shape) == 3 else template

        # Template görseli, ana görselden büyük olamaz
        if template_gray.shape[0] > img_gray.shape[0] or template_gray.shape[1] > img_gray.shape[1]:
            return 0.0

        # Template matching yap
        result = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        return float(max_val)
    except Exception:
        return 0.0


def detect_bank_from_logos(pdf_path: str | Path, threshold: float = 0.6) -> Optional[str]:
    """
    PDF'den çıkarılan logoları kullanarak bankayı tespit eder.

    Parametreler:
        pdf_path: PDF dosyasının yolu.
        threshold: Minimum benzerlik eşiği (varsayılan: 0.6).

    Dönen:
        Tespit edilen banka adı veya None.
    """
    if not CV2_AVAILABLE or not PYMUPDF_AVAILABLE:
        return None

    # PDF'den görselleri çıkar
    images = extract_images_from_pdf(pdf_path)
    if not images:
        return None

    bank_scores: Dict[str, float] = {}

    # Her banka için referans logoyu yükle ve karşılaştır
    for bank_name in BANK_LOGOS.keys():
        reference_logo = load_reference_logo(bank_name)
        if reference_logo is None:
            continue

        best_match = 0.0
        for image in images:
            match_score = template_match(image, reference_logo, threshold)
            best_match = max(best_match, match_score)

        if best_match >= threshold:
            bank_scores[bank_name] = best_match

    if not bank_scores:
        return None

    # En yüksek skorlu bankayı döndür
    best_bank = max(bank_scores.items(), key=lambda x: x[1])[0]
    return best_bank


def detect_bank_from_logos_with_confidence(
    pdf_path: str | Path, threshold: float = 0.6
) -> Tuple[Optional[str], float]:
    """
    Logo tabanlı banka tespiti yapar ve güven skoru döndürür.

    Parametreler:
        pdf_path: PDF dosyasının yolu.
        threshold: Minimum benzerlik eşiği.

    Dönen:
        (banka_adı, güven_skoru) tuple'ı.
    """
    if not CV2_AVAILABLE or not PYMUPDF_AVAILABLE:
        return None, 0.0

    images = extract_images_from_pdf(pdf_path)
    if not images:
        return None, 0.0

    bank_scores: Dict[str, float] = {}

    for bank_name in BANK_LOGOS.keys():
        reference_logo = load_reference_logo(bank_name)
        if reference_logo is None:
            continue

        best_match = 0.0
        for image in images:
            match_score = template_match(image, reference_logo, threshold)
            best_match = max(best_match, match_score)

        if best_match >= threshold:
            bank_scores[bank_name] = best_match

    if not bank_scores:
        return None, 0.0

    best_bank, best_score = max(bank_scores.items(), key=lambda x: x[1])

    # Güven skoru: Benzerlik skorunun normalleştirilmiş hali
    # 0.6-0.7 arası düşük güven, 0.7-0.8 arası orta, 0.8+ yüksek güven
    if best_score >= 0.8:
        confidence = 1.0
    elif best_score >= 0.7:
        confidence = 0.8
    else:
        confidence = 0.6

    return best_bank, confidence


__all__ = [
    "detect_bank_from_logos",
    "detect_bank_from_logos_with_confidence",
    "extract_images_from_pdf",
    "load_reference_logo",
    "template_match",
    "BANK_LOGOS",
    "LOGO_DIR",
]

