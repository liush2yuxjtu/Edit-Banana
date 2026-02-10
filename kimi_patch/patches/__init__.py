"""
API Patches Package

提供 OpenAI、Azure OpenAI 和 Mistral API 的 Kimi 兼容补丁
"""

from .openai_patch import OpenAI, patch_openai
from .azure_patch import AzureOpenAI, patch_azure_openai
from .mistral_patch import MistralClient, MistralAI, patch_mistral

__all__ = [
    "OpenAI",
    "AzureOpenAI", 
    "MistralClient",
    "MistralAI",
    "patch_openai",
    "patch_azure_openai",
    "patch_mistral",
]
