PYTHON ?= .venv/bin/python
PYTHONPATH := src:$(PYTHONPATH)

# OCR Extraction
.PHONY: extract
extract:
	@if [ -z "$(FILE)" ]; then \
		echo "Kullanım: make extract FILE=dosya.pdf [BANK=halkbank]"; \
		exit 1; \
	fi
	@PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m ocr.extraction.cli "$(FILE)" $(if $(BANK),--bank $(BANK),)

# NLP Inference (v3 Robust - Hybrid System)
.PHONY: test-intent
test-intent:
	@echo "🎯 Intent Classification (v3 Robust + Multi-Intent)"
	@PYTHONPATH=$(PYTHONPATH) $(PYTHON) src/nlp/v3/inference_robust.py

.PHONY: analyze
analyze:
	@if [ -z "$(TEXT)" ]; then \
		echo "Kullanım: make analyze TEXT='dekont açıklaması'"; \
		echo ""; \
		echo "Örnek:"; \
		echo "  make analyze TEXT='FATİH DİNDAR DAİRE 9 ÇALIK-2 APART KİRA ÖDEME'"; \
		exit 1; \
	fi
	@PYTHONPATH=$(PYTHONPATH) $(PYTHON) scripts/analyze_text.py "$(TEXT)"

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

# Full Pipeline (OCR → Intent + NER)
.PHONY: pipeline-demo
pipeline-demo:
	@echo "🚀 Full Pipeline Demo..."
	@PYTHONPATH=$(PYTHONPATH) $(PYTHON) src/pipeline/full_pipeline.py

.PHONY: pipeline-pdf
pipeline-pdf:
	@if [ -z "$(PDF)" ]; then \
		echo "❌ Error: PDF parameter required"; \
		echo "Usage: make pipeline-pdf PDF=data/halkbank.pdf [BANK=halkbank] [MATCH=1]"; \
		exit 1; \
	fi
	@echo "🚀 Processing PDF: $(PDF)"
	@if [ -n "$(BANK)" ] && [ "$(MATCH)" = "1" ]; then \
		PYTHONPATH=$(PYTHONPATH) $(PYTHON) src/pipeline/cli.py --pdf "$(PDF)" --bank "$(BANK)" --enable-matching --pretty; \
	elif [ -n "$(BANK)" ]; then \
		PYTHONPATH=$(PYTHONPATH) $(PYTHON) src/pipeline/cli.py --pdf "$(PDF)" --bank "$(BANK)" --pretty; \
	elif [ "$(MATCH)" = "1" ]; then \
		PYTHONPATH=$(PYTHONPATH) $(PYTHON) src/pipeline/cli.py --pdf "$(PDF)" --enable-matching --pretty; \
	else \
		PYTHONPATH=$(PYTHONPATH) $(PYTHON) src/pipeline/cli.py --pdf "$(PDF)" --pretty; \
	fi

.PHONY: pipeline-json
pipeline-json:
	@if [ -z "$(OCR)" ]; then \
		echo "❌ OCR parameter required"; \
		echo "Usage: make pipeline-json OCR=results/ocr_output.json"; \
		exit 1; \
	fi
	@echo "🚀 Processing OCR JSON: $(OCR)"
	@PYTHONPATH=$(PYTHONPATH) $(PYTHON) src/pipeline/cli.py --ocr-json "$(OCR)" --pretty

.PHONY: help
help:
	@echo "╔═══════════════════════════════════════════════════════════╗"
	@echo "║         📋 NLP PROJECT - MAKEFILE COMMANDS               ║"
	@echo "╚═══════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "🔥 FULL PIPELINE:"
	@echo "  make pipeline-demo                              - Run full pipeline demo"
	@echo "  make pipeline-pdf PDF=<pdf> [BANK=<bank>] [MATCH=1] - Process PDF (add MATCH=1 for matching)"
	@echo "  make pipeline-json OCR=<json_path>              - Process OCR JSON"
	@echo ""
	@echo "🔍 OCR:"
	@echo "  make extract FILE=<pdf_path> BANK=<bank_name>   - Extract from receipt"
	@echo ""
	@echo "🎯 NLP:"
	@echo "  make analyze TEXT='<text>'                      - Analyze text"
	@echo "  make test-intent                                - Test intent classifier"
	@echo ""
	@echo "🔗 MATCHING:"
	@echo "  make match RECEIPT=<id>                         - Match receipt"
	@echo ""
	@echo "📚 Examples:"
	@echo "  make pipeline-demo"
	@echo "  make extract FILE=data/Dekont-1.pdf BANK=kuveytturk"
	@echo "  make analyze TEXT='ÇALIK APT DAİRE 9 FATİH DİNDAR KİRA'"

