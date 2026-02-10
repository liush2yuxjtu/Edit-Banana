"""
Kimi Patch Package

将 LLM API 调用替换为 Kimi API 的补丁包
"""

from .kimi_client import KimiClient, OpenAICompatibleClient, get_client

__version__ = "1.0.0"
__all__ = [
    "KimiClient",
    "OpenAICompatibleClient", 
    "get_client",
]
