"""
Data Types Module
定义项目中使用的数据类型
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from pathlib import Path


class ElementType(Enum):
    """元素类型枚举"""
    SHAPE = "shape"
    ARROW = "arrow"
    TEXT = "text"
    ICON = "icon"
    IMAGE = "image"
    BACKGROUND = "background"


class ProcessingStatus(Enum):
    """处理状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BoundingBox:
    """边界框"""
    x: float
    y: float
    width: float
    height: float
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "BoundingBox":
        return cls(
            x=data.get("x", 0),
            y=data.get("y", 0),
            width=data.get("width", 0),
            height=data.get("height", 0)
        )


@dataclass
class Element:
    """图表元素"""
    element_id: str
    element_type: ElementType
    bbox: BoundingBox
    confidence: float = 1.0
    content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.element_id,
            "type": self.element_type.value,
            "bbox": self.bbox.to_dict(),
            "confidence": self.confidence,
            "content": self.content,
            "metadata": self.metadata
        }


@dataclass
class SegmentationResult:
    """分割结果"""
    elements: List[Element] = field(default_factory=list)
    original_image_path: Optional[Path] = None
    processed_image_path: Optional[Path] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_element(self, element: Element):
        self.elements.append(element)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "elements": [e.to_dict() for e in self.elements],
            "element_count": len(self.elements),
            "metadata": self.metadata
        }


@dataclass
class ProcessingTask:
    """处理任务"""
    task_id: str
    status: ProcessingStatus
    input_path: Optional[Path] = None
    output_path: Optional[Path] = None
    result: Optional[SegmentationResult] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# 图层级别枚举
class LayerLevel(Enum):
    """图层级别枚举"""
    BACKGROUND = 0
    IMAGE = 1
    SHAPE = 2
    ICON = 3
    TEXT = 4
    ARROW = 5


def get_layer_level(element_type: ElementType) -> LayerLevel:
    """根据元素类型获取图层级别"""
    mapping = {
        ElementType.BACKGROUND: LayerLevel.BACKGROUND,
        ElementType.IMAGE: LayerLevel.IMAGE,
        ElementType.SHAPE: LayerLevel.SHAPE,
        ElementType.ICON: LayerLevel.ICON,
        ElementType.TEXT: LayerLevel.TEXT,
        ElementType.ARROW: LayerLevel.ARROW,
    }
    return mapping.get(element_type, LayerLevel.SHAPE)


@dataclass
class ElementInfo:
    """元素信息（兼容旧代码）"""
    element_id: str
    element_type: ElementType
    bbox: BoundingBox
    confidence: float = 1.0
    content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# 别名定义（兼容旧代码）
ProcessingContext = ProcessingTask
ProcessingResult = SegmentationResult
