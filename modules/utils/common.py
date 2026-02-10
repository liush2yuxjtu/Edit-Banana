"""
Utility Functions
通用工具函数
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    确保目录存在
    
    Args:
        path: 目录路径
        
    Returns:
        Path: 目录路径
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    加载 JSON 文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        Dict: JSON 数据
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"加载 JSON 文件失败 {file_path}: {e}")
        return {}


def save_json_file(data: Dict[str, Any], file_path: Union[str, Path]) -> bool:
    """
    保存 JSON 文件
    
    Args:
        data: 数据
        file_path: 文件路径
        
    Returns:
        bool: 是否成功
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logging.error(f"保存 JSON 文件失败 {file_path}: {e}")
        return False


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    获取文件大小
    
    Args:
        file_path: 文件路径
        
    Returns:
        int: 文件大小（字节）
    """
    try:
        return os.path.getsize(file_path)
    except Exception:
        return 0


def is_image_file(filename: str) -> bool:
    """
    检查是否为图片文件
    
    Args:
        filename: 文件名
        
    Returns:
        bool: 是否为图片文件
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    return any(filename.lower().endswith(ext) for ext in image_extensions)


def is_pdf_file(filename: str) -> bool:
    """
    检查是否为 PDF 文件
    
    Args:
        filename: 文件名
        
    Returns:
        bool: 是否为 PDF 文件
    """
    return filename.lower().endswith('.pdf')


def format_time(seconds: float) -> str:
    """
    格式化时间
    
    Args:
        seconds: 秒数
        
    Returns:
        str: 格式化后的时间字符串
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:.0f}m {secs:.1f}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours:.0f}h {minutes:.0f}m"


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    安全获取字典值
    
    Args:
        dictionary: 字典
        key: 键
        default: 默认值
        
    Returns:
        Any: 值或默认值
    """
    return dictionary.get(key, default)
