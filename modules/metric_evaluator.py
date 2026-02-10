"""
Metric Evaluator Module
评估指标计算
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .base import BaseProcessor
from .data_types import Element, SegmentationResult, BoundingBox


@dataclass
class EvaluationMetrics:
    """评估指标"""
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    iou_mean: float = 0.0
    iou_median: float = 0.0
    ap: float = 0.0  # Average Precision
    ar: float = 0.0  # Average Recall
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "iou_mean": self.iou_mean,
            "iou_median": self.iou_median,
            "ap": self.ap,
            "ar": self.ar
        }


class MetricEvaluator(BaseProcessor):
    """评估指标计算器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.iou_threshold = self.get_config("iou_threshold", 0.5)
        self.confidence_threshold = self.get_config("confidence_threshold", 0.5)
    
    def process(
        self, 
        input_data: Tuple[SegmentationResult, SegmentationResult], 
        **kwargs
    ) -> EvaluationMetrics:
        """
        计算评估指标
        
        Args:
            input_data: (预测结果, 真实标注)
            **kwargs: 额外参数
            
        Returns:
            EvaluationMetrics: 评估指标
        """
        pred_result, gt_result = input_data
        
        metrics = EvaluationMetrics()
        
        # 计算 IoU 矩阵
        iou_matrix = self._compute_iou_matrix(pred_result.elements, gt_result.elements)
        
        # 计算精确率和召回率
        tp, fp, fn = self._compute_tp_fp_fn(
            pred_result.elements, 
            gt_result.elements, 
            iou_matrix
        )
        
        metrics.precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        metrics.recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        
        if metrics.precision + metrics.recall > 0:
            metrics.f1_score = 2 * (metrics.precision * metrics.recall) / \
                              (metrics.precision + metrics.recall)
        
        # 计算 IoU 统计
        if iou_matrix.size > 0:
            metrics.iou_mean = float(np.mean(iou_matrix))
            metrics.iou_median = float(np.median(iou_matrix))
        
        return metrics
    
    def _compute_iou_matrix(
        self, 
        pred_elements: List[Element], 
        gt_elements: List[Element]
    ) -> np.ndarray:
        """
        计算 IoU 矩阵
        
        Args:
            pred_elements: 预测元素
            gt_elements: 真实标注元素
            
        Returns:
            np.ndarray: IoU 矩阵
        """
        n_pred = len(pred_elements)
        n_gt = len(gt_elements)
        
        iou_matrix = np.zeros((n_pred, n_gt))
        
        for i, pred in enumerate(pred_elements):
            for j, gt in enumerate(gt_elements):
                iou_matrix[i, j] = self._calculate_iou(pred.bbox, gt.bbox)
        
        return iou_matrix
    
    def _calculate_iou(self, bbox1: BoundingBox, bbox2: BoundingBox) -> float:
        """
        计算两个边界框的 IoU
        
        Args:
            bbox1: 第一个边界框
            bbox2: 第二个边界框
            
        Returns:
            float: IoU 值
        """
        x1 = max(bbox1.x, bbox2.x)
        y1 = max(bbox1.y, bbox2.y)
        x2 = min(bbox1.x + bbox1.width, bbox2.x + bbox2.width)
        y2 = min(bbox1.y + bbox1.height, bbox2.y + bbox2.height)
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        
        area1 = bbox1.width * bbox1.height
        area2 = bbox2.width * bbox2.height
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _compute_tp_fp_fn(
        self,
        pred_elements: List[Element],
        gt_elements: List[Element],
        iou_matrix: np.ndarray
    ) -> Tuple[int, int, int]:
        """
        计算 TP, FP, FN
        
        Args:
            pred_elements: 预测元素
            gt_elements: 真实标注元素
            iou_matrix: IoU 矩阵
            
        Returns:
            Tuple[int, int, int]: (TP, FP, FN)
        """
        if iou_matrix.size == 0:
            return 0, len(pred_elements), len(gt_elements)
        
        matched_gt = set()
        tp = 0
        
        for i, pred in enumerate(pred_elements):
            if pred.confidence < self.confidence_threshold:
                continue
            
            best_iou = 0
            best_gt = -1
            
            for j in range(len(gt_elements)):
                if j in matched_gt:
                    continue
                
                if iou_matrix[i, j] > best_iou:
                    best_iou = iou_matrix[i, j]
                    best_gt = j
            
            if best_iou >= self.iou_threshold:
                tp += 1
                matched_gt.add(best_gt)
        
        fp = len(pred_elements) - tp
        fn = len(gt_elements) - len(matched_gt)
        
        return tp, fp, fn
    
    def evaluate_batch(
        self,
        predictions: List[SegmentationResult],
        ground_truths: List[SegmentationResult]
    ) -> Dict[str, float]:
        """
        批量评估
        
        Args:
            predictions: 预测结果列表
            ground_truths: 真实标注列表
            
        Returns:
            Dict[str, float]: 平均指标
        """
        all_metrics = []
        
        for pred, gt in zip(predictions, ground_truths):
            metrics = self.process((pred, gt))
            all_metrics.append(metrics)
        
        # 计算平均值
        avg_metrics = {
            "precision": np.mean([m.precision for m in all_metrics]),
            "recall": np.mean([m.recall for m in all_metrics]),
            "f1_score": np.mean([m.f1_score for m in all_metrics]),
            "iou_mean": np.mean([m.iou_mean for m in all_metrics]),
            "iou_median": np.mean([m.iou_median for m in all_metrics]),
        }
        
        return avg_metrics
