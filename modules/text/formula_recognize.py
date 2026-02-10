"""
公式识别模块 - 使用 Kimi 视觉模型
支持数学公式识别和 LaTeX 转换
"""

from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import numpy as np
from PIL import Image

# 导入 Kimi 客户端
try:
    from modules.llm_client import get_kimi_client
    KIMI_AVAILABLE = True
except ImportError:
    KIMI_AVAILABLE = False


class FormulaType(Enum):
    """公式类型"""
    INLINE = "inline"           # 行内公式 $...$
    DISPLAY = "display"         # 独立公式 $$...$$
    EQUATION = "equation"       # 编号公式
    MATRIX = "matrix"           # 矩阵
    FRACTION = "fraction"       # 分数
    INTEGRAL = "integral"       # 积分
    SUMMATION = "summation"     # 求和
    LIMIT = "limit"             # 极限
    UNKNOWN = "unknown"         # 未知


@dataclass
class FormulaResult:
    """公式识别结果"""
    latex: str                          # LaTeX 代码
    formula_type: FormulaType           # 公式类型
    confidence: float                   # 置信度
    raw_text: Optional[str] = None      # 原始文本（如果不是公式）
    error_msg: Optional[str] = None     # 错误信息


class KimiFormulaRecognizer:
    """
    基于 Kimi 视觉模型的公式识别器
    
    特点：
    - 高精度数学公式识别
    - 支持复杂公式结构
    - 自动 LaTeX 转换
    - 公式类型分类
    """
    
    def __init__(self, confidence_threshold: float = 0.7):
        """
        初始化公式识别器
        
        Args:
            confidence_threshold: 置信度阈值
        """
        if not KIMI_AVAILABLE:
            raise ImportError("Kimi client not available")
        
        self.client = get_kimi_client()
        self.confidence_threshold = confidence_threshold
        
        # LaTeX 验证模式
        self.latex_patterns = {
            'inline': re.compile(r'\$(.+?)\$'),
            'display': re.compile(r'\$\$(.+?)\$\$'),
            'equation': re.compile(r'\\begin\{equation\}(.+?)\\end\{equation\}'),
            'align': re.compile(r'\\begin\{align\}(.+?)\\end\{align\}'),
        }
    
    def recognize(self, image: Union[str, np.ndarray, Image.Image]) -> FormulaResult:
        """
        识别图片中的公式
        
        Args:
            image: 输入图片
        
        Returns:
            FormulaResult: 识别结果
        """
        try:
            # 使用 Kimi 识别公式
            latex = self.client.recognize_formula(image, temperature=0.1)
            
            # 清理和验证 LaTeX
            latex = self._clean_latex(latex)
            
            # 判断公式类型
            formula_type = self._classify_formula(latex)
            
            # 评估置信度
            confidence = self._evaluate_confidence(latex, formula_type)
            
            return FormulaResult(
                latex=latex,
                formula_type=formula_type,
                confidence=confidence
            )
            
        except Exception as e:
            return FormulaResult(
                latex="",
                formula_type=FormulaType.UNKNOWN,
                confidence=0.0,
                error_msg=str(e)
            )
    
    def recognize_batch(self, images: List[Union[str, np.ndarray, Image.Image]]) -> List[FormulaResult]:
        """
        批量识别公式
        
        Args:
            images: 图片列表
        
        Returns:
            List[FormulaResult]: 识别结果列表
        """
        results = []
        for image in images:
            result = self.recognize(image)
            results.append(result)
        return results
    
    def is_formula(self, text: str) -> bool:
        """
        判断文本是否包含公式
        
        Args:
            text: 输入文本
        
        Returns:
            bool: 是否为公式
        """
        # 检查是否包含 LaTeX 标记
        if '$' in text or '\\' in text:
            return True
        
        # 检查数学符号
        math_symbols = [
            '=', '+', '-', '*', '/', '^', '_', '√', '∫', '∑', '∏', '∂', '∇',
            '∞', '±', '×', '÷', '≤', '≥', '≠', '≈', '∈', '∉', '⊂', '⊃',
            'α', 'β', 'γ', 'δ', 'ε', 'θ', 'λ', 'μ', 'π', 'ρ', 'σ', 'φ', 'ω',
            'sin', 'cos', 'tan', 'log', 'ln', 'exp', 'lim', 'max', 'min'
        ]
        
        return any(symbol in text for symbol in math_symbols)
    
    def validate_latex(self, latex: str) -> Tuple[bool, Optional[str]]:
        """
        验证 LaTeX 语法
        
        Args:
            latex: LaTeX 代码
        
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误信息)
        """
        errors = []
        
        # 检查括号匹配
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        
        for char in latex:
            if char in brackets:
                stack.append(char)
            elif char in brackets.values():
                if not stack:
                    errors.append(f"Unmatched closing bracket: {char}")
                else:
                    opening = stack.pop()
                    if brackets[opening] != char:
                        errors.append(f"Mismatched brackets: {opening} and {char}")
        
        if stack:
            errors.append(f"Unmatched opening brackets: {stack}")
        
        # 检查环境匹配
        env_pattern = re.compile(r'\\begin\{(\w+)\}')
        for match in env_pattern.finditer(latex):
            env_name = match.group(1)
            end_pattern = f"\\end{{{env_name}}}"
            if end_pattern not in latex:
                errors.append(f"Unclosed environment: {env_name}")
        
        # 检查常见错误
        common_errors = [
            ('\\frac{', 'Fraction missing numerator/denominator'),
            ('\\sqrt{', 'Sqrt missing argument'),
            ('\\int_{', 'Integral missing bounds'),
        ]
        
        for pattern, msg in common_errors:
            if pattern in latex:
                # 简单检查是否有对应的闭合
                start = latex.find(pattern)
                if start != -1:
                    remaining = latex[start + len(pattern):]
                    if not remaining or remaining[0] == '}':
                        errors.append(msg)
        
        if errors:
            return False, "; ".join(errors)
        
        return True, None
    
    def fix_latex(self, latex: str) -> str:
        """
        自动修复常见的 LaTeX 错误
        
        Args:
            latex: 原始 LaTeX
        
        Returns:
            str: 修复后的 LaTeX
        """
        fixed = latex
        
        # 修复未闭合的括号
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        
        for char in fixed:
            if char in brackets:
                stack.append(char)
            elif char in brackets.values():
                if stack and brackets[stack[-1]] == char:
                    stack.pop()
        
        # 添加缺失的闭合括号
        while stack:
            opening = stack.pop()
            fixed += brackets[opening]
        
        # 修复环境
        env_pattern = re.compile(r'\\begin\{(\w+)\}')
        found_envs = set()
        for match in env_pattern.finditer(fixed):
            found_envs.add(match.group(1))
        
        for env_name in found_envs:
            end_pattern = f"\\end{{{env_name}}}"
            begin_count = fixed.count(f"\\begin{{{env_name}}}")
            end_count = fixed.count(end_pattern)
            
            while end_count < begin_count:
                fixed += end_pattern
                end_count += 1
        
        return fixed
    
    def to_mathml(self, latex: str) -> str:
        """
        将 LaTeX 转换为 MathML（简单实现）
        
        Args:
            latex: LaTeX 代码
        
        Returns:
            str: MathML
        """
        # 这是一个简化实现，完整实现需要使用专门的库
        # 如 latex2mathml 或 MathJax
        mathml = f'<math xmlns="http://www.w3.org/1998/Math/MathML">\n'
        mathml += f'  <mrow>{latex}</mrow>\n'
        mathml += '</math>'
        return mathml
    
    def _clean_latex(self, latex: str) -> str:
        """
        清理 LaTeX 代码
        
        Args:
            latex: 原始 LaTeX
        
        Returns:
            str: 清理后的 LaTeX
        """
        # 移除解释性文字
        lines = latex.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # 跳过空行和解释
            if not line:
                continue
            if line.lower().startswith('this is') or line.lower().startswith('the formula'):
                continue
            cleaned_lines.append(line)
        
        cleaned = ' '.join(cleaned_lines)
        
        # 确保有正确的包裹
        if not cleaned.startswith('$') and not cleaned.startswith('\\['):
            # 检查是否是独立公式
            if '\n' in latex or len(cleaned) > 50:
                cleaned = f"$${cleaned}$$"
            else:
                cleaned = f"${cleaned}$"
        
        return cleaned
    
    def _classify_formula(self, latex: str) -> FormulaType:
        """
        分类公式类型
        
        Args:
            latex: LaTeX 代码
        
        Returns:
            FormulaType: 公式类型
        """
        # 检查各种模式
        if '\\begin{equation}' in latex or '\\begin{align}' in latex:
            return FormulaType.EQUATION
        
        if '\\begin{matrix}' in latex or '\\begin{bmatrix}' in latex or '\\begin{pmatrix}' in latex:
            return FormulaType.MATRIX
        
        if '\\frac' in latex or '\\dfrac' in latex:
            return FormulaType.FRACTION
        
        if '\\int' in latex or '\\iint' in latex or '\\iiint' in latex:
            return FormulaType.INTEGRAL
        
        if '\\sum' in latex or '\\prod' in latex:
            return FormulaType.SUMMATION
        
        if '\\lim' in latex:
            return FormulaType.LIMIT
        
        if latex.startswith('$$') and latex.endswith('$$'):
            return FormulaType.DISPLAY
        
        if latex.startswith('$') and latex.endswith('$'):
            return FormulaType.INLINE
        
        return FormulaType.UNKNOWN
    
    def _evaluate_confidence(self, latex: str, formula_type: FormulaType) -> float:
        """
        评估识别结果的置信度
        
        Args:
            latex: LaTeX 代码
            formula_type: 公式类型
        
        Returns:
            float: 置信度 (0-1)
        """
        confidence = 0.8  # 基础置信度
        
        # 检查语法有效性
        is_valid, error = self.validate_latex(latex)
        if is_valid:
            confidence += 0.1
        else:
            confidence -= 0.2
        
        # 根据公式类型调整
        if formula_type != FormulaType.UNKNOWN:
            confidence += 0.05
        
        # 检查是否有明显错误
        if '...' in latex or '[formula]' in latex.lower():
            confidence -= 0.3
        
        # 检查长度是否合理
        if len(latex) < 5:
            confidence -= 0.2
        
        return max(0.0, min(1.0, confidence))
    
    def extract_formulas_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        从文本中提取公式
        
        Args:
            text: 包含公式的文本
        
        Returns:
            List[Dict]: 公式列表
        """
        formulas = []
        
        # 匹配 $...$ 格式的行内公式
        inline_pattern = re.compile(r'\$(.+?)\$')
        for match in inline_pattern.finditer(text):
            formulas.append({
                'type': 'inline',
                'latex': match.group(1),
                'full': match.group(0),
                'start': match.start(),
                'end': match.end()
            })
        
        # 匹配 $$...$$ 格式的独立公式
        display_pattern = re.compile(r'\$\$(.+?)\$\$')
        for match in display_pattern.finditer(text):
            formulas.append({
                'type': 'display',
                'latex': match.group(1),
                'full': match.group(0),
                'start': match.start(),
                'end': match.end()
            })
        
        return formulas


# 便捷函数
def recognize_formula(image: Union[str, np.ndarray, Image.Image]) -> str:
    """
    识别公式（便捷函数）
    
    Args:
        image: 输入图片
    
    Returns:
        str: LaTeX 公式
    """
    recognizer = KimiFormulaRecognizer()
    result = recognizer.recognize(image)
    return result.latex if result.confidence > 0.5 else ""


def is_formula_text(text: str) -> bool:
    """
    判断是否为公式文本（便捷函数）
    
    Args:
        text: 输入文本
    
        Returns:
        bool: 是否为公式
    """
    recognizer = KimiFormulaRecognizer()
    return recognizer.is_formula(text)


def validate_and_fix(latex: str) -> str:
    """
    验证并修复 LaTeX（便捷函数）
    
    Args:
        latex: 输入 LaTeX
    
    Returns:
        str: 修复后的 LaTeX
    """
    recognizer = KimiFormulaRecognizer()
    is_valid, error = recognizer.validate_latex(latex)
    
    if is_valid:
        return latex
    else:
        return recognizer.fix_latex(latex)
