"""
统一 LLM 客户端
支持 Kimi API（Anthropic 格式）
"""

import os
import base64
import io
import re
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
from abc import ABC, abstractmethod

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

import numpy as np
from PIL import Image


class BaseLLMClient(ABC):
    """LLM 客户端基类"""
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """发送聊天请求"""
        pass
    
    @abstractmethod
    def chat_with_image(self, image: Union[str, np.ndarray, Image.Image], 
                       prompt: str, **kwargs) -> str:
        """发送带图片的聊天请求"""
        pass


class KimiClient(BaseLLMClient):
    """Kimi API 客户端（Anthropic 格式）"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package required. Install: pip install anthropic")
        
        self.api_key = api_key or os.getenv("KIMI_API_KEY")
        self.base_url = base_url or os.getenv("KIMI_BASE_URL", "https://api.kimi.com/coding/")
        self.model = model or os.getenv("KIMI_MODEL", "kimi-v1")
        
        if not self.api_key:
            raise ValueError("KIMI_API_KEY not set")
        
        self.client = anthropic.Anthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def _encode_image(self, image: Union[str, np.ndarray, Image.Image]) -> Dict[str, Any]:
        """将图片编码为 Anthropic 格式"""
        if isinstance(image, str):
            # 文件路径
            if image.startswith('data:image'):
                # base64 URL
                match = re.match(r'data:image/([^;]+);base64,(.+)', image)
                if match:
                    media_type = f"image/{match.group(1)}"
                    return {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": match.group(2)
                        }
                    }
                raise ValueError("Invalid data URL format")
            else:
                # 文件路径
                path = Path(image)
                if not path.exists():
                    raise FileNotFoundError(f"Image not found: {image}")
                
                ext = path.suffix.lower()
                media_type_map = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'}
                media_type = media_type_map.get(ext, 'image/png')
                
                with open(path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode()
                
                return {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_data
                    }
                }
        
        elif isinstance(image, np.ndarray):
            # numpy array
            pil_image = Image.fromarray(image)
            buffer = io.BytesIO()
            pil_image.save(buffer, format="PNG")
            image_data = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_data
                }
            }
        
        elif isinstance(image, Image.Image):
            # PIL Image
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            image_data = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_data
                }
            }
        
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")
    
    def chat(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """
        发送纯文本聊天请求
        
        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}, ...]
            **kwargs: 额外参数 (temperature, max_tokens等)
        
        Returns:
            str: 模型回复
        """
        system_msg = ""
        chat_messages = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_msg = content
            else:
                chat_messages.append({"role": role, "content": content})
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7),
            system=system_msg if system_msg else None,
            messages=chat_messages
        )
        
        return response.content[0].text
    
    def chat_with_image(self, image: Union[str, np.ndarray, Image.Image], 
                       prompt: str, **kwargs) -> str:
        """
        发送带图片的聊天请求
        
        Args:
            image: 图片路径、numpy数组或PIL Image
            prompt: 文字提示
            **kwargs: 额外参数
        
        Returns:
            str: 模型回复
        """
        image_content = self._encode_image(image)
        
        messages = [{
            "role": "user",
            "content": [
                image_content,
                {"type": "text", "text": prompt}
            ]
        }]
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", kwargs.get("temp", 0.3)),
            messages=messages
        )
        
        return response.content[0].text
    
    def vision_ocr(self, image: Union[str, np.ndarray, Image.Image], 
                   detail_level: str = "detailed", **kwargs) -> List[Dict[str, Any]]:
        """
        使用视觉模型进行 OCR
        
        Args:
            image: 输入图片
            detail_level: "detailed" (详细，带坐标) 或 "simple" (仅文字)
            **kwargs: 额外参数
        
        Returns:
            List[Dict]: 识别的文字列表，每项包含 text, bbox, confidence
        """
        if detail_level == "detailed":
            prompt = """请识别图片中的所有文字，并以 JSON 格式返回。
要求：
1. 识别所有可见的文字内容
2. 对每个文字区域，提供大致的边界框坐标 (x, y, width, height)
3. 估计置信度 (0-1)

返回格式：
{
  "texts": [
    {"text": "文字内容", "bbox": {"x": 10, "y": 20, "width": 100, "height": 30}, "confidence": 0.95},
    ...
  ]
}

