#!/usr/bin/env python3
"""
Kimi OCR 测试套件
测试 OCR 功能、公式识别和端到端流程
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))


class TestKimiClient(unittest.TestCase):
    """测试 Kimi 客户端"""
    
    def setUp(self):
        """测试前置"""
        # 模拟环境变量
        self.env_patcher = patch.dict(os.environ, {
            "ANTHROPIC_API_KEY": "test-api-key",
            "KIMI_BASE_URL": "https://api.kimi.com/coding/"
        })
        self.env_patcher.start()
    
    def tearDown(self):
        """测试后置"""
        self.env_patcher.stop()
    
    @patch('modules.kimi_client.ANTHROPIC_AVAILABLE', True)
    @patch('modules.kimi_client.anthropic')
    def test_kimi_client_init(self, mock_anthropic):
        """测试客户端初始化"""
        from modules.kimi_client import KimiClient
        
        # 创建客户端
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        
        client = KimiClient(api_key="test-key", model="kimi-k2-5")
        
        # 验证属性
        self.assertEqual(client.api_key, "test-key")
        self.assertEqual(client.model, "kimi-k2-5")
        self.assertEqual(client.max_tokens, 4096)
        
        print("✓ KimiClient 初始化测试通过")
    
    @patch('modules.kimi_client.ANTHROPIC_AVAILABLE', True)
    @patch('modules.kimi_client.anthropic')
    def test_kimi_client_from_env(self, mock_anthropic):
        """测试从环境变量初始化"""
        from modules.kimi_client import KimiClient
        
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        
        client = KimiClient()
        
        self.assertEqual(client.api_key, "test-api-key")
        print("✓ KimiClient 环境变量初始化测试通过")
    
    def test_text_block_dataclass(self):
        """测试 TextBlock 数据类"""
        from modules.kimi_client import TextBlock
        
        block = TextBlock(
            text="测试文本",
            x=0.1,
            y=0.2,
            width=0.3,
            height=0.05,
            confidence=0.95
        )
        
        self.assertEqual(block.text, "测试文本")
        self.assertEqual(block.x, 0.1)
        self.assertEqual(block.confidence, 0.95)
        
        # 测试 to_dict
        data = block.to_dict()
        self.assertEqual(data["text"], "测试文本")
        self.assertEqual(data["x"], 0.1)
        
        print("✓ TextBlock 数据类测试通过")
    
    def test_formula_result_dataclass(self):
        """测试 FormulaResult 数据类"""
        from modules.kimi_client import FormulaResult
        
        result = FormulaResult(latex="$E = mc^2$", confidence=0.95)
        
        self.assertEqual(result.latex, "$E = mc^2$")
        self.assertEqual(result.confidence, 0.95)
        
        print("✓ FormulaResult 数据类测试通过")


class TestKimiOCR(unittest.TestCase):
    """测试 Kimi OCR 模块"""
    
    def setUp(self):
        """测试前置"""
        self.env_patcher = patch.dict(os.environ, {
            "ANTHROPIC_API_KEY": "test-api-key"
        })
        self.env_patcher.start()
    
    def tearDown(self):
        """测试后置"""
        self.env_patcher.stop()
    
    def test_ocr_result_dataclass(self):
        """测试 OCRResult 数据类"""
        from modules.text.kimi_ocr import OCRResult, TextBlock
        
        blocks = [
            TextBlock("文本1", 0.1, 0.1, 0.2, 0.05, 0.9),
            TextBlock("文本2", 0.1, 0.2, 0.2, 0.05, 0.85)
        ]
        
        result = OCRResult(
            text_blocks=blocks,
            raw_text="原始响应",
            image_path="/test/image.png"
        )
        
        self.assertEqual(len(result.text_blocks), 2)
        self.assertEqual(result.image_path, "/test/image.png")
        
        # 测试 to_text
        text = result.to_text()
        self.assertIn("文本1", text)
        self.assertIn("文本2", text)
        
        # 测试 to_dict
        data = result.to_dict()
        self.assertEqual(len(data["text_blocks"]), 2)
        
        print("✓ OCRResult 数据类测试通过")
    
    def test_kimi_ocr_init(self):
        """测试 KimiOCR 初始化"""
        from modules.text.kimi_ocr import KimiOCR
        
        with patch('modules.text.kimi_ocr.get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            
            ocr = KimiOCR(min_confidence=0.7)
            
            self.assertEqual(ocr.min_confidence, 0.7)
            self.assertIsNotNone(ocr.ocr_prompt)
            
        print("✓ KimiOCR 初始化测试通过")
    
    def test_filter_by_confidence(self):
        """测试置信度过滤"""
        from modules.text.kimi_ocr import OCRResult, TextBlock
        
        blocks = [
            TextBlock("高置信度", 0.1, 0.1, 0.2, 0.05, 0.9),
            TextBlock("低置信度", 0.1, 0.2, 0.2, 0.05, 0.4),
            TextBlock("中置信度", 0.1, 0.3, 0.2, 0.05, 0.7)
        ]
        
        result = OCRResult(text_blocks=blocks, raw_text="", image_path="")
        filtered = result.filter_by_confidence(min_confidence=0.6)
        
        self.assertEqual(len(filtered), 2)
        self.assertTrue(all(b.confidence >= 0.6 for b in filtered))
        
        print("✓ 置信度过滤测试通过")


class TestKimiFormula(unittest.TestCase):
    """测试 Kimi 公式识别模块"""
    
    def setUp(self):
        """测试前置"""
        self.env_patcher = patch.dict(os.environ, {
            "ANTHROPIC_API_KEY": "test-api-key"
        })
        self.env_patcher.start()
    
    def tearDown(self):
        """测试后置"""
        self.env_patcher.stop()
    
    def test_formula_dataclass(self):
        """测试 Formula 数据类"""
        from modules.text.kimi_formula import Formula
        
        formula = Formula(
            latex="$E = mc^2$",
            confidence=0.95,
            bbox={"x": 0.1, "y": 0.1, "width": 0.3, "height": 0.1}
        )
        
        self.assertEqual(formula.latex, "$E = mc^2$")
        self.assertTrue(formula.is_valid())
        
        # 测试转换为行内格式
        inline = formula.to_inline_latex()
        self.assertIn("$", inline)
        
        print("✓ Formula 数据类测试通过")
    
    def test_formula_recognition_result(self):
        """测试公式识别结果"""
        from modules.text.kimi_formula import Formula, FormulaRecognitionResult
        
        formulas = [
            Formula("$E = mc^2$", 0.95),
            Formula("$$\\int_a^b f(x)dx$$", 0.9)
        ]
        
        result = FormulaRecognitionResult(
            formulas=formulas,
            raw_response="原始响应",
            image_path="/test/formula.png"
        )
        
        self.assertEqual(len(result.formulas), 2)
        
        # 测试 get_latex_list
        latex_list = result.get_latex_list()
        self.assertEqual(len(latex_list), 2)
        
        print("✓ FormulaRecognitionResult 测试通过")
    
    def test_validate_latex(self):
        """测试 LaTeX 验证"""
        from modules.text.kimi_formula import KimiFormulaRecognizer
        
        with patch('modules.text.kimi_formula.get_client'):
            recognizer = KimiFormulaRecognizer()
            
            # 有效的 LaTeX
            self.assertTrue(recognizer.validate_latex("$E = mc^2$"))
            self.assertTrue(recognizer.validate_latex("$$\\int_a^b x dx$$"))
            
            # 无效的 LaTeX
            self.assertFalse(recognizer.validate_latex("普通文本"))
            self.assertFalse(recognizer.validate_latex("$未闭合"))
        
        print("✓ LaTeX 验证测试通过")


class TestModuleImports(unittest.TestCase):
    """测试模块导入"""
    
    def test_import_kimi_client(self):
        """测试导入 KimiClient"""
        try:
            from modules import KimiClient, TextBlock, FormulaResult
            self.assertTrue(True)
            print("✓ modules 包导入测试通过")
        except ImportError as e:
            self.fail(f"导入失败: {e}")
    
    def test_import_text_modules(self):
        """测试导入文本处理模块"""
        try:
            from modules.text import KimiOCR, KimiFormulaRecognizer
            self.assertTrue(True)
            print("✓ modules.text 包导入测试通过")
        except ImportError as e:
            self.fail(f"导入失败: {e}")


class TestEndToEnd(unittest.TestCase):
    """端到端集成测试"""
    
    def setUp(self):
        """测试前置"""
        self.env_patcher = patch.dict(os.environ, {
            "ANTHROPIC_API_KEY": "test-api-key"
        })
        self.env_patcher.start()
    
    def tearDown(self):
        """测试后置"""
        self.env_patcher.stop()
    
    @patch('modules.kimi_client.ANTHROPIC_AVAILABLE', True)
    @patch('modules.kimi_client.anthropic')
    def test_ocr_pipeline(self, mock_anthropic):
        """测试 OCR 流程"""
        from modules.text.kimi_ocr import KimiOCR
        
        # 模拟客户端响应
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"text_blocks": [{"text": "测试文本", "x": 0.1, "y": 0.1, "width": 0.2, "height": 0.05, "confidence": 0.95}]}')]
        
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.Anthropic.return_value = mock_client
        
        # 创建临时测试图片
        from PIL import Image
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            # 创建简单测试图片
            img = Image.new('RGB', (100, 100), color='white')
            img.save(f.name)
            temp_path = f.name
        
        try:
            # 创建 OCR 实例并测试
            ocr = KimiOCR()
            result = ocr.recognize(temp_path)
            
            self.assertIsNotNone(result)
            self.assertEqual(result.image_path, temp_path)
            
            print("✓ OCR 流程测试通过")
            
        finally:
            os.unlink(temp_path)


def create_test_image():
    """创建测试图片"""
    from PIL import Image, ImageDraw, ImageFont
    
    # 创建白色背景
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    
    # 添加一些文本
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except:
        font = ImageFont.load_default()
    
    draw.text((50, 50), "Hello World", fill='black', font=font)
    draw.text((50, 100), "测试文本", fill='black', font=font)
    
    # 添加简单公式
    draw.text((50, 150), "E = mc^2", fill='black', font=font)
    
    return img


def run_integration_test():
    """运行集成测试（需要真实 API Key）"""
    print("\n" + "="*60)
    print("运行集成测试（需要真实 API Key）")
    print("="*60)
    
    # 检查是否有 API Key
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("KIMI_API_KEY")
    if not api_key:
        print("⚠️  未设置 API Key，跳过集成测试")
        print("   请设置 ANTHROPIC_API_KEY 或 KIMI_API_KEY 环境变量")
        return
    
    try:
        from modules.text.kimi_ocr import KimiOCR
        from modules.text.kimi_formula import KimiFormulaRecognizer
        from PIL import Image
        import tempfile
        
        # 创建测试图片
        test_img = create_test_image()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            test_img.save(f.name)
            temp_path = f.name
        
        try:
            # 测试 OCR
            print("\n1. 测试 OCR 识别...")
            ocr = KimiOCR()
            ocr_result = ocr.recognize(temp_path)
            print(f"   识别到 {len(ocr_result.text_blocks)} 个文本块")
            for i, block in enumerate(ocr_result.text_blocks[:3]):
                print(f"   - 文本: {block.text[:30]}... 置信度: {block.confidence:.2f}")
            
            # 测试公式识别
            print("\n2. 测试公式识别...")
            formula = KimiFormulaRecognizer()
            formula_result = formula.recognize(temp_path)
            print(f"   识别到 {len(formula_result.formulas)} 个公式")
            for i, f in enumerate(formula_result.formulas[:3]):
                print(f"   - 公式: {f.latex[:50]}... 置信度: {f.confidence:.2f}")
            
            print("\n✓ 集成测试通过！")
            
        finally:
            os.unlink(temp_path)
            
    except Exception as e:
        print(f"\n❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("="*60)
    print("Kimi OCR 测试套件")
    print("="*60)
    
    # 运行单元测试
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestKimiClient))
    suite.addTests(loader.loadTestsFromTestCase(TestKimiOCR))
    suite.addTests(loader.loadTestsFromTestCase(TestKimiFormula))
    suite.addTests(loader.loadTestsFromTestCase(TestModuleImports))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEnd))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    print(f"测试总数: {result.testsRun}")
    print(f"通过: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ 所有单元测试通过！")
    else:
        print("\n❌ 部分测试失败")
    
    # 运行集成测试（可选）
    run_integration_test()
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
