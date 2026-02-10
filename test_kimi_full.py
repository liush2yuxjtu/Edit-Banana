#!/usr/bin/env python3
"""
全量 Kimi 方案测试脚本
测试 OCR 和公式识别功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()


def test_kimi_client():
    """测试 Kimi 客户端"""
    print("=" * 60)
    print("🧪 Test 1: Kimi Client Initialization")
    print("=" * 60)
    
    try:
        from modules.llm_client import KimiClient
        
        client = KimiClient()
        print(f"✅ KimiClient initialized successfully")
        print(f"   Model: {client.model}")
        print(f"   Base URL: {client.base_url}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_kimi_chat():
    """测试 Kimi 聊天功能"""
    print("\n" + "=" * 60)
    print("🧪 Test 2: Kimi Chat")
    print("=" * 60)
    
    try:
        from modules.llm_client import chat
        
        messages = [
            {"role": "user", "content": "Say 'Hello from Kimi' in 5 words or less."}
        ]
        response = chat(messages, max_tokens=50, temperature=0.7)
        print(f"✅ Chat response: {response}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_ocr_recognizer():
    """测试 OCR 识别器"""
    print("\n" + "=" * 60)
    print("🧪 Test 3: OCR Recognizer")
    print("=" * 60)
    
    try:
        from modules.text.ocr_recognize import KimiOCRRecognizer
        
        recognizer = KimiOCRRecognizer()
        print(f"✅ KimiOCRRecognizer initialized successfully")
        print(f"   Use formulas: {recognizer.use_formulas}")
        print(f"   Min confidence: {recognizer.min_confidence}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_formula_recognizer():
    """测试公式识别器"""
    print("\n" + "=" * 60)
    print("🧪 Test 4: Formula Recognizer")
    print("=" * 60)
    
    try:
        from modules.text.formula_recognize import KimiFormulaRecognizer
        
        recognizer = KimiFormulaRecognizer()
        print(f"✅ KimiFormulaRecognizer initialized successfully")
        
        # 测试公式类型判断
        test_cases = [
            "E = mc^2",
            "\\frac{a}{b}",
            "\\int_0^1 f(x)dx",
            "This is plain text"
        ]
        
        print("   Formula detection tests:")
        for text in test_cases:
            is_formula = recognizer.is_formula(text)
            print(f"     '{text[:20]}...' -> {'Formula' if is_formula else 'Text'}")
        
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_text_restorer():
    """测试 TextRestorer"""
    print("\n" + "=" * 60)
    print("🧪 Test 5: TextRestorer")
    print("=" * 60)
    
    try:
        from modules.text import TextRestorer
        
        config = {
            "use_ocr": True,
            "use_formulas": True,
            "min_confidence": 0.6
        }
        
        restorer = TextRestorer(config=config)
        print(f"✅ TextRestorer initialized successfully")
        print(f"   Use OCR: {restorer.use_ocr}")
        print(f"   Use formulas: {restorer.use_formulas}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_text_module_imports():
    """测试 text 模块导入"""
    print("\n" + "=" * 60)
    print("🧪 Test 6: Text Module Imports")
    print("=" * 60)
    
    try:
        from modules.text import (
            TextRestorer,
            KimiOCRRecognizer,
            OCRResult,
            KimiFormulaRecognizer,
            FormulaResult,
            FormulaType
        )
        print(f"✅ All text module imports successful")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_latex_validation():
    """测试 LaTeX 验证功能"""
    print("\n" + "=" * 60)
    print("🧪 Test 7: LaTeX Validation")
    print("=" * 60)
    
    try:
        from modules.text.formula_recognize import KimiFormulaRecognizer
        
        recognizer = KimiFormulaRecognizer()
        
        # 测试用例
        test_cases = [
            ("$E = mc^2$", True),
            ("$$\\int_0^1 x dx$$", True),
            ("\\frac{a}{b", False),  # 未闭合
            ("Plain text", True),     # 非公式，视为有效
        ]
        
        print("   LaTeX validation tests:")
        for latex, expected in test_cases:
            is_valid, error = recognizer.validate_latex(latex)
            status = "✅" if is_valid == expected else "❌"
            print(f"     {status} '{latex[:20]}...' -> Valid={is_valid}")
        
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "🍌" * 30)
    print("Edit-Banana 全量 Kimi 方案测试")
    print("🍌" * 30 + "\n")
    
    # 检查环境变量
    kimi_key = os.getenv("KIMI_API_KEY")
    if not kimi_key:
        print("⚠️  Warning: KIMI_API_KEY not set in environment")
        print("   Please check your .env file\n")
    else:
        print(f"✅ KIMI_API_KEY is set ({kimi_key[:20]}...)\n")
    
    # 运行测试
    tests = [
        ("Kimi Client", test_kimi_client),
        ("Kimi Chat", test_kimi_chat),
        ("OCR Recognizer", test_ocr_recognizer),
        ("Formula Recognizer", test_formula_recognizer),
        ("Text Restorer", test_text_restorer),
        ("Text Module Imports", test_text_module_imports),
        ("LaTeX Validation", test_latex_validation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Test {name} crashed: {e}")
            results.append((name, False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {name}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 All tests passed! Full Kimi implementation is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
