"""
Base Processor Module
所有处理器的基类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pathlib import Path


class BaseProcessor(ABC):
    """处理器基类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.name = self.__class__.__name__
    
    @abstractmethod
    def process(self, input_data: Any, **kwargs) -> Any:
        """
        处理输入数据
        
        Args:
            input_data: 输入数据
            **kwargs: 额外参数
            
        Returns:
            处理结果
        """
        pass
    
    def validate_input(self, input_data: Any) -> bool:
        """
        验证输入数据
        
        Args:
            input_data: 输入数据
            
        Returns:
            是否有效
        """
        return input_data is not None
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        return self.config.get(key, default)
