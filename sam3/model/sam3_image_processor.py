"""
SAM3 Image Processor
图像处理器
"""

import torch
import numpy as np
from PIL import Image
from typing import List, Dict, Any, Optional, Union


class Sam3Processor:
    """SAM3 图像处理器"""
    
    def __init__(self, model, device: str = "cpu"):
        self.model = model
        self.device = device
    
    def preprocess(self, image: Union[np.ndarray, Image.Image, str]) -> np.ndarray:
        """
        预处理图像
        
        Args:
            image: 输入图像
            
        Returns:
            np.ndarray: 预处理后的图像
        """
        if isinstance(image, str):
            image = Image.open(image).convert('RGB')
        
        if isinstance(image, Image.Image):
            image = np.array(image)
        
        # 确保是 RGB 格式
        if len(image.shape) == 2:
            image = np.stack([image] * 3, axis=-1)
        elif image.shape[2] == 4:
            image = image[:, :, :3]
        
        return image
    
    def postprocess_masks(
        self,
        masks: List[np.ndarray],
        boxes: List[List[int]],
        scores: List[float],
        labels: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """
        后处理掩码
        
        Args:
            masks: 掩码列表
            boxes: 边界框列表
            scores: 分数列表
            labels: 标签列表
            
        Returns:
            Dict: 处理后的结果
        """
        return {
            "masks": masks,
            "boxes": boxes,
            "scores": scores,
            "labels": labels,
            "count": len(masks)
        }
    
    def __call__(
        self,
        image: Union[np.ndarray, Image.Image],
        prompts: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        处理图像
        
        Args:
            image: 输入图像
            prompts: 文本提示
            
        Returns:
            Dict: 处理结果
        """
        # 预处理
        processed_image = self.preprocess(image)
        
        # 使用模型预测
        result = self.model.predict(processed_image, prompts=prompts)
        
        # 后处理
        return self.postprocess_masks(
            result.get("masks", []),
            result.get("boxes", []),
            result.get("scores", []),
            result.get("labels", [])
        )
