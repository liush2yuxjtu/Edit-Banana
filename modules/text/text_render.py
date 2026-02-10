"""
Text Render Module
文字渲染和恢复 - 集成 Kimi OCR 和公式识别
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# 导入 Kimi OCR 和公式识别
try:
    from .ocr_recognize import KimiOCRRecognizer, OCRResult
    from .formula_recognize import KimiFormulaRecognizer, FormulaResult, FormulaType
    KIMI_TEXT_AVAILABLE = True
except ImportError:
    KIMI_TEXT_AVAILABLE = False


class TextRestorer:
    """
    文字恢复器 - 全量 Kimi 实现
    
    功能：
    - 使用 Kimi 视觉模型进行 OCR
    - 使用 Kimi 进行公式识别和 LaTeX 转换
    - 生成 DrawIO XML
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化文字恢复器
        
        Args:
            config: 配置字典
                - default_font_size: 默认字体大小
                - default_font_family: 默认字体
                - use_ocr: 是否启用 OCR
                - use_formulas: 是否启用公式识别
                - min_confidence: 最小置信度
        """
        self.config = config or {}
        self.default_font_size = self.config.get("default_font_size", 14)
        self.default_font_family = self.config.get("default_font_family", "Arial")
        self.use_ocr = self.config.get("use_ocr", True)
        self.use_formulas = self.config.get("use_formulas", True)
        self.min_confidence = self.config.get("min_confidence", 0.6)
        
        # 初始化识别器
        self._ocr_recognizer = None
        self._formula_recognizer = None
        
        if KIMI_TEXT_AVAILABLE and self.use_ocr:
            try:
                self._ocr_recognizer = KimiOCRRecognizer(
                    use_formulas=self.use_formulas,
                    min_confidence=self.min_confidence
                )
            except Exception as e:
                print(f"OCR recognizer initialization failed: {e}")
        
        if KIMI_TEXT_AVAILABLE and self.use_formulas:
            try:
                self._formula_recognizer = KimiFormulaRecognizer(
                    confidence_threshold=self.min_confidence
                )
            except Exception as e:
                print(f"Formula recognizer initialization failed: {e}")
    
    def process(self, image_path: str) -> str:
        """
        处理图像，提取文字并生成 DrawIO XML
        
        Args:
            image_path: 输入图像路径
            
        Returns:
            str: DrawIO XML 格式字符串
        """
        import cv2
        
        # 加载图像
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Cannot load image: {image_path}")
        
        # OCR 识别文字
        ocr_results = self.recognize_text(image)
        
        # 生成 XML
        xml_content = self.generate_xml(ocr_results)
        
        return xml_content
    
    def recognize_text(self, image: Union[str, np.ndarray]) -> List[OCRResult]:
        """
        识别图像中的文字
        
        Args:
            image: 输入图像（路径或 numpy 数组）
            
        Returns:
            List[OCRResult]: 识别结果列表
        """
        if self._ocr_recognizer is None:
            print("OCR recognizer not available")
            return []
        
        try:
            return self._ocr_recognizer.recognize(image)
        except Exception as e:
            print(f"OCR recognition failed: {e}")
            return []
    
    def recognize_formula(self, image: Union[str, np.ndarray]) -> FormulaResult:
        """
        识别图像中的公式
        
        Args:
            image: 输入图像
            
        Returns:
            FormulaResult: 公式识别结果
        """
        if self._formula_recognizer is None:
            return FormulaResult(
                latex="",
                formula_type=FormulaType.UNKNOWN,
                confidence=0.0,
                error_msg="Formula recognizer not available"
            )
        
        try:
            return self._formula_recognizer.recognize(image)
        except Exception as e:
            return FormulaResult(
                latex="",
                formula_type=FormulaType.UNKNOWN,
                confidence=0.0,
                error_msg=str(e)
            )
    
    def generate_xml(self, ocr_results: List[OCRResult]) -> str:
        """
        生成 DrawIO XML
        
        Args:
            ocr_results: OCR 结果列表
            
        Returns:
            str: DrawIO XML
        """
        xml_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<mxfile version="21.0" type="device">',
            '<diagram name="Page-1" id="page-1">',
            '<mxGraphModel dx="800" dy="600" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="1" shadow="0">',
            '<root>',
            '<mxCell id="0" />',
            '<mxCell id="1" parent="0" />'
        ]
        
        for i, result in enumerate(ocr_results, start=2):
            bbox = result.bbox
            x = bbox.get("x", 0)
            y = bbox.get("y", 0)
            w = max(bbox.get("width", 100), 20)
            h = max(bbox.get("height", 20), 15)
            
            # 处理文字内容
            text = result.text
            if result.is_formula and result.latex:
                # 使用 LaTeX 格式
                text = result.latex
            
            # 转义特殊字符
            text_escaped = self._escape_xml(text)
            
            # 根据是否是公式设置样式
            if result.is_formula:
                style = "text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=14;math=1;"
            else:
                style = "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=12;"
            
            xml_parts.append(
                f'  <mxCell id="{i}" value="{text_escaped}" style="{style}" vertex="1" parent="1">'
                f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />'
                f'</mxCell>'
            )
        
        xml_parts.extend([
            '</root>',
            '</mxGraphModel>',
            '</diagram>',
            '</mxfile>'
        ])
        
        return '\n'.join(xml_parts)
    
    def restore_text(self, image: np.ndarray, text_info: Dict[str, Any]) -> np.ndarray:
        """
        在图像上恢复文字
        
        Args:
            image: 输入图像
            text_info: 文字信息
            
        Returns:
            np.ndarray: 处理后的图像
        """
        # 转换为 PIL Image
        if len(image.shape) == 2:
            pil_image = Image.fromarray(image).convert('RGB')
        else:
            pil_image = Image.fromarray(image)
        
        draw = ImageDraw.Draw(pil_image)
        
        # 获取文字内容
        text = text_info.get("text", "")
        bbox = text_info.get("bbox", {"x": 0, "y": 0, "width": 100, "height": 20})
        
        x = int(bbox.get("x", 0))
        y = int(bbox.get("y", 0))
        
        # 绘制文字
        try:
            font = ImageFont.truetype(self.default_font_family, self.default_font_size)
        except:
            font = ImageFont.load_default()
        
        draw.text((x, y), text, fill=(0, 0, 0), font=font)
        
        return np.array(pil_image)
    
    def detect_text(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        检测图像中的文字
        
        Args:
            image: 输入图像
            
        Returns:
            List[Dict]: 检测到的文字列表
        """
        results = self.recognize_text(image)
        return [
            {
                "text": r.text,
                "bbox": r.bbox,
                "confidence": r.confidence,
                "is_formula": r.is_formula,
                "latex": r.latex
            }
            for r in results
        ]
    
    def recognize_font(self, image: np.ndarray) -> str:
        """
        识别字体
        
        Args:
            image: 输入图像
            
        Returns:
            str: 字体名称
        """
        return self.default_font_family
    
    def _escape_xml(self, text: str) -> str:
        """
        转义 XML 特殊字符
        
        Args:
            text: 原始文本
            
        Returns:
            str: 转义后的文本
        """
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))


# 类型提示用
from typing import Union
