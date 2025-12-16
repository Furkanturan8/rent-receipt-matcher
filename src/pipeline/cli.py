"""
CLI for Full Pipeline
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pipeline.full_pipeline import ReceiptPipeline


def main():
    parser = argparse.ArgumentParser(
        description='🚀 Full Receipt Processing Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Process PDF directly
  python src/pipeline/cli.py --pdf data/halkbank.pdf --bank halkbank
  
  # Process PDF with auto bank detection
  python src/pipeline/cli.py --pdf data/halkbank.pdf
  
  # Process from OCR JSON
  python src/pipeline/cli.py --ocr-json results/ocr_output.json
  
  # With output file
  python src/pipeline/cli.py --ocr-json results/ocr_output.json --output results/processed.json
  
  # From stdin (pipe OCR output)
  echo '{"sender":"...","description":"..."}' | python src/pipeline/cli.py --stdin
  
  # Run demo
  python src/pipeline/cli.py --demo
        '''
    )
    
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--pdf',
        type=str,
        help='Path to PDF receipt file (direct OCR integration)'
    )
    input_group.add_argument(
        '--ocr-json',
        type=str,
        help='Path to OCR output JSON file'
    )
    input_group.add_argument(
        '--stdin',
        action='store_true',
        help='Read OCR JSON from stdin'
    )
    input_group.add_argument(
        '--demo',
        action='store_true',
        help='Run demo with example data'
    )
    
    # PDF-specific options
    parser.add_argument(
        '--bank',
        type=str,
        choices=['halkbank', 'kuveytturk', 'yapikredi', 'ziraatbank'],
        help='Bank name hint (for PDF processing). If not provided, auto-detect.'
    )
    parser.add_argument(
        '--use-logo-detection',
        action='store_true',
        help='Use hybrid bank detection (text + logo) for PDF processing'
    )
    
    # Matching options
    parser.add_argument(
        '--enable-matching',
        action='store_true',
        help='Enable receipt matching with tenant database'
    )
    parser.add_argument(
        '--mock-db',
        type=str,
        help='Path to mock database JSON (default: tests/mock-data.json)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output JSON path (optional)'
    )
    
    parser.add_argument(
        '--pretty',
        action='store_true',
        help='Pretty print output'
    )
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = ReceiptPipeline(
        enable_matching=args.enable_matching,
        mock_db_path=args.mock_db
    )
    
    # Process
    if args.demo:
        # Run demo
        from src.pipeline.full_pipeline import demo
        demo()
        return
    
    elif args.pdf:
        # Process PDF directly
        print("=" * 80)
        print("📄 PDF MODE - Direct OCR Integration")
        print("=" * 80)
        result = pipeline.process_from_file(
            pdf_path=args.pdf,
            bank=args.bank,
            output_path=args.output,
            use_logo_detection=args.use_logo_detection
        )
    
    elif args.stdin:
        # Read from stdin
        print("📥 Reading OCR output from stdin...")
        ocr_json = sys.stdin.read()
        ocr_data = json.loads(ocr_json)
        result = pipeline.process_ocr_output(ocr_data)
    
    else:
        # Read from file
        result = pipeline.process_from_ocr_json(
            args.ocr_json,
            output_path=args.output
        )
    
    # Output
    if not args.output:
        if args.pretty:
            print("\n" + "="*70)
            print("📋 RESULT:")
            print("="*70)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
