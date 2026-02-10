"""
Kimi API Client
统一的 Kimi API 客户端，使用 Anthropic 格式

使用方法:
    from modules.kimi_client import KimiClient
    
    client = KimiClient()
    response = client.chat([{"role": "user", "content": "你好"}])
"""

import os
import base64
import json
from typing import List, Dict, Any, Optional, Generator, Union
from pathlib import Path
from dataclasses import dataclass
import yaml

# 尝试导入 anthropic 库
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("警告: anthropic 库未安装，请运行: pip install anthropic")


@dataclass
class TextBlock:
    """文本块数据结构"""
    text: str
    x: float  # 左上角 x 坐标（相对于图片宽度的比例，0-1之间）
    y: float  # 左上角 y 坐标（相对于图片高度的比例，0-1之间）
    width: float
    height: float
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "confidence": self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TextBlock':
        return cls(
            text=data.get("text", ""),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 0.0),
            height=data.get("height", 0.0),
            confidence=data.get("confidence", 1.0)
        )


@dataclass
class FormulaResult:
    """公式识别结果"""
    latex: str
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "latex": self.latex,
            "confidence": self.confidence
        }


class KimiClient:
    """
    Kimi API 客户端
    
    使用 Anthropic API 格式访问 Kimi 服务
    """
    
    DEFAULT_BASE_URL = "https://api.kimi.com/coding/"
    DEFAULT_MODEL = "kimi-k2-5"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        timeout: float = 60.0
    ):
        """
        初始化 Kimi 客户端
        
        Args:
            api_key: API Key，默认从 ANTHROPIC_API_KEY 或 KIMI_API_KEY 环境变量读取
            base_url: API Base URL，默认 https://api.kimi.com/coding/
            model: 模型名称，默认 kimi-k2-5
            max_tokens: 最大生成 token 数
            temperature: 采样温度
            timeout: 请求超时时间（秒）
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic 库未安装，请运行: pip install anthropic")
        
        # 尝试从多个来源获取 API Key
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("KIMI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API Key 未提供。请设置 ANTHROPIC_API_KEY 或 KIMI_API_KEY 环境变量，"
                "或在初始化时传入"
            )
        
        # 尝试从多个来源获取 Base URL
        self.base_url = base_url or os.getenv(
            "ANTHROPIC_BASE_URL", 
            os.getenv("KIMI_BASE_URL", self.DEFAULT_BASE_URL)
        )
        
        # 尝试从多个来源获取模型名称
        self.model = model or os.getenv("KIMI_MODEL", self.DEFAULT_MODEL)
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        
        # 初始化 Anthropic 客户端
        self.client = anthropic.Anthropic(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )
    
    @classmethod
    def from_config(cls, config_path: str = "config/config.yaml") -> 'KimiClient':
        """
        从配置文件创建客户端
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            KimiClient: 配置好的客户端实例
        """
        # 加载配置文件
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            kimi_config = config.get('kimi', {})
            return cls(
                api_key=os.getenv("ANTHROPIC_API_KEY") or os.getenv("KIMI_API_KEY"),
                base_url=kimi_config.get('base_url'),
                model=kimi_config.get('model'),
                max_tokens=kimi_config.get('max_tokens', 4096),
                temperature=kimi_config.get('temperature', 0.7),
                timeout=kimi_config.get('timeout', 60.0)
            )
        
        # 如果配置文件不存在，使用环境变量
        return cls()
    
    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        文本补全（单轮对话）
        
        Args:
            prompt: 用户输入提示
            system: 系统提示（可选）
            **kwargs: 额外的 API 参数
            
        Returns:
            str: 模型生成的回复
        """
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, system=system, **kwargs)
    
    def chat(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        多轮对话
        
        Args:
            messages: 消息列表，格式为 [{"role": "user"/"assistant", "content": "..."}]
            system: 系统提示（可选）
            model: 模型名称（可选，默认使用初始化时的设置）
            max_tokens: 最大生成 token 数（可选）
            temperature: 采样温度（可选）
            **kwargs: 额外的 API 参数
            
        Returns:
            str: 模型生成的回复
        """
        try:
            params = {
                "model": model or self.model,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature if temperature is not None else self.temperature,
                "messages": messages,
            }
            
            if system:
                params["system"] = system
            
            # 添加额外参数
            params.update(kwargs)
            
            response = self.client.messages.create(**params)
            
            # 提取文本内容
            text_content = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    text_content += block.text
            
            return text_content
            
        except Exception as e:
            raise Exception(f"Kimi API 调用失败: {e}")
    
    def chat_with_image(
        self,
        prompt: str,
        image_path: str,
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        带视觉输入的对话（单张图片）
        
        Args:
            prompt: 文本提示
            image_path: 图片路径
            system: 系统提示（可选）
            **kwargs: 额外的 API 参数
            
        Returns:
            str: 模型生成的回复
        """
        # 读取图片
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片不存在: {image_path}")
        
        with open(image_path, "rb") as f:
            image_content = f.read()
        
        # 转换为 base64
        image_base64 = base64.b64encode(image_content).decode('utf-8')
        
        # 检测 mime 类型
        mime_type = self._detect_mime_type(image_path)
        
        # 构建视觉消息
        image_message = {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": image_base64
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }
        
        return self.chat([image_message], system=system, **kwargs)
    
    def chat_with_images(
        self,
        prompt: str,
        image_paths: List[str],
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        带多张视觉输入的对话
        
        Args:
            prompt: 文本提示
            image_paths: 图片路径列表
            system: 系统提示（可选）
            **kwargs: 额外的 API 参数
            
        Returns:
            str: 模型生成的回复
        """
        content = []
        
        for image_path in image_paths:
            # 读取图片
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"图片不存在: {image_path}")
            
            with open(image_path, "rb") as f:
                image_content = f.read()
            
            # 转换为 base64
            image_base64 = base64.b64encode(image_content).decode('utf-8')
            mime_type = self._detect_mime_type(image_path)
            
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": image_base64
                }
            })
        
        # 添加文本提示
        content.append({
            "type": "text",
            "text": prompt
        })
        
        image_message = {
            "role": "user",
            "content": content
        }
        
        return self.chat([image_message], system=system, **kwargs)
    
    def ocr(
        self,
        image_path: str,
        return_coordinates: bool = True,
        **kwargs
    ) -> List[TextBlock]:
        """
        OCR 识别图片中的文本
        
        Args:
            image_path: 图片路径
            return_coordinates: 是否返回坐标信息
            **kwargs: 额外的 API 参数
            
        Returns:
            List[TextBlock]: 文本块列表（带坐标）
        """
        ocr_prompt = """请识别图片中的所有文本，并以 JSON 格式返回。
每个文本块需要包含以下信息：
- text: 文本内容
- x: 左上角 x 坐标（相对于图片宽度的比例，0-1之间）
- y: 左上角 y 坐标（相对于图片高度的比例，0-1之间）
- width: 宽度（相对于图片宽度的比例，0-1之间）
- height: 高度（相对于图片高度的比例，0-1之间）
- confidence: 置信度（0-1之间）

请严格按以下 JSON 格式返回，不要包含其他说明文字：
{
  "text_blocks": [
    {
      "text": "文本内容",
      "x": 0.1,
      "y": 0.2,
      "width": 0.3,
      "height": 0.05,
      "confidence": 0.95
    }
  ]
}"""
        
        response = self.chat_with_image(
            prompt=ocr_prompt,
            image_path=image_path,
            system="你是一个专业的 OCR 引擎，擅长识别图片中的文本。",
            **kwargs
        )
        
        # 解析 JSON 响应
        try:
            # 尝试提取 JSON 部分
            json_str = self._extract_json(response)
            data = json.loads(json_str)
            
            text_blocks = []
            for block in data.get("text_blocks", []):
                text_blocks.append(TextBlock(
                    text=block.get("text", ""),
                    x=block.get("x", 0),
                    y=block.get("y", 0),
                    width=block.get("width", 0),
                    height=block.get("height", 0),
                    confidence=block.get("confidence", 1.0)
                ))
            
            return text_blocks
            
        except json.JSONDecodeError as e:
            raise Exception(f"OCR 结果 JSON 解析失败: {e}\n原始响应: {response}")
        except Exception as e:
            raise Exception(f"OCR 处理失败: {e}")
    
    def recognize_formula(
        self,
        image_path: str,
        **kwargs
    ) -> FormulaResult:
        """
        识别数学公式并返回 LaTeX
        
        Args:
            image_path: 图片路径
            **kwargs: 额外的 API 参数
            
        Returns:
            FormulaResult: 包含 LaTeX 字符串和置信度的结果
        """
        formula_prompt = """请识别图片中的数学公式，并以 LaTeX 格式返回。

要求：
1. 只返回 LaTeX 代码，不要包含任何说明文字
2. 使用 $ 或 $$ 包裹公式
3. 确保 LaTeX 语法正确
4. 如果图片中包含多个公式，请分别识别并返回

示例输出格式：
$E = mc^2$

或复杂公式：
$$\\int_{a}^{b} f(x) \\, dx = F(b) - F(a)$$"""
        
        response = self.chat_with_image(
            prompt=formula_prompt,
            image_path=image_path,
            system="你是一个专业的数学公式识别引擎，擅长将图片中的公式转换为 LaTeX 代码。",
            **kwargs
        )
        
        # 清理响应，提取 LaTeX
        latex = self._extract_latex(response)
        return FormulaResult(latex=latex, confidence=0.95)
    
    def understand_image(
        self,
        image_path: str,
        question: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        图像理解 - 分析图片内容并回答问题
        
        Args:
            image_path: 图片路径
            question: 关于图片的问题（可选，默认请求描述图片）
            **kwargs: 额外的 API 参数
            
        Returns:
            str: 模型的回答
        """
        if question is None:
            question = "请详细描述这张图片的内容。"
        
        return self.chat_with_image(
            prompt=question,
            image_path=image_path,
            system="你是一个专业的图像分析助手，擅长理解图片内容并提供详细描述。",
            **kwargs
        )
    
    def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        流式对话
        
        Args:
            messages: 消息列表
            system: 系统提示（可选）
            **kwargs: 额外的 API 参数
            
        Yields:
            str: 生成的文本片段
        """
        try:
            params = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": messages,
                "stream": True,
            }
            
            if system:
                params["system"] = system
            
            params.update(kwargs)
            
            with self.client.messages.stream(**params) as stream:
                for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            raise Exception(f"Kimi API 流式调用失败: {e}")
    
    def _detect_mime_type(self, image_path: str) -> str:
        """检测图片的 MIME 类型"""
        ext = Path(image_path).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp',
        }
        return mime_types.get(ext, 'image/png')
    
    def _extract_json(self, text: str) -> str:
        """从文本中提取 JSON 部分"""
        # 尝试找到 JSON 代码块
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            return text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            return text[start:end].strip()
        
        # 尝试找到 JSON 对象
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return text[start:end+1]
        
        return text
    
    def _extract_latex(self, text: str) -> str:
        """从文本中提取 LaTeX 公式"""
        # 清理文本
        lines = text.strip().split('\n')
        
        # 过滤掉说明文字，保留公式行
        formula_lines = []
        for line in lines:
            line = line.strip()
            # 跳过空行和明显的说明文字
            if not line:
                continue
            if line.startswith('LaTeX:') or line.startswith('公式:'):
                line = line.split(':', 1)[1].strip()
            if '$' in line or '\\' in line:
                formula_lines.append(line)
        
        if formula_lines:
            return '\n'.join(formula_lines)
        
        # 如果没有找到公式标记，返回原始文本
        return text.strip()
    
    def list_models(self) -> List[str]:
        """
        列出可用的模型
        
        Returns:
            List[str]: 可用模型列表
        """
        return [
            "kimi-k2-5",
            "kimi-k2-5-long-context",
        ]
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            Dict: 包含状态信息的字典
        """
        try:
            response = self.complete("Hello", max_tokens=10)
            return {
                "status": "healthy",
                "model": self.model,
                "base_url": self.base_url,
                "message": "API 连接正常"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "model": self.model,
                "base_url": self.base_url,
                "error": str(e)
            }


# 兼容性包装器（模拟 OpenAI API 格式）
class OpenAICompatibleClient:
    """
    OpenAI 兼容客户端
    
    提供与 OpenAI API 类似的接口，内部使用 KimiClient
    """
    
    def __init__(self, **kwargs):
        self.kimi_client = KimiClient(**kwargs)
    
    def create_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建补全（OpenAI 兼容格式）
        
        Returns:
            Dict: 模拟 OpenAI 格式的响应
        """
        response_text = self.kimi_client.chat(messages, model=model, **kwargs)
        
        return {
            "id": "kimi-compat-completion",
            "object": "chat.completion",
            "created": int(__import__('time').time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": -1,
                "completion_tokens": -1,
                "total_tokens": -1
            }
        }


# 便捷函数
def get_client(**kwargs) -> KimiClient:
    """
    获取 KimiClient 实例
    
    Returns:
        KimiClient: 客户端实例
    """
    return KimiClient(**kwargs)


def get_client_from_config(config_path: str = "config/config.yaml") -> KimiClient:
    """
    从配置文件获取 KimiClient 实例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        KimiClient: 配置好的客户端实例
    """
    return KimiClient.from_config(config_path)
