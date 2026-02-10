"""
Kimi 公式识别模块
使用 Kimi 视觉模型识别数学公式并转换为 LaTeX

功能：
- 识别图片中的数学公式
- 返回 LaTeX 格式的公式

使用方法:
    from modules.text.kimi_formula import KimiFormulaRecognizer
    
    recognizer = KimiFormulaRecognizer()
    latex = recognizer.recognize("formula.png")
    print(latex)  # 输出: $E = mc^2$
"""

import os
import re
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path

from modules.kimi_client import KimiClient, get_client


@dataclass
class Formula:
    """公式数据结构"""
    latex: str
    confidence: float = 1.0
    bbox: Optional[Dict[str, float]] = None  # 边界框信息（可选）
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "latex": self.latex,
            "confidence": self.confidence,
            "bbox": self.bbox
        }
    
    def is_valid(self) -> bool:
        """检查公式是否有效"""
        if not self.latex:
            return False
        # 检查是否包含 LaTeX 标记
        return '$' in self.latex or '\\' in self.latex
    
    def to_inline_latex(self) -> str:
        """转换为行内 LaTeX 格式"""
        latex = self.latex.strip()
        # 移除现有的 $ 包裹
        if latex.startswith('$$') and latex.endswith('$$'):
            latex = latex[2:-2].strip()
        elif latex.startswith('$') and latex.endswith('$'):
            latex = latex[1:-1].strip()
        # 添加单行内 $ 包裹
        return f"${latex}$"
    
    def to_display_latex(self) -> str:
        """转换为行间 LaTeX 格式"""
        latex = self.latex.strip()
        # 移除现有的 $ 包裹
        if latex.startswith('$$') and latex.endswith('$$'):
            return latex
        if latex.startswith('$') and latex.endswith('$'):
            latex = latex[1:-1].strip()
        # 添加行间 $$ 包裹
        return f"$${latex}$$"


@dataclass
class FormulaRecognitionResult:
    """公式识别结果"""
    formulas: List[Formula]
    raw_response: str = ""
    image_path: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "formulas": [f.to_dict() for f in self.formulas],
            "raw_response": self.raw_response,
            "image_path": self.image_path
        }
    
    def get_latex_list(self) -> List[str]:
        """获取所有 LaTeX 字符串列表"""
        return [f.latex for f in self.formulas if f.is_valid()]
    
    def to_text(self, separator: str = "\n") -> str:
        """将所有公式合并为一个字符串"""
        return separator.join(self.get_latex_list())
    
    def filter_by_confidence(self, min_confidence: float = 0.6) -> List[Formula]:
        """按置信度过滤公式"""
        return [f for f in self.formulas if f.confidence >= min_confidence]


