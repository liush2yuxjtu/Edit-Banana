"""
Icon Picture Processor Module
图标和图片处理器
"""

import cv2
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path

from .base import BaseProcessor
from .data_types import Element, ElementType, BoundingBox

# 检查 spandrel 是否可用
try:
    import spandrel
    SPANDREL_AVAILABLE = True
except ImportError:
    SPANDREL_AVAILABLE = False


class UpscaleModel:
    """图像超分辨率模型包装器"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model = None
        self.scale = 2  # 默认 2x 放大
        
        if SPANDREL_AVAILABLE:
            self._load_model()
    
    def _load_model(self):
        """加载超分辨率模型"""
        try:
            # 使用 spandrel 加载模型
            from spandrel import ModelLoader
            if self.model_path and Path(self.model_path).exists():
                self.model = ModelLoader().load_from_file(self.model_path)
            else:
                # 使用默认的轻量级模型
                self.model = None
        except Exception as e:
            print(f"Failed to load upscale model: {e}")
            self.model = None
    
    def upscale(self, image: np.ndarray) -> np.ndarray:
        """
        放大图像
        
        Args:
            image: 输入图像
            
        Returns:
            np.ndarray: 放大后的图像
        """
        if self.model is None or not SPANDREL_AVAILABLE:
            # 使用简单的插值方法
            h, w = image.shape[:2]
            return cv2.resize(image, (w * self.scale, h * self.scale), interpolation=cv2.INTER_CUBIC)
        
        try:
            # 使用 spandrel 模型
            import torch
            from spandrel import ImageModelDescriptor
            
            # 准备输入
            if len(image.shape) == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            elif image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
            
            # 转换为 tensor
            img_tensor = torch.from_numpy(image).permute(2, 0, 1).unsqueeze(0).float() / 255.0
            
            # 推理
            with torch.no_grad():
                output = self.model(img_tensor)
            
            # 转换回 numpy
            output = output.squeeze(0).permute(1, 2, 0).cpu().numpy()
            output = (output * 255.0).clip(0, 255).astype(np.uint8)
            
            return output
        except Exception as e:
            print(f"Upscale failed: {e}, falling back to interpolation")
            h, w = image.shape[:2]
            return cv2.resize(image, (w * self.scale, h * self.scale), interpolation=cv2.INTER_CUBIC)


class IconPictureProcessor(BaseProcessor):
    """图标和图片处理器 - 识别和处理图标及图片"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.min_icon_size = self.get_config("min_icon_size", 16)
        self.max_icon_size = self.get_config("max_icon_size", 256)
        self.icon_templates_dir = self.get_config("icon_templates_dir", None)
        self.templates = []
        
        # 加载图标模板（如果提供了目录）
        if self.icon_templates_dir:
            self._load_templates()
    
    def process(self, input_data: np.ndarray, **kwargs) -> List[Element]:
        """
        处理图像，识别图标和图片
        
        Args:
            input_data: 输入图像 (numpy array)
            **kwargs: 额外参数
            
        Returns:
            List[Element]: 识别出的图标和图片元素列表
        """
        image = input_data
        elements = []
        
        # 检测图标
        icons = self._detect_icons(image)
        elements.extend(icons)
        
        # 检测图片区域
        pictures = self._detect_pictures(image)
        elements.extend(pictures)
        
        return elements
    
    def _detect_icons(self, image: np.ndarray) -> List[Element]:
        """
        检测图标
        
        Args:
            image: 输入图像
            
        Returns:
            List[Element]: 图标元素列表
        """
        icons = []
        
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 使用模板匹配（如果有模板）
        if self.templates:
            for template_info in self.templates:
                template = template_info["image"]
                template_name = template_info["name"]
                
                # 多尺度匹配
                for scale in np.linspace(0.5, 1.5, 10):
                    resized = cv2.resize(
                        template, 
                        None, 
                        fx=scale, 
                        fy=scale
                    )
                    
                    if resized.shape[0] > gray.shape[0] or resized.shape[1] > gray.shape[1]:
                        continue
                    
                    result = cv2.matchTemplate(gray, resized, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    if max_val > 0.8:  # 匹配阈值
                        h, w = resized.shape[:2]
                        bbox = BoundingBox(
                            x=float(max_loc[0]),
                            y=float(max_loc[1]),
                            width=float(w),
                            height=float(h)
                        )
                        
                        element = Element(
                            element_id=f"icon_{len(icons):04d}",
                            element_type=ElementType.ICON,
                            bbox=bbox,
                            confidence=float(max_val),
                            metadata={
                                "template": template_name,
                                "scale": float(scale),
                                "matched_size": (w, h)
                            }
                        )
                        
                        icons.append(element)
        else:
            # 使用启发式方法检测可能的图标区域
            icons = self._detect_icons_heuristic(gray)
        
        return icons
    
    def _detect_icons_heuristic(self, gray: np.ndarray) -> List[Element]:
        """
        使用启发式方法检测图标
        
        Args:
            gray: 灰度图像
            
        Returns:
            List[Element]: 图标元素列表
        """
        icons = []
        
        # 二值化
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 查找轮廓
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        for i, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            
            # 检查大小是否在图标范围内
            if self.min_icon_size <= w <= self.max_icon_size and \
               self.min_icon_size <= h <= self.max_icon_size:
                
                # 检查宽高比
                aspect_ratio = w / h if h > 0 else 1
                
                if 0.5 <= aspect_ratio <= 2.0:
                    bbox = BoundingBox(
                        x=float(x),
                        y=float(y),
                        width=float(w),
                        height=float(h)
                    )
                    
                    element = Element(
                        element_id=f"icon_{i:04d}",
                        element_type=ElementType.ICON,
                        bbox=bbox,
                        confidence=0.7,
                        metadata={
                            "detection_method": "heuristic",
                            "aspect_ratio": float(aspect_ratio)
                        }
                    )
                    
                    icons.append(element)
        
        return icons
    
    def _detect_pictures(self, image: np.ndarray) -> List[Element]:
        """
        检测图片区域
        
        Args:
            image: 输入图像
            
        Returns:
            List[Element]: 图片元素列表
        """
        pictures = []
        
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 检测大的矩形区域（可能是图片）
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(
            edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        height, width = gray.shape
        min_picture_area = (height * width) * 0.05  # 至少占图像5%面积
        
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            
            if area >= min_picture_area:
                x, y, w, h = cv2.boundingRect(contour)
                
                bbox = BoundingBox(
                    x=float(x),
                    y=float(y),
                    width=float(w),
                    height=float(h)
                )
                
                element = Element(
                    element_id=f"picture_{i:04d}",
                    element_type=ElementType.IMAGE,
                    bbox=bbox,
                    confidence=0.75,
                    metadata={
                        "area": float(area),
                        "area_ratio": float(area / (height * width))
                    }
                )
                
                pictures.append(element)
        
        return pictures
    
    def _load_templates(self):
        """加载图标模板"""
        if not self.icon_templates_dir:
            return
        
        template_dir = Path(self.icon_templates_dir)
        if not template_dir.exists():
            return
        
        for template_file in template_dir.glob("*.png"):
            template_img = cv2.imread(str(template_file), cv2.IMREAD_GRAYSCALE)
            if template_img is not None:
                self.templates.append({
                    "name": template_file.stem,
                    "image": template_img
                })
