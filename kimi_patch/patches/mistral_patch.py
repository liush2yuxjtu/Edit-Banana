"""
Mistral AI API Patch - 替换 Mistral 调用为 Kimi API

原始文件参考: config/config.yaml 中的 mistral 配置

使用方法:
    # 替换原始 Mistral 调用
    # from mistralai.client import MistralClient
    from patches.mistral_patch import MistralClient
"""

import os
import sys
from typing import List, Dict, Any, Optional

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kimi_client import KimiClient


class MistralClient:
    """
    模拟 Mistral 客户端，底层使用 Kimi API
    
    用法与原 Mistral 客户端兼容
    """
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        初始化客户端
        
        注意: api_key 被忽略，实际使用 ANTHROPIC_API_KEY 环境变量
        
        Args:
            api_key: 被忽略
            **kwargs: 其他参数被忽略
        """
        # 使用 Kimi 客户端
        self.kimi_client = KimiClient()
        self._original_api_key = api_key  # 记录用于调试
    
    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> 'ChatCompletionResponse':
        """
        创建聊天补全
        
        Args:
            model: Mistral 模型名称（会被映射到 kimi-k2-5）
            messages: 消息列表
            **kwargs: 其他参数（temperature, max_tokens 等）
            
        Returns:
            ChatCompletionResponse: 响应对象
        """
        # Mistral 模型映射到 Kimi 模型
        model_mapping = {
            "mistral-large-latest": "kimi-k2-5",
            "mistral-medium-latest": "kimi-k2-5",
            "mistral-small-latest": "kimi-k2-5",
            "mistral-tiny": "kimi-k2-5",
        }
        kimi_model = model_mapping.get(model, "kimi-k2-5")
        
        # 提取参数
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 4096)
        
        # 处理系统消息
        system = None
        filtered_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system = msg.get("content")
            else:
                filtered_messages.append(msg)
        
        # 调用 Kimi
        content = self.kimi_client.chat(
            messages=filtered_messages,
            system=system,
            model=kimi_model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return ChatCompletionResponse(content, model)
    
    def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ):
        """
        创建流式聊天补全
        
        Args:
            model: Mistral 模型名称
            messages: 消息列表
            **kwargs: 其他参数
            
        Yields:
            ChatCompletionStreamResponse: 流式响应
        """
        # Mistral 模型映射到 Kimi 模型
        model_mapping = {
            "mistral-large-latest": "kimi-k2-5",
            "mistral-medium-latest": "kimi-k2-5",
            "mistral-small-latest": "kimi-k2-5",
            "mistral-tiny": "kimi-k2-5",
        }
        kimi_model = model_mapping.get(model, "kimi-k2-5")
        
        # 提取参数
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 4096)
        
        # 处理系统消息
        system = None
        filtered_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system = msg.get("content")
            else:
                filtered_messages.append(msg)
        
        # 生成流式响应
        full_content = ""
        chunk_id = 0
        
        for chunk in self.kimi_client.chat_stream(
            messages=filtered_messages,
            system=system,
            model=kimi_model,
            max_tokens=max_tokens,
            temperature=temperature
        ):
            full_content += chunk
            yield ChatCompletionStreamResponse(chunk, model, chunk_id)
            chunk_id += 1
        
        # 最终响应
        yield ChatCompletionStreamResponse("", model, chunk_id, finish_reason="stop")


class ChatCompletionResponse:
    """Mistral 格式的聊天补全响应"""
    
    def __init__(self, content: str, model: str):
        import time
        self.id = f"kimi-mistral-{int(time.time())}"
        self.object = "chat.completion"
        self.created = int(time.time())
        self.model = model
        self.choices = [
            Choice(content)
        ]
        self.usage = Usage()
    
    def __repr__(self):
        return f"MistralChatCompletionResponse(model={self.model}, content={self.choices[0].message.content[:50]}...)"


class Choice:
    """响应选项"""
    
    def __init__(self, content: str, finish_reason: str = "stop"):
        self.index = 0
        self.message = Message(content)
        self.finish_reason = finish_reason


class Message:
    """消息对象"""
    
    def __init__(self, content: str):
        self.role = "assistant"
        self.content = content


class Usage:
    """用量统计"""
    
    def __init__(self):
        self.prompt_tokens = -1
        self.completion_tokens = -1
        self.total_tokens = -1


class ChatCompletionStreamResponse:
    """流式响应"""
    
    def __init__(self, content: str, model: str, chunk_id: int, finish_reason: Optional[str] = None):
        import time
        self.id = f"kimi-mistral-chunk-{chunk_id}"
        self.object = "chat.completion.chunk"
        self.created = int(time.time())
        self.model = model
        self.choices = [
            StreamingChoice(content, finish_reason)
        ]


class StreamingChoice:
    """流式选项"""
    
    def __init__(self, content: str, finish_reason: Optional[str] = None):
        self.index = 0
        self.delta = Delta(content)
        self.finish_reason = finish_reason


class Delta:
    """增量内容"""
    
    def __init__(self, content: str):
        self.role = "assistant"
        self.content = content


# 便捷函数
def patch_mistral():
    """
    全局替换 mistralai 模块
    
    用法:
        from patches.mistral_patch import patch_mistral
        patch_mistral()
        
        # 现在 from mistralai.client import MistralClient 会使用 Kimi 后端
        from mistralai.client import MistralClient
        client = MistralClient(api_key="...")
    """
    import sys
    
    # 创建模拟的 mistralai 模块结构
    class MockMistralModule:
        client = type('client', (), {'MistralClient': MistralClient})()
    
    sys.modules['mistralai'] = MockMistralModule
    sys.modules['mistralai.client'] = MockMistralModule.client
    
    print("✅ 已应用 Mistral -> Kimi 补丁")


# 兼容性别名
class MistralAI:
    """MistralAI 别名"""
    def __init__(self, api_key: Optional[str] = None):
        self.client = MistralClient(api_key=api_key)
