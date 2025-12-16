#!/bin/bash
# Quick Start Script - NLP Project
# Kullanım: ./run.sh [komut]

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Environment setup
export HF_HOME="./.cache/huggingface"
export TRANSFORMERS_CACHE="./.cache/huggingface"

# Activate virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment bulunamadı!${NC}"
    echo "Oluşturmak için: python3 -m venv .venv"
    exit 1
fi

source .venv/bin/activate

# Function definitions
train_intent() {
    echo -e "${BLUE}🚀 Intent Classification model eğitimi başlıyor...${NC}"
    python src/nlp/train_intent_classifier.py
}

train_ner() {
    echo -e "${BLUE}🚀 NER model eğitimi başlıyor...${NC}"
    python src/nlp/train_ner.py
}

inference() {
    echo -e "${BLUE}🎯 v3 Robust Inference (Hybrid: BERT + Regex)${NC}"
    echo -e "${YELLOW}   → Multi-intent detection ✅${NC}"
    echo -e "${YELLOW}   → Case-insensitive ✅${NC}"
    echo -e "${YELLOW}   → Regex fallback ✅${NC}"
    echo ""
    python src/nlp/v3/inference_robust.py
}

inference_ner() {
    echo -e "${BLUE}🔍 NER Extraction demo çalıştırılıyor...${NC}"
    python src/nlp/v3/inference_ner.py
}

inference_v2() {
    echo -e "${BLUE}🎯 v2 Intent Inference (OCR-Aware)${NC}"
    python src/nlp/v2/inference.py
}

inference_v1() {
    echo -e "${BLUE}🎯 v1 Intent Inference (Basic)${NC}"
    python src/nlp/v1/inference.py
}

generate_data() {
    echo -e "${BLUE}📊 Synthetic data üretiliyor...${NC}"
    python scripts/generate_synthetic_data.py
}

show_results() {
    echo -e "${GREEN}📈 Model Sonuçları:${NC}"
    if [ -f "models/intent_classifier/test_results.json" ]; then
        cat models/intent_classifier/test_results.json | python -m json.tool | grep -E "(accuracy|precision|recall|f1)"
    else
        echo -e "${YELLOW}Model henüz eğitilmedi!${NC}"
    fi
}

show_confusion_matrix() {
    if [ -f "models/intent_classifier/confusion_matrix.png" ]; then
        echo -e "${GREEN}📊 Confusion matrix açılıyor...${NC}"
        open models/intent_classifier/confusion_matrix.png
    else
        echo -e "${YELLOW}Confusion matrix bulunamadı!${NC}"
    fi
}

show_help() {
    echo -e "${GREEN}🚀 NLP Project - Quick Start${NC}"
    echo ""
    echo "Kullanım: ./run.sh [komut]"
    echo ""
    echo "Komutlar:"
    echo ""
    echo "🔥 FULL PIPELINE:"
    echo "  pipeline                          - Full pipeline demo"
    echo "  pipeline-pdf <pdf> [bank] [--match] - Process PDF (add --match for matching)"
    echo "  pipeline-json <json>              - Process OCR JSON"
    echo ""
    echo "🎯 NLP TEST:"
    echo "  test              - v3 Robust inference (BERT+Regex Hybrid)"
    echo "  test-ner          - NER extraction demo"
    echo "  test-v2           - v2 OCR-Aware inference"
    echo "  test-v1           - v1 Basic inference"
    echo ""
    echo "🔧 TRAINING:"
    echo "  train             - Intent classification model eğit"
    echo "  train-ner         - NER model eğit"
    echo "  data              - Synthetic data üret"
    echo "  results           - Model sonuçlarını göster"
    echo "  matrix            - Confusion matrix'i aç"
    echo "  help              - Bu yardım mesajını göster"
    echo ""
    echo "Örnekler:"
    echo "  ./run.sh pipeline-pdf data/halkbank.pdf halkbank"
    echo "  ./run.sh pipeline-pdf data/halkbank.pdf --match     # With matching"
    echo "  ./run.sh test           # v3 Robust test et"
    echo "  ./run.sh test-ner       # NER test et"
    echo "  ./run.sh train          # Intent model eğit"
}

pipeline() {
    echo -e "${BLUE}🚀 Full Pipeline - OCR → Intent + NER → Structured Output${NC}"
    echo -e "${YELLOW}   → Tüm modüller entegre ✅${NC}"
    echo ""
    python src/pipeline/full_pipeline.py
}

pipeline_pdf() {
    if [ -z "$1" ]; then
        echo -e "${RED}❌ PDF path required${NC}"
        echo "Usage: ./run.sh pipeline-pdf <pdf_path> [bank_name] [--match]"
        exit 1
    fi
    
    local pdf_path="$1"
    local bank_name="$2"
    local enable_match=""
    
    # Check for --match flag
    if [ "$2" = "--match" ] || [ "$3" = "--match" ]; then
        enable_match="--enable-matching"
    fi
    
    echo -e "${BLUE}🚀 Processing PDF: $pdf_path${NC}"
    
    if [ -n "$bank_name" ] && [ "$bank_name" != "--match" ]; then
        echo -e "${YELLOW}   Bank: $bank_name${NC}"
        python src/pipeline/cli.py --pdf "$pdf_path" --bank "$bank_name" $enable_match --pretty
    else
        echo -e "${YELLOW}   Auto-detecting bank...${NC}"
        python src/pipeline/cli.py --pdf "$pdf_path" $enable_match --pretty
    fi
}

pipeline_json() {
    if [ -z "$1" ]; then
        echo -e "${RED}❌ OCR JSON path required${NC}"
        echo "Usage: ./run.sh pipeline-json <ocr_json_path>"
        exit 1
    fi
    
    echo -e "${BLUE}🚀 Processing OCR JSON: $1${NC}"
    python src/pipeline/cli.py --ocr-json "$1" --pretty
}

# Main
case "$1" in
    pipeline)
        pipeline
        ;;
    pipeline-pdf)
        pipeline_pdf "$2" "$3"
        ;;
    pipeline-json)
        pipeline_json "$2"
        ;;
    train)
        train_intent
        ;;
    train-ner)
        train_ner
        ;;
    test)
        inference
        ;;
    test-ner)
        inference_ner
        ;;
    test-v2)
        inference_v2
        ;;
    test-v1)
        inference_v1
        ;;
    data)
        generate_data
        ;;
    results)
        show_results
        ;;
    matrix)
        show_confusion_matrix
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo -e "${YELLOW}⚠️  Bilinmeyen komut: $1${NC}"
        show_help
        exit 1
        ;;
esac
