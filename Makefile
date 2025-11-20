PYTHON ?= .venv/bin/python
PYTHONPATH := src:$(PYTHONPATH)

.PHONY: extract
extract:
	@if [ -z "$(FILE)" ]; then \
		echo "Kullanım: make extract FILE=dosya.pdf [BANK=halkbank]"; \
		exit 1; \
	fi
	@PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m ocr.extraction.cli "$(FILE)" $(if $(BANK),--bank $(BANK),)

.PHONY: match
match:
	@if [ -z "$(FILE)" ] && [ -z "$(RECEIPT)" ] && [ -z "$(OCR_JSON)" ]; then \
		echo "Dekont Eşleştirme Komutu"; \
		echo ""; \
		echo "Kullanım:"; \
		echo "  make match FILE=dosya.pdf                    # PDF'den OCR yap ve eşleştir"; \
		echo "  make match RECEIPT=DEKONT_001               # Mock data'dan eşleştir"; \
		echo "  make match OCR_JSON=output.json             # OCR JSON'dan eşleştir"; \
		echo ""; \
		echo "Parametreler:"; \
		echo "  MOCK=tests/mock-data.json                   # Mock data dosyası (varsayılan: tests/mock-data.json)"; \
		echo "  MIN_CONF=70                                 # Minimum güven skoru (varsayılan: 70)"; \
		echo ""; \
		echo "Örnekler:"; \
		echo "  make match RECEIPT=DEKONT_006"; \
		echo "  make match FILE=data/ziraatbank.pdf"; \
		echo "  make match RECEIPT=DEKONT_001 MIN_CONF=80"; \
		exit 1; \
	fi
	@if [ -n "$(FILE)" ]; then \
		PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m ocr.matching.cli --pdf "$(FILE)" $(if $(MOCK),--mock-data $(MOCK),) $(if $(MIN_CONF),--min-confidence $(MIN_CONF),) $(if $(JSON),--json,); \
	elif [ -n "$(OCR_JSON)" ]; then \
		PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m ocr.matching.cli --ocr-json "$(OCR_JSON)" $(if $(MOCK),--mock-data $(MOCK),) $(if $(MIN_CONF),--min-confidence $(MIN_CONF),) $(if $(JSON),--json,); \
	elif [ -n "$(RECEIPT)" ]; then \
		PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m ocr.matching.cli --receipt-id "$(RECEIPT)" $(if $(MOCK),--mock-data $(MOCK),) $(if $(MIN_CONF),--min-confidence $(MIN_CONF),) $(if $(JSON),--json,); \
	fi


