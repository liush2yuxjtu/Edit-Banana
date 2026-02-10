"""
Edit-Banana 模块包
"""

# 核心处理器
from .sam3_info_extractor import Sam3InfoExtractor, PromptGroup
from .icon_picture_processor import IconPictureProcessor, UpscaleModel, SPANDREL_AVAILABLE
from .basic_shape_processor import BasicShapeProcessor
from .arrow_processor import ArrowProcessor
from .xml_merger import XMLMerger
from .metric_evaluator import MetricEvaluator
from .refinement_processor import RefinementProcessor

# 数据类型
from .data_types import (
    ElementType, ProcessingStatus, BoundingBox, Element,
    SegmentationResult, ProcessingTask, LayerLevel, get_layer_level,
    ElementInfo, ProcessingContext, ProcessingResult
)

# Kimi 客户端
from .kimi_client import KimiClient, TextBlock, FormulaResult, get_client

# 文本处理（带可用性检查）
try:
    from .text.text_render import TextRestorer
except ImportError:
    TextRestorer = None

__all__ = [
    # 核心处理器
    'Sam3InfoExtractor', 'PromptGroup',
    'IconPictureProcessor', 'UpscaleModel', 'SPANDREL_AVAILABLE',
    'BasicShapeProcessor', 'ArrowProcessor',
    'XMLMerger', 'MetricEvaluator', 'RefinementProcessor',
    # 数据类型
    'ElementType', 'ProcessingStatus', 'BoundingBox', 'Element',
    'SegmentationResult', 'ProcessingTask', 'LayerLevel', 'get_layer_level',
    'ElementInfo', 'ProcessingContext', 'ProcessingResult',
    # Kimi 客户端
    'KimiClient', 'TextBlock', 'FormulaResult', 'get_client',
    # 文本处理
    'TextRestorer',
]
