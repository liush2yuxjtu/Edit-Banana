"""
SAM3 Model Builder
模型构建器
"""

import torch
from pathlib import Path
from typing import Optional

from .sam3_model import SAM3Model


def build_sam3_image_model(
    checkpoint_path: str = "models/sam3_checkpoint.pth",
    device: Optional[str] = None,
    **kwargs
) -> SAM3Model:
    """
    构建 SAM3 图像模型
    
    Args:
        checkpoint_path: 模型检查点路径
        device: 运行设备 (cuda, cpu, mps)
        **kwargs: 其他参数
        
    Returns:
        SAM3Model: SAM3 模型实例
    """
    model = SAM3Model(model_path=checkpoint_path)
    
    # 设置设备
    if device:
        model.device = torch.device(device)
    elif torch.cuda.is_available():
        model.device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        model.device = torch.device("mps")
    else:
        model.device = torch.device("cpu")
    
    # 加载模型
    model.load_model()
    
    return model
