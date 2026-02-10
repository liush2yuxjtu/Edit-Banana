"""
SAM3 Info Extractor Module
从 SAM3 模型输出中提取信息
"""

import torch
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import cv2

from .base import BaseProcessor
from .data_types import BoundingBox, Element, ElementType, SegmentationResult


class PromptGroup(Enum):
    """提示词分组枚举"""
    IMAGE = "image"
    ARROW = "arrow"
    BASIC_SHAPE = "shape"
    BACKGROUND = "background"
    TEXT = "text"
    ICON = "icon"


class SAM3InfoExtractor(BaseProcessor):
    """SAM3 信息提取器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.confidence_threshold = self.get_config("confidence_threshold", 0.5)
        self.min_area = self.get_config("min_area", 100)
    
    def process(self, input_data: Any, **kwargs) -> SegmentationResult:
        """
        从 SAM3 输出中提取元素信息
        
        Args:
            input_data: SAM3 模型输出 (masks, boxes, 等)
            **kwargs: 额外参数，包括原始图像路径
            
        Returns:
            SegmentationResult: 分割结果
        """
        masks = input_data.get("masks", [])
        boxes = input_data.get("boxes", [])
        scores = input_data.get("scores", [])
        labels = input_data.get("labels", [])
        
        result = SegmentationResult()
        result.original_image_path = kwargs.get("image_path")
        
        for i, (mask, box, score, label) in enumerate(zip(masks, boxes, scores, labels)):
            if score < self.confidence_threshold:
                continue
            
            # 计算边界框
            bbox = BoundingBox(
                x=float(box[0]),
                y=float(box[1]),
                width=float(box[2] - box[0]),
                height=float(box[3] - box[1])
            )
            
            # 确定元素类型
            element_type = self._get_element_type(label)
            
            # 创建元素
            element = Element(
                element_id=f"element_{i:04d}",
                element_type=element_type,
                bbox=bbox,
                confidence=float(score),
                metadata={
                    "mask_area": float(np.sum(mask)),
                    "label": label
                }
            )
            
            result.add_element(element)
        
        return result
    
    def _get_element_type(self, label: Any) -> ElementType:
        """
        根据标签确定元素类型
        
        Args:
            label: 标签
            
        Returns:
            ElementType: 元素类型
        """
        label_str = str(label).lower()
        
        if any(word in label_str for word in ["arrow", "line", "connector"]):
            return ElementType.ARROW
        elif any(word in label_str for word in ["text", "label", "caption"]):
            return ElementType.TEXT
        elif any(word in label_str for word in ["icon", "symbol"]):
            return ElementType.ICON
        elif any(word in label_str for word in ["image", "picture", "photo"]):
            return ElementType.IMAGE
        elif any(word in label_str for word in ["background", "bg"]):
            return ElementType.BACKGROUND
        else:
            return ElementType.SHAPE
    
    def extract_masks(self, image: np.ndarray, sam_output: Dict[str, Any]) -> List[np.ndarray]:
        """
        提取掩码
        
        Args:
            image: 原始图像
            sam_output: SAM3 输出
            
        Returns:
            List[np.ndarray]: 掩码列表
        """
        masks = sam_output.get("masks", [])
        return [m for m in masks if np.sum(m) >= self.min_area]
