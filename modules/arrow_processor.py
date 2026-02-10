"""
Arrow Processor Module
箭头处理器
"""

import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

from .base import BaseProcessor
from .data_types import Element, ElementType, BoundingBox


class ArrowProcessor(BaseProcessor):
    """箭头处理器 - 识别和处理箭头"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.min_arrow_length = self.get_config("min_arrow_length", 20)
        self.max_arrow_width = self.get_config("max_arrow_width", 50)
        self.angle_tolerance = self.get_config("angle_tolerance", 15)  # 角度容差
    
    def process(self, input_data: np.ndarray, **kwargs) -> List[Element]:
        """
        处理图像，识别箭头
        
        Args:
            input_data: 输入图像 (numpy array)
            **kwargs: 额外参数
            
        Returns:
            List[Element]: 识别出的箭头元素列表
        """
        image = input_data
        arrows = []
        
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 边缘检测
        edges = cv2.Canny(gray, 50, 150)
        
        # 查找轮廓
        contours, _ = cv2.findContours(
            edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
        )
        
        # 查找直线
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, 
            threshold=self.get_config("hough_threshold", 50),
            minLineLength=self.min_arrow_length,
            maxLineGap=self.get_config("max_line_gap", 10)
        )
        
        if lines is not None:
            for i, line in enumerate(lines):
                x1, y1, x2, y2 = line[0]
                
                # 计算直线长度和角度
                length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                
                # 检查是否为箭头（通过查找箭头头部）
                arrow_head = self._detect_arrow_head(
                    image, (x1, y1), (x2, y2), contours
                )
                
                if arrow_head:
                    bbox = BoundingBox(
                        x=float(min(x1, x2) - 10),
                        y=float(min(y1, y2) - 10),
                        width=float(abs(x2 - x1) + 20),
                        height=float(abs(y2 - y1) + 20)
                    )
                    
                    element = Element(
                        element_id=f"arrow_{i:04d}",
                        element_type=ElementType.ARROW,
                        bbox=bbox,
                        confidence=arrow_head.get("confidence", 0.75),
                        metadata={
                            "start_point": (int(x1), int(y1)),
                            "end_point": (int(x2), int(y2)),
                            "length": float(length),
                            "angle": float(angle),
                            "arrow_head": arrow_head,
                            "direction": self._get_direction(angle)
                        }
                    )
                    
                    arrows.append(element)
        
        return arrows
    
    def _detect_arrow_head(
        self, 
        image: np.ndarray, 
        start: Tuple[int, int], 
        end: Tuple[int, int],
        contours: List[np.ndarray]
    ) -> Optional[Dict[str, Any]]:
        """
        检测箭头头部
        
        Args:
            image: 输入图像
            start: 起点
            end: 终点
            contours: 轮廓列表
            
        Returns:
            Optional[Dict]: 箭头头部信息
        """
        # 检查终点附近的轮廓
        search_radius = 20
        
        for contour in contours:
            # 计算轮廓中心
            M = cv2.moments(contour)
            if M["m00"] == 0:
                continue
            
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            
            # 检查是否在终点附近
            dist_to_end = np.sqrt((cx - end[0]) ** 2 + (cy - end[1]) ** 2)
            
            if dist_to_end < search_radius:
                # 检查形状是否为三角形（箭头头部）
                epsilon = 0.1 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                if len(approx) == 3:  # 三角形
                    return {
                        "position": (cx, cy),
                        "confidence": 0.9,
                        "type": "triangle"
                    }
        
        return None
    
    def _get_direction(self, angle: float) -> str:
        """
        根据角度获取方向描述
        
        Args:
            angle: 角度（度）
            
        Returns:
            str: 方向描述
        """
        # 标准化角度到 0-360
        angle = angle % 360
        if angle < 0:
            angle += 360
        
        # 判断方向
        if 45 <= angle < 135:
            return "down"
        elif 135 <= angle < 225:
            return "left"
        elif 225 <= angle < 315:
            return "up"
        else:
            return "right"
    
    def get_arrow_relationships(self, arrows: List[Element]) -> List[Dict[str, Any]]:
        """
        分析箭头之间的关系（连接关系）
        
        Args:
            arrows: 箭头列表
            
        Returns:
            List[Dict]: 关系列表
        """
        relationships = []
        
        for i, arrow1 in enumerate(arrows):
            end1 = arrow1.metadata.get("end_point")
            
            for j, arrow2 in enumerate(arrows):
                if i == j:
                    continue
                
                start2 = arrow2.metadata.get("start_point")
                
                # 检查是否连接
                if end1 and start2:
                    distance = np.sqrt(
                        (end1[0] - start2[0]) ** 2 + 
                        (end1[1] - start2[1]) ** 2
                    )
                    
                    if distance < 20:  # 连接阈值
                        relationships.append({
                            "from": arrow1.element_id,
                            "to": arrow2.element_id,
                            "type": "connects_to",
                            "distance": float(distance)
                        })
        
        return relationships