class KimiFormulaRecognizer:
    """
    Kimi 公式识别器
    
    使用 Kimi 视觉模型识别图片中的数学公式
    """
    
    # 公式识别提示词
    DEFAULT_FORMULA_PROMPT = """请识别图片中的数学公式，并以 LaTeX 格式返回。

识别要求：
1. 准确识别所有数学符号、运算符、上下标、分数、积分、矩阵等
2. 正确处理数学公式的结构和层次关系
3. 识别希腊字母、特殊符号等
4. 如果图片中包含多个公式，请分别识别

输出要求：
1. 只返回 LaTeX 代码，不要包含任何说明文字
2. 行内公式使用 $ 包裹，如: $E = mc^2$
3. 行间公式使用 $$ 包裹，如: $$\\int_{a}^{b} f(x) \\, dx$$
4. 确保 LaTeX 语法正确，可以直接渲染

请按以下 JSON 格式返回（如果可能）：
{
  "formulas": [
    {
      "latex": "LaTeX 代码",
      "confidence": 0.95
    }
  ]
}

如果无法返回 JSON，请直接返回 LaTeX 代码，每行一个公式。"""
    
    DEFAULT_SYSTEM_PROMPT = "你是一个专业的数学公式识别引擎，擅长将图片中的数学公式转换为准确的 LaTeX 代码。"
    
    def __init__(
        self,
        client: Optional[KimiClient] = None,
        min_confidence: float = 0.6,
        formula_prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **client_kwargs
    ):
        """
        初始化公式识别器
        
        Args:
            client: KimiClient 实例（可选，默认自动创建）
            min_confidence: 最小置信度阈值
            formula_prompt: 自定义公式识别提示词
            system_prompt: 自定义系统提示词
            **client_kwargs: 传递给 KimiClient 的参数
        """
        self.client = client or get_client(**client_kwargs)
        self.min_confidence = min_confidence
        self.formula_prompt = formula_prompt or self.DEFAULT_FORMULA_PROMPT
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
    
    def recognize(
        self,
        image_path: Union[str, Path],
        **kwargs
    ) -> FormulaRecognitionResult:
        """
        识别图片中的数学公式
        
        Args:
            image_path: 图片路径
            **kwargs: 额外的 API 参数
            
        Returns:
            FormulaRecognitionResult: 公式识别结果
        """
        image_path = str(image_path)
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片不存在: {image_path}")
        
        # 调用 Kimi API 进行公式识别
        response = self.client.chat_with_image(
            prompt=self.formula_prompt,
            image_path=image_path,
            system=self.system_prompt,
            **kwargs
        )
        
        # 解析响应
        formulas = self._parse_formula_response(response)
        
        # 过滤低置信度的结果
        filtered_formulas = [
            f for f in formulas 
            if f.confidence >= self.min_confidence and f.is_valid()
        ]
        
        return FormulaRecognitionResult(
            formulas=filtered_formulas,
            raw_response=response,
            image_path=image_path
        )
    
    def recognize_batch(
        self,
        image_paths: List[Union[str, Path]],
        **kwargs
    ) -> List[FormulaRecognitionResult]:
        """
        批量识别多张图片中的公式
        
        Args:
            image_paths: 图片路径列表
            **kwargs: 额外的 API 参数
            
        Returns:
            List[FormulaRecognitionResult]: 公式识别结果列表
        """
        results = []
        for path in image_paths:
            try:
                result = self.recognize(path, **kwargs)
                results.append(result)
            except Exception as e:
                # 记录错误但继续处理其他图片
                results.append(FormulaRecognitionResult(
                    formulas=[],
                    raw_response=f"错误: {str(e)}",
                    image_path=str(path)
                ))
        
        return results
    
    def recognize_to_latex(
        self,
        image_path: Union[str, Path],
        **kwargs
    ) -> str:
        """
        识别公式并返回 LaTeX 字符串（仅返回第一个有效公式）
        
        Args:
            image_path: 图片路径
            **kwargs: 额外的 API 参数
            
        Returns:
            str: LaTeX 字符串
        """
        result = self.recognize(image_path, **kwargs)
        if result.formulas:
            return result.formulas[0].latex
        return ""
    
    def validate_latex(self, latex: str) -> bool:
        """
        简单验证 LaTeX 语法
        
        Args:
            latex: LaTeX 字符串
            
        Returns:
            bool: 是否有效
        """
        # 检查基本的 LaTeX 语法规则
        latex = latex.strip()
        
        # 必须有 $ 或 $$ 包裹，或包含 \ 命令
        if not ('$' in latex or '\\' in latex):
            return False
        
        # 检查括号是否匹配
        counts = {
            '{': latex.count('{'),
            '}': latex.count('}'),
            '[': latex.count('['),
            ']': latex.count(']'),
            '(': latex.count('('),
            ')': latex.count(')'),
        }
        
        if counts['{'] != counts['}']:
            return False
        
        # 检查 $ 是否配对
        dollar_count = latex.count('$')
        if dollar_count % 2 != 0:
            return False
        
        return True
    
    def _parse_formula_response(self, response: str) -> List[Formula]:
        """
        解析公式识别 API 响应
        
        Args:
            response: API 返回的原始响应
            
        Returns:
            List[Formula]: 公式列表
        """
        formulas = []
        
        try:
            # 尝试解析 JSON 格式
            json_str = self._extract_json(response)
            data = json.loads(json_str)
            
            if "formulas" in data:
                for formula_data in data["formulas"]:
                    formula = Formula(
                        latex=formula_data.get("latex", ""),
                        confidence=formula_data.get("confidence", 0.95),
                        bbox=formula_data.get("bbox")
                    )
                    formulas.append(formula)
                return formulas
            
        except (json.JSONDecodeError, Exception):
            pass
        
        # 备用：从文本中提取 LaTeX 公式
        formulas = self._extract_latex_from_text(response)
        
        return formulas
    
    def _extract_json(self, text: str) -> str:
        """从文本中提取 JSON 部分"""
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end == -1:
                end = len(text)
            return text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end == -1:
                end = len(text)
            return text[start:end].strip()
        
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return text[start:end+1]
        
        return text
    
    def _extract_latex_from_text(self, text: str) -> List[Formula]:
        """
        从文本中提取 LaTeX 公式
        
        支持多种格式：
        - $$...$$ 行间公式
        - $...$ 行内公式
        - \\[...\\] 行间公式
        - \\(...\\) 行内公式
        """
        formulas = []
        
        # 匹配 $$...$$ 格式
        display_pattern = r'\$\$(.*?)\$\$'
        for match in re.finditer(display_pattern, text, re.DOTALL):
            latex = match.group(0).strip()
            formulas.append(Formula(latex=latex, confidence=0.9))
        
        # 匹配 $...$ 格式（非贪婪）
        inline_pattern = r'\$([^$\n]+?)\$'
        for match in re.finditer(inline_pattern, text):
            latex = match.group(0).strip()
            formulas.append(Formula(latex=latex, confidence=0.85))
        
        # 如果没有找到 $ 包裹的公式，尝试找包含 \ 的行
        if not formulas:
            for line in text.strip().split('\n'):
                line = line.strip()
                if '\\' in line and len(line) > 3:
                    formulas.append(Formula(latex=f"${line}$", confidence=0.7))
        
        return formulas
    
    def health_check(self) -> Dict[str, Any]:
        """
        检查公式识别服务健康状态
        
        Returns:
            Dict: 状态信息
        """
        return self.client.health_check()


# 便捷函数
def recognize_formula(
    image_path: Union[str, Path],
    **kwargs
) -> FormulaRecognitionResult:
    """
    便捷函数：识别图片中的数学公式
    
    Args:
        image_path: 图片路径
        **kwargs: 额外参数
        
    Returns:
        FormulaRecognitionResult: 公式识别结果
    """
    recognizer = KimiFormulaRecognizer()
    return recognizer.recognize(image_path, **kwargs)


def recognize_to_latex(
    image_path: Union[str, Path],
    **kwargs
) -> str:
    """
    便捷函数：识别公式并返回 LaTeX 字符串
    
    Args:
        image_path: 图片路径
        **kwargs: 额外参数
        
    Returns:
        str: LaTeX 字符串
    """
    recognizer = KimiFormulaRecognizer()
    return recognizer.recognize_to_latex(image_path, **kwargs)
