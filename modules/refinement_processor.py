"""
Refinement Processor Module
精化处理器 - 对分割结果进行后处理和精化
"""

import cv2
import numpy as np
from typing import List, Dict, Any, Optional

from .base import BaseProcessor
from .data_types import Element, SegmentationResult, BoundingBox, ElementType


class RefinementProcessor(BaseProcessor):
    """精化处理器 - 清理和优化分割结果"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.iou_threshold = self.get_config("iou_threshold", 0.5)
        self.min_confidence = self.get_config("min_confidence", 0.3)
        self.merge_overlapping = self.get_config("merge_overlapping", True)
        self.remove_small = self.get_config("remove_small", True)
        self.min_element_size = self.get_config("min_element_size", 10)
    
    def process(self, input_data: SegmentationResult, **kwargs) -> SegmentationResult:
        """
        精化分割结果
        
        Args:
            input_data: 原始分割结果
            **kwargs: 额外参数，包括原始图像
            
        Returns:
            SegmentationResult: 精化后的结果
        """
        result = input_data
        elements = result.elements.copy()
        
        # 1. 过滤低置信度元素
        elements = self._filter_by_confidence(elements)
        
        # 2. 移除过小元素
        if self.remove_small:
            elements = self._filter_by_size(elements)
        
        # 3. 合并重叠元素
        if self.merge_overlapping:
            elements = self._merge_overlapping(elements)
        
        # 4. 边界框精化
        elements = self._refine_bounding_boxes(elements, kwargs.get("image"))
        
        # 5. 去重
        elements = self._remove_duplicates(elements)
        
        # 更新结果
        result.elements = elements
        
        return result
    
    def _filter_by_confidence(self, elements: List[Element]) -> List[Element]:
        """
        按置信度过滤元素
        
        Args:
            elements: 元素列表
            
        Returns:
            List[Element]: 过滤后的元素列表
        """
        return [e for e in elements if e.confidence >= self.min_confidence]
    
    def _filter_by_size(self, elements: List[Element]) -> List[Element]:
        """
        按大小过滤元素
        
        Args:
            elements: 元素列表
            
        Returns:
            List[Element]: 过滤后的元素列表
        """
        filtered = []
        for e in elements:
            if e.bbox.width >= self.min_element_size and \
               e.bbox.height >= self.min_element_size:
                filtered.append(e)
        return filtered
    
    def _calculate_iou(self, bbox1: BoundingBox, bbox2: BoundingBox) -> float:
        """
        计算两个边界框的 IoU
        
        Args:
            bbox1: 第一个边界框
            bbox2: 第二个边界框
            
        Returns:
            float: IoU 值
        """
        # 计算交集
        x1 = max(bbox1.x, bbox2.x)
        y1 = max(bbox1.y, bbox2.y)
        x2 = min(bbox1.x + bbox1.width, bbox2.x + bbox2.width)
        y2 = min(bbox1.y + bbox1.height, bbox2.y + bbox2.height)
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        
        # 计算并集
        area1 = bbox1.width * bbox1.height
        area2 = bbox2.width * bbox2.height
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _merge_overlapping(self, elements: List[Element]) -> List[Element]:
        """
        合并重叠的元素
        
        Args:
            elements: 元素列表
            
        Returns:
            List[Element]: 合并后的元素列表
        """
        if not elements:
            return elements
        
        # 按置信度排序
        sorted_elements = sorted(
            elements, 
            key=lambda e: e.confidence, 
            reverse=True
        )
        
        merged = []
        removed = set()
        
        for i, elem1 in enumerate(sorted_elements):
            if i in removed:
                continue
            
            # 查找重叠的元素
            overlapping = [elem1]
            
            for j, elem2 in enumerate(sorted_elements[i+1:], start=i+1):
                if j in removed:
                    continue
                
                iou = self._calculate_iou(elem1.bbox, elem2.bbox)
                
                if iou >= self.iou_threshold:
                    overlapping.append(elem2)
                    removed.add(j)
            
            # 合并重叠元素
            if len(overlapping) > 1:
                merged_elem = self._merge_elements(overlapping)
                merged.append(merged_elem)
            else:
                merged.append(elem1)
        
        return merged
    
    def _merge_elements(self, elements: List[Element]) -> Element:
        """
        合并多个元素
        
        Args:
            elements: 要合并的元素列表
            
        Returns:
            Element: 合并后的元素
        """
        if not elements:
            raise ValueError("Cannot merge empty list of elements")
        
        if len(elements) == 1:
            return elements[0]
        
        # 计算合并后的边界框
        min_x = min(e.bbox.x for e in elements)
        min_y = min(e.bbox.y for e in elements)
        max_x = max(e.bbox.x + e.bbox.width for e in elements)
        max_y = max(e.bbox.y + e.bbox.height for e in elements)
        
        merged_bbox = BoundingBox(
            x=min_x,
            y=min_y,
            width=max_x - min_x,
            height=max_y - min_y
        )
        
        # 使用最高置信度
        max_confidence = max(e.confidence for e in elements)
        
        # 合并元数据
        merged_metadata = {}
        for e in elements:
            merged_metadata.update(e.metadata)
        
        # 确定元素类型（使用第一个元素的类型）
        primary_type = elements[0].element_type
        
        return Element(
            element_id=f"merged_{elements[0].element_id}",
            element_type=primary_type,
            bbox=merged_bbox,
            confidence=max_confidence,
            metadata=merged_metadata
        )
    
    def _refine_bounding_boxes(
        self, 
        elements: List[Element], 
        image: Optional[np.ndarray] = None
    ) -> List[Element]:
        """
        精化边界框
        
        Args:
            elements: 元素列表
            image: 原始图像（可选）
            
        Returns:
            List[Element]: 精化后的元素列表
        """
        # 这里可以实现更复杂的边界框精化逻辑
        # 例如使用图像信息调整边界框
        return elements
    
    def _remove_duplicates(self, elements: List[Element]) -> List[Element]:
        """
        移除重复元素
        
        Args:
            elements: 元素列表
            
        Returns:
            List[Element]: 去重后的元素列表
        """
        unique = []
        seen_boxes = []
        
        for elem in elements:
            is_duplicate = False
            
            for seen_box in seen_boxes:
                iou = self._calculate_iou(elem.bbox, seen_box)
                if iou > 0.9:  # 几乎完全重叠
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append(elem)
                seen_boxes.append(elem.bbox)
        
        return unique
