"""
OpenAI API Patch - 替换 OpenAI 调用为 Kimi API

原始文件参考: 模拟替换 OpenAI 调用

使用方法:
    # 替换原始导入
    # from openai import OpenAI
    from patches.openai_patch import OpenAI
"""

import os
import sys
from typing import List, Dict, Any, Optional

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kimi_client import KimiClient, OpenAICompatibleClient


class OpenAI:
    """
    模拟 OpenAI 客户端，底层使用 Kimi API
    
    用法与原 OpenAI 客户端兼容
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs):
        """
        初始化客户端
        
        Args:
            api_key: 被忽略，使用 ANTHROPIC_API_KEY 环境变量
            base_url: 被忽略，使用 Kimi 的 base_url
            **kwargs: 其他参数被忽略
        """
        # 使用 Kimi 客户端
        self.kimi_client = KimiClient()
        self.chat = ChatCompletions(self.kimi_client)
        
    def __getattr__(self, name):
        """处理其他属性访问"""
        raise NotImplementedError(f"OpenAI 的 {name} 功能未在 Kimi 补丁中实现")


class ChatCompletions:
    """聊天补全 API 兼容层"""
    
    def __init__(self, kimi_client: KimiClient):
        self.kimi_client = kimi_client
    
    def create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        **kwargs
    ) -> 'ChatCompletionResponse':
        """
        创建聊天补全
        
        Args:
            model: 模型名称（如 gpt-4 会被映射到 kimi-k2-5）
            messages: 消息列表
            max_tokens: 最大 token 数
            temperature: 温度
            stream: 是否流式输出
            **kwargs: 其他参数
            
        Returns:
            ChatCompletionResponse: 响应对象
        """
        # 模型映射
        model_mapping = {
            "gpt-4": "kimi-k2-5",
            "gpt-4-vision-preview": "kimi-k2-5",
            "gpt-4o": "kimi-k2-5",
            "gpt-3.5-turbo": "kimi-k2-5",
        }
        kimi_model = model_mapping.get(model, "kimi-k2-5")
        
        # 处理系统消息
        system = None
        filtered_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system = msg.get("content")
            else:
                filtered_messages.append(msg)
        
        if stream:
            # 返回流式响应
            return StreamingChatCompletionResponse(
                self.kimi_client, filtered_messages, system, kimi_model, 
                max_tokens, temperature
            )
        else:
            # 普通响应
            content = self.kimi_client.chat(
                messages=filtered_messages,
                system=system,
                model=kimi_model,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return ChatCompletionResponse(content, model)


class ChatCompletionResponse:
    """OpenAI 格式的聊天补全响应"""
    
    def __init__(self, content: str, model: str):
        import time
        self.id = f"kimi-chatcmpl-{int(time.time())}"
        self.object = "chat.completion"
        self.created = int(time.time())
        self.model = model
        self.choices = [
            Choice(content)
        ]
        self.usage = Usage()
    
    def __repr__(self):
        return f"ChatCompletionResponse(model={self.model}, content={self.choices[0].message.content[:50]}...)"


class Choice:
    """响应选项"""
    
    def __init__(self, content: str):
        self.index = 0
        self.message = Message(content)
        self.finish_reason = "stop"


class Message:
    """消息对象"""
    
    def __init__(self, content: str):
        self.role = "assistant"
        self.content = content


class Usage:
    """用量统计"""
    
    def __init__(self):
        # Kimi API 不返回精确的 token 计数
        self.prompt_tokens = -1
        self.completion_tokens = -1
        self.total_tokens = -1


class StreamingChatCompletionResponse:
    """流式响应"""
    
    def __init__(self, client, messages, system, model, max_tokens, temperature):
        self.client = client
        self.messages = messages
        self.system = system
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
    
    def __iter__(self):
        """迭代生成流式响应"""
        full_content = ""
        for chunk in self.client.chat_stream(
            messages=self.messages,
            system=self.system,
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        ):
            full_content += chunk
            yield StreamingChunk(chunk, self.model)
        
        # 最终 chunk
        yield StreamingChunk("", self.model, finish_reason="stop")


class StreamingChunk:
    """流式响应块"""
    
    def __init__(self, content: str, model: str, finish_reason: Optional[str] = None):
        import time
        self.id = f"kimi-chatcmpl-{int(time.time())}"
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
        self.content = content
        self.role = "assistant" if content else None


# 便捷函数
def patch_openai():
    """
    全局替换 openai 模块
    
    用法:
        from patches.openai_patch import patch_openai
        patch_openai()
        
        # 现在 import openai 会使用 Kimi 后端
        import openai
        client = openai.OpenAI()
    """
    import sys
    sys.modules['openai'] = sys.modules[__name__]
    print("✅ 已应用 OpenAI -> Kimi 补丁")
