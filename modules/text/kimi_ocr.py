"""
Kimi OCR 模块
使用 Kimi 视觉模型进行 OCR 识别

功能：
- 识别图片中的文本
- 返回带坐标的文本列表

使用方法:
    from modules.text.kimi_ocr import KimiOCR
    
    ocr = KimiOCR()
    text_blocks = ocr.recognize("image.png")
    for block in text_blocks:
        print(f"文本: {block.text}, 位置: ({block.x}, {block.y})")
"""

import os
import json
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path

from modules.kimi_client import KimiClient, TextBlock, get_client


@dataclass
class OCRResult:
    """OCR 识别结果"""
    text_blocks: List[TextBlock]
    raw_text: str = ""
    image_path: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "text_blocks": [block.to_dict() for block in self.text_blocks],
            "raw_text": self.raw_text,
            "image_path": self.image_path
        }
    
    def to_text(self, separator: str = "\n") -> str:
        """将所有文本合并为一个字符串"""
        return separator.join(block.text for block in self.text_blocks)
    
    def filter_by_confidence(self, min_confidence: float = 0.6) -> List[TextBlock]:
        """按置信度过滤文本块"""
        return [block for block in self.text_blocks if block.confidence >= min_confidence]
    
    def get_text_by_region(
        self,
        x: float = 0,
        y: float = 0,
        width: float = 1,
        height: float = 1
    ) -> List[TextBlock]:
        """
        获取指定区域内的文本
        
        Args:
            x, y: 区域左上角坐标（0-1 相对坐标）
            width, height: 区域宽高（0-1 相对坐标）
            
        Returns:
            区域内的文本块列表
        """
        region_blocks = []
        for block in self.text_blocks:
            # 检查文本块是否在指定区域内
            block_right = block.x + block.width
            block_bottom = block.y + block.height
            region_right = x + width
            region_bottom = y + height
            
            # 简单判断是否有重叠
            if (block.x < region_right and block_right > x and
                block.y < region_bottom and block_bottom > y):
                region_blocks.append(block)
        
        return region_blocks


