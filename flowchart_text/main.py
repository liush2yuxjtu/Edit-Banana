#!/usr/bin/env python3
"""
OCR & Text Extraction — entry point for text-only pipeline.
全量 Kimi 方案：使用 Kimi 视觉模型进行 OCR 和公式识别

Reads an image, runs OCR and formula recognition, writes DrawIO XML for text layers.
Used by the full pipeline; can also be run standalone for text-only output.

Usage:
    python flowchart_text/main.py -i input/diagram.png -o output/
    python flowchart_text/main.py -i input/diagram.png
    python flowchart_text/main.py -i input/diagram.png --formula
    python flowchart_text/main.py -i input/diagram.png --confidence 0.7
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# Use shared text pipeline
from modules.text.restorer import TextRestorer


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="OCR & text extraction to DrawIO XML (Full Kimi Implementation)"
    )
    parser.add_argument("-i", "--input", required=True, help="Input image path")
    parser.add_argument("-o", "--output", default="./output", help="Output directory")
    parser.add_argument(
        "--formula", 
        action="store_true",
        help="Enable formula recognition (default: True in full Kimi mode)"
    )
    parser.add_argument(
        "--no-formula",
        action="store_true",
        help="Disable formula recognition"
    )
    parser.add_argument(
        "--confidence", 
        type=float, 
        default=0.6,
        help="Minimum confidence threshold (default: 0.6)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ Error: file not found {args.input}")
        sys.exit(1)

    os.makedirs(args.output, exist_ok=True)
    
    # 配置
    use_formulas = not args.no_formula
    
    config = {
        "use_ocr": True,
        "use_formulas": use_formulas,
        "min_confidence": args.confidence,
        "default_font_size": 14,
        "default_font_family": "Arial"
    }
    
    if args.debug:
        print(f"📝 Configuration: {config}")
        print(f"🔑 Kimi API Key: {'Set' if os.getenv('KIMI_API_KEY') else 'Not Set'}")
        print(f"🌐 Kimi Base URL: {os.getenv('KIMI_BASE_URL', 'https://api.kimi.com/coding/')}")
    
    try:
        print("🚀 Initializing TextRestorer (Full Kimi Mode)...")
        restorer = TextRestorer(config=config)
        
        print(f"📖 Processing image: {args.input}")
        xml_content = restorer.process(args.input)
        
        out_path = os.path.join(args.output, "text_only.drawio")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(xml_content)
        
        print(f"✅ Text XML written: {out_path}")
        
        # 输出统计信息
        if args.debug:
            # 统计文字数量
            ocr_results = restorer.recognize_text(args.input)
            formula_count = sum(1 for r in ocr_results if r.is_formula)
            print(f"📊 Statistics:")
            print(f"   - Total text regions: {len(ocr_results)}")
            print(f"   - Formulas detected: {formula_count}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        if args.debug:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
