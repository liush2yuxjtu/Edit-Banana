"""
OCR 识别模块 - 使用 Kimi 视觉模型
不依赖 PaddleOCR，完全使用 LLM Vision
"""

from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
import numpy as np
from PIL import Image

# 导入 Kimi 客户端
try:
    from modules.llm_client import get_kimi_client, vision_ocr
    KIMI_AVAILABLE = True
except ImportError:
    KIMI_AVAILABLE = False


@dataclass
class OCRResult:
    """OCR 识别结果"""
    text: str
    bbox: Dict[str, int]  # x, y, width, height
    confidence: float
    is_formula: bool = False
    latex: Optional[str] = None


class KimiOCRRecognizer:
    """
    基于 Kimi 视觉模型的 OCR 识别器
    
    特点：
    - 不依赖传统 OCR 引擎（PaddleOCR/Tesseract）
    - 利用大模型视觉能力直接识别文字
    - 支持中英文混合识别
    - 支持公式识别
    """
    
    def __init__(self, use_formulas: bool = True, min_confidence: float = 0.6):
        """
        初始化 OCR 识别器
        
        Args:
            use_formulas: 是否启用公式识别
            min_confidence: 最小置信度阈值
        """
        if not KIMI_AVAILABLE:
            raise ImportError("Kimi client not available. Check modules/llm_client.py")
        
        self.client = get_kimi_client()
        self.use_formulas = use_formulas
        self.min_confidence = min_confidence
        
        # 批处理配置
        self.batch_size = 5  # 每批处理的区域数
        self.max_retries = 2  # 失败重试次数
    
    def recognize(self, image: Union[str, np.ndarray, Image.Image]) -> List[OCRResult]:
        """
        识别图像中的所有文字
        
        Args:
            image: 输入图片（路径、numpy数组或PIL Image）
        
        Returns:
            List[OCRResult]: 识别结果列表
        """
        # 1. 使用 Kimi 视觉进行整体 OCR
        raw_results = self._vision_ocr(image)
        
        # 2. 过滤低置信度结果
        filtered = [r for r in raw_results if r.confidence >= self.min_confidence]
        
        # 3. 如果是公式模式，进一步识别公式
        if self.use_formulas:
            filtered = self._recognize_formulas(image, filtered)
        
        # 4. 去重和排序
        filtered = self._deduplicate_and_sort(filtered)
        
        return filtered
    
    def recognize_region(self, image: Union[str, np.ndarray, Image.Image], 
                        bbox: Dict[str, int]) -> OCRResult:
        """
        识别指定区域的文字
        
        Args:
            image: 输入图片
            bbox: 区域坐标 {x, y, width, height}
        
        Returns:
            OCRResult: 识别结果
        """
        # 裁剪区域
        crop = self._crop_image(image, bbox)
        
        # 识别
        text = self._recognize_single(crop)
        
        # 判断是否为公式
        is_formula = self._is_formula(text)
        latex = None
        
        if is_formula and self.use_formulas:
            latex = self.client.recognize_formula(crop)
        
        return OCRResult(
            text=text,
            bbox=bbox,
            confidence=0.85,  # 单区域识别置信度较高
            is_formula=is_formula,
            latex=latex
        )
    
    def recognize_batch(self, image: Union[str, np.ndarray, Image.Image],
                       regions: List[Dict[str, int]]) -> List[OCRResult]:
        """
        批量识别多个区域
        
        Args:
            image: 输入图片
            regions: 区域列表
        
        Returns:
            List[OCRResult]: 识别结果列表
        """
        results = []
        
        for i in range(0, len(regions), self.batch_size):
            batch = regions[i:i + self.batch_size]
            
            for region in batch:
                try:
                    result = self.recognize_region(image, region)
                    results.append(result)
                except Exception as e:
                    print(f"OCR failed for region {region}: {e}")
                    # 添加空结果占位
                    results.append(OCRResult(
                        text="",
                        bbox=region,
                        confidence=0.0
                    ))
        
        return results
    
    def _vision_ocr(self, image: Union[str, np.ndarray, Image.Image]) -> List[OCRResult]:
        """
        使用 Kimi 视觉 API 进行 OCR
        
        Args:
            image: 输入图片
        
        Returns:
            List[OCRResult]: 识别结果
        """
        try:
            # 调用 Kimi 视觉 OCR
            texts = self.client.vision_ocr(image, detail_level="detailed", temperature=0.1)
            
            results = []
            for item in texts:
                text = item.get("text", "").strip()
                if not text:
                    continue
                
                bbox = item.get("bbox", {"x": 0, "y": 0, "width": 0, "height": 0})
                confidence = item.get("confidence", 0.8)
                
                results.append(OCRResult(
                    text=text,
                    bbox=bbox,
                    confidence=confidence,
                    is_formula=self._is_formula(text)
                ))
            
            return results
            
        except Exception as e:
            print(f"Vision OCR failed: {e}")
            # 降级为简单 OCR
            return self._simple_ocr(image)
    
    def _simple_ocr(self, image: Union[str, np.ndarray, Image.Image]) -> List[OCRResult]:
        """
        简单 OCR（降级方案）
        
        Args:
            image: 输入图片
        
        Returns:
            List[OCRResult]: 识别结果
        """
        prompt = """请识别图片中的所有文字，直接列出文字内容，每行一个。
保持文字的原始顺序（从上到下，从左到右）。"""
        
        response = self.client.chat_with_image(image, prompt, temperature=0.1)
        
        results = []
        y_offset = 0
        
        for line in response.split('\n'):
            line = line.strip()
            if line:
                results.append(OCRResult(
                    text=line,
                    bbox={"x": 10, "y": y_offset, "width": 200, "height": 25},
                    confidence=0.7
                ))
                y_offset += 30
        
        return results
    
    def _recognize_formulas(self, image: Union[str, np.ndarray, Image.Image],
                           results: List[OCRResult]) -> List[OCRResult]:
        """
        对可能是公式的区域进行公式识别
        
        Args:
            image: 原图
            results: OCR 结果列表
        
        Returns:
            List[OCRResult]: 更新后的结果
        """
        updated = []
        
        for result in results:
            if result.is_formula:
                try:
                    # 裁剪公式区域
                    crop = self._crop_image(image, result.bbox)
                    # 识别公式
                    latex = self.client.recognize_formula(crop)
                    result.latex = latex
                except Exception as e:
                    print(f"Formula recognition failed: {e}")
            
            updated.append(result)
        
        return updated
    
    def _recognize_single(self, image: Union[str, np.ndarray, Image.Image]) -> str:
        """
        识别单张图片中的文字
        
        Args:
            image: 输入图片
        
        Returns:
            str: 识别的文字
        """
        prompt = """请识别图片中的文字，直接返回文字内容，不要解释。
如果是数学公式，转换为 LaTeX 格式。"""
        
        return self.client.chat_with_image(image, prompt, temperature=0.1).strip()
    
    def _crop_image(self, image: Union[str, np.ndarray, Image.Image], 
                   bbox: Dict[str, int]) -> Image.Image:
        """
        裁剪图片区域
        
        Args:
            image: 原图
            bbox: 边界框 {x, y, width, height}
        
        Returns:
            PIL Image: 裁剪后的图片
        """
        # 统一转换为 PIL Image
        if isinstance(image, str):
            pil_img = Image.open(image)
        elif isinstance(image, np.ndarray):
            if len(image.shape) == 3 and image.shape[2] == 3:
                pil_img = Image.fromarray(image)
            else:
                pil_img = Image.fromarray(image).convert('RGB')
        elif isinstance(image, Image.Image):
            pil_img = image
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")
        
        # 裁剪
        x = int(bbox.get("x", 0))
        y = int(bbox.get("y", 0))
        w = int(bbox.get("width", 100))
        h = int(bbox.get("height", 50))
        
        # 确保不超出边界
        img_w, img_h = pil_img.size
        x = max(0, min(x, img_w - 1))
        y = max(0, min(y, img_h - 1))
        w = min(w, img_w - x)
        h = min(h, img_h - y)
        
        return pil_img.crop((x, y, x + w, y + h))
    
    def _is_formula(self, text: str) -> bool:
        """
        判断文本是否为数学公式
        
        Args:
            text: 输入文本
        
        Returns:
            bool: 是否为公式
        """
        # 公式特征
        formula_indicators = [
            '=', '+', '-', '*', '/', '^', '_', '\\', 'frac', 'sum', 'int',
            'sqrt', 'lim', 'sin', 'cos', 'tan', 'log', 'ln', 'alpha', 'beta',
            'gamma', 'delta', 'theta', 'lambda', 'pi', 'sigma', 'omega',
            '∫', '∑', '√', '∞', '∂', 'Δ', '±', '×', '÷', '≤', '≥', '≠'
        ]
        
        # 检查是否包含公式特征
        return any(indicator in text for indicator in formula_indicators)
    
    def _deduplicate_and_sort(self, results: List[OCRResult]) -> List[OCRResult]:
        """
        去重并排序 OCR 结果
        
        Args:
            results: 原始结果
        
        Returns:
            List[OCRResult]: 处理后的结果
        """
        # 基于位置去重（IOU 阈值）
        unique = []
        for result in results:
            is_duplicate = False
            for existing in unique:
                if self._calculate_iou(result.bbox, existing.bbox) > 0.5:
                    # 保留置信度高的
                    if result.confidence > existing.confidence:
                        existing.text = result.text
                        existing.confidence = result.confidence
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append(result)
        
        # 按阅读顺序排序（从上到下，从左到右）
        # 使用 y 坐标为主，x 坐标为辅
        unique.sort(key=lambda r: (r.bbox.get("y", 0), r.bbox.get("x", 0)))
        
        return unique
    
    def _calculate_iou(self, bbox1: Dict[str, int], bbox2: Dict[str, int]) -> float:
        """
        计算两个边界框的 IOU
        
        Args:
            bbox1: 边界框1
            bbox2: 边界框2
        
        Returns:
            float: IOU 值
        """
        x1 = max(bbox1.get("x", 0), bbox2.get("x", 0))
        y1 = max(bbox1.get("y", 0), bbox2.get("y", 0))
        x2 = min(bbox1.get("x", 0) + bbox1.get("width", 0),
                 bbox2.get("x", 0) + bbox2.get("width", 0))
        y2 = min(bbox1.get("y", 0) + bbox1.get("height", 0),
                 bbox2.get("y", 0) + bbox2.get("height", 0))
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        area1 = bbox1.get("width", 0) * bbox1.get("height", 0)
        area2 = bbox2.get("width", 0) * bbox2.get("height", 0)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0


# 便捷函数
def recognize_text(image: Union[str, np.ndarray, Image.Image], 
                  **kwargs) -> List[OCRResult]:
    """
    识别图片中的文字（便捷函数）
    
    Args:
        image: 输入图片
        **kwargs: 额外参数
    
    Returns:
        List[OCRResult]: 识别结果
    """
    recognizer = KimiOCRRecognizer(**kwargs)
    return recognizer.recognize(image)


def recognize_formula(image: Union[str, np.ndarray, Image.Image]) -> str:
    """
    识别图片中的公式（便捷函数）
    
    Args:
        image: 输入图片
    
    Returns:
        str: LaTeX 公式
    """
    client = get_kimi_client()
    return client.recognize_formula(image)