class KimiOCR:
    """
    Kimi OCR 识别器
    
    使用 Kimi 视觉模型识别图片中的文本
    """
    
    # OCR 提示词
    DEFAULT_OCR_PROMPT = """请识别图片中的所有文本，并以 JSON 格式返回。

要求：
1. 识别图片中的所有可见文本
2. 为每个文本块提供位置信息（相对于图片的归一化坐标，0-1之间）
3. 提供每个文本块的置信度（0-1之间）
4. 保持文本的原始阅读顺序（从上到下，从左到右）

每个文本块需要包含以下字段：
- text: 文本内容（字符串）
- x: 左上角 x 坐标（0-1之间）
- y: 左上角 y 坐标（0-1之间）
- width: 宽度（0-1之间）
- height: 高度（0-1之间）
- confidence: 置信度（0-1之间）

请严格按以下 JSON 格式返回，不要包含任何其他说明文字：
{
  "text_blocks": [
    {
      "text": "示例文本",
      "x": 0.1,
      "y": 0.2,
      "width": 0.3,
      "height": 0.05,
      "confidence": 0.95
    }
  ]
}"""
    
    DEFAULT_SYSTEM_PROMPT = "你是一个专业的 OCR 引擎，擅长准确识别图片中的文本内容并提供精确的位置信息。"
    
    def __init__(
        self,
        client: Optional[KimiClient] = None,
        min_confidence: float = 0.6,
        ocr_prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **client_kwargs
    ):
        """
        初始化 OCR 识别器
        
        Args:
            client: KimiClient 实例（可选，默认自动创建）
            min_confidence: 最小置信度阈值
            ocr_prompt: 自定义 OCR 提示词
            system_prompt: 自定义系统提示词
            **client_kwargs: 传递给 KimiClient 的参数
        """
        self.client = client or get_client(**client_kwargs)
        self.min_confidence = min_confidence
        self.ocr_prompt = ocr_prompt or self.DEFAULT_OCR_PROMPT
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
    
    def recognize(
        self,
        image_path: Union[str, Path],
        return_raw: bool = False,
        **kwargs
    ) -> OCRResult:
        """
        识别图片中的文本
        
        Args:
            image_path: 图片路径
            return_raw: 是否返回原始响应
            **kwargs: 额外的 API 参数
            
        Returns:
            OCRResult: OCR 识别结果
        """
        image_path = str(image_path)
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片不存在: {image_path}")
        
        # 调用 Kimi API 进行 OCR
        response = self.client.chat_with_image(
            prompt=self.ocr_prompt,
            image_path=image_path,
            system=self.system_prompt,
            **kwargs
        )
        
        # 解析响应
        text_blocks = self._parse_ocr_response(response)
        
        # 过滤低置信度的结果
        filtered_blocks = [
            block for block in text_blocks 
            if block.confidence >= self.min_confidence
        ]
        
        # 按阅读顺序排序（从上到下，从左到右）
        sorted_blocks = sorted(
            filtered_blocks, 
            key=lambda b: (b.y, b.x)
        )
        
        result = OCRResult(
            text_blocks=sorted_blocks,
            raw_text=response,
            image_path=image_path
        )
        
        return result
    
    def recognize_batch(
        self,
        image_paths: List[Union[str, Path]],
        **kwargs
    ) -> List[OCRResult]:
        """
        批量识别多张图片
        
        Args:
            image_paths: 图片路径列表
            **kwargs: 额外的 API 参数
            
        Returns:
            List[OCRResult]: OCR 结果列表
        """
        results = []
        for path in image_paths:
            try:
                result = self.recognize(path, **kwargs)
                results.append(result)
            except Exception as e:
                # 记录错误但继续处理其他图片
                results.append(OCRResult(
                    text_blocks=[],
                    raw_text=f"错误: {str(e)}",
                    image_path=str(path)
                ))
        
        return results
    
    def extract_text_only(
        self,
        image_path: Union[str, Path],
        separator: str = "\n",
        **kwargs
    ) -> str:
        """
        仅提取文本内容（不包含坐标信息）
        
        Args:
            image_path: 图片路径
            separator: 文本分隔符
            **kwargs: 额外的 API 参数
            
        Returns:
            str: 提取的文本
        """
        result = self.recognize(image_path, **kwargs)
        return result.to_text(separator)
    
    def _parse_ocr_response(self, response: str) -> List[TextBlock]:
        """
        解析 OCR API 响应
        
        Args:
            response: API 返回的原始响应
            
        Returns:
            List[TextBlock]: 文本块列表
        """
        try:
            # 提取 JSON 部分
            json_str = self._extract_json(response)
            data = json.loads(json_str)
            
            text_blocks = []
            for block_data in data.get("text_blocks", []):
                text_blocks.append(TextBlock(
                    text=block_data.get("text", ""),
                    x=float(block_data.get("x", 0)),
                    y=float(block_data.get("y", 0)),
                    width=float(block_data.get("width", 0)),
                    height=float(block_data.get("height", 0)),
                    confidence=float(block_data.get("confidence", 1.0))
                ))
            
            return text_blocks
            
        except json.JSONDecodeError as e:
            # 尝试从文本中提取可能的文本内容
            return self._fallback_parse(response)
        except Exception as e:
            raise Exception(f"OCR 结果解析失败: {e}")
    
    def _extract_json(self, text: str) -> str:
        """从文本中提取 JSON 部分"""
        # 尝试找到 JSON 代码块
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end == -1:
                end = len(text)
            return text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end == -1:
                end = len(text)
            return text[start:end].strip()
        
        # 尝试找到 JSON 对象
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return text[start:end+1]
        
        return text
    
    def _fallback_parse(self, text: str) -> List[TextBlock]:
        """
        备用解析方法 - 当 JSON 解析失败时使用
        
        尝试从非结构化文本中提取文本块
        """
        # 简单处理：将整个响应作为一个文本块
        # 坐标设为 0，表示未知位置
        return [TextBlock(
            text=text.strip(),
            x=0.0,
            y=0.0,
            width=1.0,
            height=1.0,
            confidence=0.5
        )]
    
    def health_check(self) -> Dict[str, Any]:
        """
        检查 OCR 服务健康状态
        
        Returns:
            Dict: 状态信息
        """
        return self.client.health_check()


# 便捷函数
def recognize_text(
    image_path: Union[str, Path],
    **kwargs
) -> OCRResult:
    """
    便捷函数：识别图片中的文本
    
    Args:
        image_path: 图片路径
        **kwargs: 额外参数
        
    Returns:
        OCRResult: OCR 结果
    """
    ocr = KimiOCR()
    return ocr.recognize(image_path, **kwargs)


def extract_text(
    image_path: Union[str, Path],
    separator: str = "\n",
    **kwargs
) -> str:
    """
    便捷函数：仅提取文本
    
    Args:
        image_path: 图片路径
        separator: 文本分隔符
        **kwargs: 额外参数
        
    Returns:
        str: 提取的文本
    """
    ocr = KimiOCR()
    return ocr.extract_text_only(image_path, separator, **kwargs)
