"""
OCR regex tabanlı alan çıkarma aracının komut satırı arayüzü.

Kullanım örneği:

    python -m ocr.extraction.cli data/halkbank.pdf --bank halkbank
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pdfminer.high_level import extract_text

from .bank_detector import detect_bank, detect_bank_hybrid
from .extractor import extract_fields


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OCR metinlerinden alan çıkarımı yapan yardımcı araç."
    )
    parser.add_argument(
        "pdf_path",
        help="İşlenecek PDF dosyasının yolu.",
        type=Path,
    )
    parser.add_argument(
        "--bank",
        help="Banka ipucu (ör. halkbank, vakifbank). Opsiyonel. Belirtilmezse otomatik tespit edilir.",
        default=None,
    )
    parser.add_argument(
        "--no-auto-detect",
        action="store_true",
        help="Otomatik banka tespitini devre dışı bırak.",
    )
    parser.add_argument(
        "--use-logo-detection",
        action="store_true",
        help="Logo tabanlı banka tespitini de kullan (hibrit mod).",
    )
    parser.add_argument(
        "--ensure-ascii",
        action="store_true",
        help="Çıktıyı ASCII karakterlerle sınırla.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    pdf_path: Path = args.pdf_path
    if not pdf_path.is_file():
        print(f"Hata: '{pdf_path}' dosyası bulunamadı.", file=sys.stderr)
        return 1

    text = extract_text(str(pdf_path))
    
    # Eğer banka belirtilmemişse ve otomatik tespit aktifse, bankayı tespit et
    bank_hint = args.bank
    if not bank_hint and not args.no_auto_detect:
        if args.use_logo_detection:
            # Hibrit yaklaşım: hem metin hem logo
            detected_bank = detect_bank_hybrid(text, pdf_path=pdf_path)
            detection_method = "hibrit (metin + logo)"
        else:
            # Sadece metin tabanlı tespit
            detected_bank = detect_bank(text)
            detection_method = "metin"
        
        if detected_bank:
            bank_hint = detected_bank
            # Kullanıcıya bilgi ver
            print(f"# Tespit edilen banka: {detected_bank} ({detection_method})", file=sys.stderr)
    
    fields = extract_fields(text, bank_hint=bank_hint)

    json_kwargs = {
        "ensure_ascii": args.ensure_ascii,
        "indent": 2,
    }
    print(json.dumps(fields, **json_kwargs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


