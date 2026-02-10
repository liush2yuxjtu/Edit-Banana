# Edit-Banana LLM 调用替换清单

## 当前项目中需要修改的文件

### 1. 配置文件

#### `config/config.yaml`
**当前内容:**
```yaml
api:
  azure:
    openai_endpoint: ""
    openai_key: ""
    openai_api_version: "2024-02-01"
    deployment_name: "gpt-4"
  mistral:
    api_key: ""
    model: "mistral-large-latest"
  openai:
    api_key: ""
    model: "gpt-4"
```

**建议修改为:**
```yaml
api:
  # Kimi API (使用 Anthropic 格式)
  kimi:
    base_url: "https://api.kimi.com/coding/"
    api_key: ""  # 从 ANTHROPIC_API_KEY 环境变量读取
    model: "kimi-k2-5"
    max_tokens: 4096
    temperature: 0.7
  
  # 保留原有配置（可选，用于兼容）
  azure:
    openai_endpoint: ""
    openai_key: ""
    openai_api_version: "2024-02-01"
    deployment_name: "gpt-4"
  mistral:
    api_key: ""
    model: "mistral-large-latest"
  openai:
    api_key: ""
    model: "gpt-4"
```

#### `.env`
**当前内容:**
```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-azure-openai-key-here
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
MISTRAL_API_KEY=your-mistral-api-key-here
MISTRAL_MODEL=mistral-large-latest
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4
```

**建议添加:**
```bash
# Kimi API 配置（使用 Anthropic 格式）
ANTHROPIC_BASE_URL=https://api.kimi.com/coding/
ANTHROPIC_API_KEY=sk-kimi-SckItPdArEsXNGKFoCYHMd8uG1FjpDnG8m1mEi1vQ6VMzhMhtVgFVqKilMthoVXN
KIMI_MODEL=kimi-k2-5
```

### 2. UI 文件

#### `streamlit_app.py`
**需要修改的位置:**
- 添加 Kimi API Key 输入界面
- 在侧边栏添加 Kimi 配置选项

**参考代码:**
```python
# 在 render_sidebar() 函数中添加

st.markdown("### Kimi API 配置")

kimi_key = st.text_input(
    "🟠 Kimi API Key",
    value=os.getenv("ANTHROPIC_API_KEY", ""),
    type="password",
    help="Kimi API Key（使用 Anthropic 格式）",
    key="kimi_key"
)

if st.button("💾 保存配置"):
    env_vars = load_env_file()
    env_vars["ANTHROPIC_API_KEY"] = kimi_key
    if save_env_file(env_vars):
        st.success("✅ 配置已保存到 .env 文件")
```

### 3. 核心模块

#### 新建 `modules/llm_client.py`
**用途:** 统一的 LLM 客户端，支持多种后端

**参考实现:**
```python
"""
LLM 客户端模块
支持 OpenAI、Azure、Mistral 和 Kimi API
"""

import os
from typing import Optional, List, Dict, Any
from enum import Enum

class LLMProvider(Enum):
    OPENAI = "openai"
    AZURE = "azure"
    MISTRAL = "mistral"
    KIMI = "kimi"


class LLMClient:
    """统一的 LLM 客户端"""
    
    def __init__(self, provider: LLMProvider = None):
        self.provider = provider or self._detect_provider()
        self._client = None
        
    def _detect_provider(self) -> LLMProvider:
        """自动检测可用的 provider"""
        if os.getenv("ANTHROPIC_API_KEY"):
            return LLMProvider.KIMI
        elif os.getenv("OPENAI_API_KEY"):
            return LLMProvider.OPENAI
        elif os.getenv("AZURE_OPENAI_KEY"):
            return LLMProvider.AZURE
        elif os.getenv("MISTRAL_API_KEY"):
            return LLMProvider.MISTRAL
        else:
            raise ValueError("未找到任何 LLM API Key")
    
    def _get_client(self):
        """获取底层客户端"""
        if self._client is None:
            if self.provider == LLMProvider.KIMI:
                from ..kimi_patch.kimi_client import KimiClient
                self._client = KimiClient()
            elif self.provider == LLMProvider.OPENAI:
                import openai
                self._client = openai.OpenAI()
            # ... 其他 provider
        return self._client
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """多轮对话"""
        client = self._get_client()
        return client.chat(messages, **kwargs)
    
    def complete(self, prompt: str, **kwargs) -> str:
        """文本补全"""
        client = self._get_client()
        return client.complete(prompt, **kwargs)
```

### 4. 提示词模块

#### `prompts/image.py` 及其他提示词文件
**当前状态:** 只有提示词模板，尚未实际调用 LLM

**未来使用时:**
```python
from modules.llm_client import LLMClient

def analyze_image(image_path: str) -> dict:
    client = LLMClient()
    
    # 使用 Kimi 客户端进行图片分析
    from kimi_patch.kimi_client import KimiClient
    kimi = KimiClient()
    
    response = kimi.chat_with_image(
        messages=[{"role": "user", "content": IMAGE_DETECTION_PROMPT}],
        image_path=image_path
    )
    
    return parse_response(response)
```

## 模型映射表

| 原模型 | Kimi 替代 | 说明 |
|--------|-----------|------|
| gpt-4 | kimi-k2-5 | 通用对话 |
| gpt-4-vision-preview | kimi-k2-5 | 视觉输入 |
| gpt-4o | kimi-k2-5 | 通用对话 |
| gpt-3.5-turbo | kimi-k2-5 | 通用对话 |
| mistral-large-latest | kimi-k2-5 | 通用对话 |
| mistral-medium-latest | kimi-k2-5 | 通用对话 |
| mistral-small-latest | kimi-k2-5 | 通用对话 |

## 功能对照表

| 功能 | OpenAI | Azure OpenAI | Mistral | Kimi | 状态 |
|------|--------|--------------|---------|------|------|
| 文本补全 | ✅ | ✅ | ✅ | ✅ | 支持 |
| 多轮对话 | ✅ | ✅ | ✅ | ✅ | 支持 |
| 流式输出 | ✅ | ✅ | ✅ | ✅ | 支持 |
| 视觉输入 | ✅ | ✅ | ❌ | ✅ | 支持 |
| 函数调用 | ✅ | ✅ | ✅ | ✅ | 支持 |
| JSON 模式 | ✅ | ✅ | ✅ | ✅ | 支持 |

## 替换步骤

### 快速替换（使用补丁）

1. **复制补丁文件**
   ```bash
   cp kimi_patch/patches/openai_patch.py modules/
   cp kimi_patch/patches/azure_patch.py modules/
   cp kimi_patch/patches/mistral_patch.py modules/
   ```

2. **修改导入语句**
   ```python
   # 原代码
   from openai import OpenAI
   
   # 修改为
   from modules.openai_patch import OpenAI
   ```

3. **设置环境变量**
   ```bash
   export ANTHROPIC_API_KEY=sk-kimi-...
   ```

### 完整替换（推荐）

1. 创建统一的 LLM 客户端模块
2. 修改配置文件，添加 Kimi 选项
3. 修改 UI，支持 Kimi API Key 输入
4. 在需要 LLM 功能的地方使用新客户端

## 保留的 API

以下 API 不需要替换，保持原样：

- **Azure Document Intelligence** - OCR 专用，与 LLM 无关
- **SAM3 模型** - 本地分割模型
- **超分模型** - 本地图像处理
