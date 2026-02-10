"""
Basic Shape Processor Module
基础形状处理器
"""

import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from .base import BaseProcessor
from .data_types import Element, ElementType, BoundingBox


class BasicShapeProcessor(BaseProcessor):
    """基础形状处理器 - 识别矩形、圆形、椭圆等基本形状"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.epsilon_factor = self.get_config("epsilon_factor", 0.02)
        self.min_contour_area = self.get_config("min_contour_area", 100)
        self.max_contour_area = self.get_config("max_contour_area", 0.9)
    
    def process(self, input_data: np.ndarray, **kwargs) -> List[Element]:
        """
        处理图像，识别基本形状
        
        Args:
            input_data: 输入图像 (numpy array)
            **kwargs: 额外参数
            
        Returns:
            List[Element]: 识别出的形状元素列表
        """
        image = input_data
        elements = []
        
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 二值化
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        
        # 查找轮廓
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        height, width = gray.shape
        max_area = height * width * self.max_contour_area
        
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            
            # 过滤过小或过大的轮廓
            if area < self.min_contour_area or area > max_area:
                continue
            
            # 分析形状
            shape_info = self._analyze_shape(contour)
            
            # 创建边界框
            x, y, w, h = cv2.boundingRect(contour)
            bbox = BoundingBox(x=float(x), y=float(y), width=float(w), height=float(h))
            
            # 创建元素
            element = Element(
                element_id=f"shape_{i:04d}",
                element_type=ElementType.SHAPE,
                bbox=bbox,
                confidence=shape_info.get("confidence", 0.8),
                metadata={
                    "shape_type": shape_info.get("type", "unknown"),
                    "area": float(area),
                    "contour": contour.tolist()
                }
            )
            
            elements.append(element)
        
        return elements
    
    def _analyze_shape(self, contour: np.ndarray) -> Dict[str, Any]:
        """
        分析轮廓形状
        
        Args:
            contour: 轮廓点
            
        Returns:
            Dict: 形状信息
        """
        # 计算周长
        perimeter = cv2.arcLength(contour, True)
        
        # 多边形逼近
        epsilon = self.epsilon_factor * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # 顶点数
        vertices = len(approx)
        
        # 计算面积
        area = cv2.contourArea(contour)
        
        # 判断形状类型
        shape_type = "unknown"
        confidence = 0.5
        
        if vertices == 3:
            shape_type = "triangle"
            confidence = 0.85
        elif vertices == 4:
            # 判断是否为矩形
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h if h > 0 else 1
            
            if 0.9 <= aspect_ratio <= 1.1:
                shape_type = "square"
                confidence = 0.9
            else:
                shape_type = "rectangle"
                confidence = 0.9
        elif vertices == 5:
            shape_type = "pentagon"
            confidence = 0.8
        elif vertices == 6:
            shape_type = "hexagon"
            confidence = 0.8
        elif vertices > 6:
            # 判断是否为圆形或椭圆
            (x, y), (MA, ma), angle = cv2.fitEllipse(contour)
            
            if abs(MA - ma) < 10:  # 长短轴接近
                shape_type = "circle"
                confidence = 0.85
            else:
                shape_type = "ellipse"
                confidence = 0.8
        
        return {
            "type": shape_type,
            "vertices": vertices,
            "confidence": confidence,
            "area": area,
            "perimeter": perimeter
        }
    
    def detect_rectangles(self, image: np.ndarray) -> List[Element]:
        """
        专门检测矩形
        
        Args:
            image: 输入图像
            
        Returns:
            List[Element]: 矩形元素列表
        """
        all_elements = self.process(image)
        return [e for e in all_elements 
                if e.metadata.get("shape_type") in ["rectangle", "square"]]