只返回 JSON，不要其他解释。"""
        else:
            prompt = """请识别图片中的所有文字，直接列出所有文字内容，每行一个。"""
        
        response = self.chat_with_image(image, prompt, temperature=0.1, **kwargs)
        
        # 解析 JSON 响应
        try:
            import json
            # 提取 JSON 部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("texts", [])
        except Exception:
            pass
        
        # 简单模式或解析失败，返回简单格式
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        return [{"text": line, "bbox": {"x": 0, "y": 0, "width": 0, "height": 0}, "confidence": 0.8} 
                for line in lines]
    
    def recognize_formula(self, image: Union[str, np.ndarray, Image.Image], 
                         **kwargs) -> str:
        """
        识别数学公式并转换为 LaTeX
        
        Args:
            image: 公式图片
            **kwargs: 额外参数
        
        Returns:
            str: LaTeX 格式公式
        """
        prompt = """请识别图片中的数学公式，并将其转换为 LaTeX 格式。

要求：
1. 如果是数学公式，使用标准的 LaTeX 语法
2. 使用 $ 包裹行内公式，$$ 包裹独立公式
3. 如果是纯文本，直接返回文字内容
4. 只返回 LaTeX/文字，不要解释

示例输出：
$E = mc^2$
或
$$\\int_{a}^{b} f(x) dx$$"""
        
        return self.chat_with_image(image, prompt, temperature=0.1, **kwargs)
    
    def analyze_diagram(self, image: Union[str, np.ndarray, Image.Image], 
                       **kwargs) -> Dict[str, Any]:
        """
        分析图表结构
        
        Args:
            image: 图表图片
            **kwargs: 额外参数
        
        Returns:
            Dict: 图表分析结果
        """
        prompt = """请分析这张图表/流程图，识别其中的元素和关系。

请返回 JSON 格式：
{
  "elements": [
    {"type": "shape|arrow|text|icon", "description": "描述", "estimated_position": {"x": 0, "y": 0}}
  ],
  "relationships": [
    {"from": "元素1", "to": "元素2", "type": "连接关系"}
  ],
  "summary": "图表整体描述"
}

只返回 JSON，不要其他内容。"""
        
        response = self.chat_with_image(image, prompt, temperature=0.3, **kwargs)
        
        try:
            import json
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
        
        return {"raw_response": response}


class LLMClientFactory:
    """LLM 客户端工厂"""
    
    _clients: Dict[str, BaseLLMClient] = {}
    
    @classmethod
    def get_client(cls, provider: Optional[str] = None) -> BaseLLMClient:
        """获取 LLM 客户端实例"""
        provider = provider or os.getenv("LLM_PROVIDER", "kimi")
        
        if provider not in cls._clients:
            if provider == "kimi":
                cls._clients[provider] = KimiClient()
            else:
                raise ValueError(f"Unknown or unsupported LLM provider: {provider}")
        
        return cls._clients[provider]
    
    @classmethod
    def reset(cls):
        """重置所有客户端"""
        cls._clients = {}


# 便捷函数
def get_kimi_client() -> KimiClient:
    """获取 Kimi 客户端实例"""
    client = LLMClientFactory.get_client("kimi")
    if not isinstance(client, KimiClient):
        raise RuntimeError("Failed to get Kimi client")
    return client


def chat(messages: List[Dict[str, Any]], **kwargs) -> str:
    """使用默认 provider 发送聊天请求"""
    client = LLMClientFactory.get_client()
    return client.chat(messages, **kwargs)


def chat_with_image(image: Union[str, np.ndarray, Image.Image], 
                   prompt: str, **kwargs) -> str:
    """使用默认 provider 发送带图片的聊天请求"""
    client = LLMClientFactory.get_client()
    return client.chat_with_image(image, prompt, **kwargs)


def vision_ocr(image: Union[str, np.ndarray, Image.Image], **kwargs) -> List[Dict[str, Any]]:
    """使用视觉模型进行 OCR"""
    client = get_kimi_client()
    return client.vision_ocr(image, **kwargs)


def recognize_formula(image: Union[str, np.ndarray, Image.Image], **kwargs) -> str:
    """识别数学公式"""
    client = get_kimi_client()
    return client.recognize_formula(image, **kwargs)
