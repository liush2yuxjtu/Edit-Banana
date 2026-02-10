"""
Text Processing Utilities
文本处理工具
"""

from typing import List, Dict, Any, Optional, Tuple
import re
import string
from pathlib import Path


def clean_text(text: str) -> str:
    """
    清理文本
    
    Args:
        text: 原始文本
        
    Returns:
        str: 清理后的文本
    """
    if not text:
        return ""
    
    # 移除多余空白字符
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 移除特殊字符（保留字母、数字、中文和基本标点）
    text = re.sub(r'[^\u4e00-\u9fff\w\s.,!?;:"\'()\-_]', '', text)
    
    return text


def extract_numbers(text: str) -> List[float]:
    """
    提取文本中的数字
    
    Args:
        text: 文本
        
    Returns:
        List[float]: 数字列表
    """
    numbers = re.findall(r'-?\d+\.?\d*', text)
    return [float(n) for n in numbers]


def normalize_text(text: str) -> str:
    """
    标准化文本
    
    Args:
        text: 原始文本
        
    Returns:
        str: 标准化后的文本
    """
    text = clean_text(text)
    
    # 转换为小写（英文部分）
    text = re.sub(
        r'([a-zA-Z]+)', 
        lambda m: m.group(1).lower(), 
        text
    )
    
    return text


def is_valid_text(text: str, min_length: int = 1) -> bool:
    """
    检查文本是否有效
    
    Args:
        text: 文本
        min_length: 最小长度
        
    Returns:
        bool: 是否有效
    """
    if not text or len(text.strip()) < min_length:
        return False
    
    # 检查是否包含有效字符
    return bool(re.search(r'[\u4e00-\u9fff\w]', text))


def split_text_by_punctuation(text: str) -> List[str]:
    """
    按标点符号分割文本
    
    Args:
        text: 文本
        
    Returns:
        List[str]: 分割后的句子列表
    """
    if not text:
        return []
    
    # 使用常见标点符号分割
    sentences = re.split(r'[。！？；；\n\r]+', text)
    return [s.strip() for s in sentences if s.strip()]
