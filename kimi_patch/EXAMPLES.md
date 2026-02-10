# 代码替换示例

## 示例 1: 替换 OpenAI 调用

### 原代码
```python
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "你是一个助手。"},
        {"role": "user", "content": "你好"}
    ],
    max_tokens=100,
    temperature=0.7
)

print(response.choices[0].message.content)
```

### 新代码（使用 Kimi）
```python
import sys
sys.path.insert(0, "kimi_patch")

from patches.openai_patch import OpenAI

client = OpenAI()  # 自动使用 ANTHROPIC_API_KEY

response = client.chat.create(
    model="gpt-4",  # 自动映射到 kimi-k2-5
    messages=[
        {"role": "system", "content": "你是一个助手。"},
        {"role": "user", "content": "你好"}
    ],
    max_tokens=100,
    temperature=0.7
)

print(response.choices[0].message.content)
```

### 新代码（直接使用 KimiClient）
```python
import sys
sys.path.insert(0, "kimi_patch")

from kimi_client import KimiClient

client = KimiClient()

response = client.chat(
    messages=[{"role": "user", "content": "你好"}],
    system="你是一个助手。",
    max_tokens=100,
    temperature=0.7
)

print(response)
```

---

## 示例 2: 替换 Azure OpenAI 调用

### 原代码
```python
import os
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "分析这张图片"}],
    max_tokens=500
)
```

### 新代码（使用 Kimi）
```python
import sys
sys.path.insert(0, "kimi_patch")

from patches.azure_patch import AzureOpenAI

client = AzureOpenAI()  # 自动使用 ANTHROPIC_API_KEY

response = client.chat.create(
    model="gpt-4",  # 自动映射到 kimi-k2-5
    messages=[{"role": "user", "content": "分析这张图片"}],
    max_tokens=500
)

print(response.choices[0].message.content)
```

---

## 示例 3: 替换 Mistral 调用

### 原代码
```python
import os
from mistralai.client import MistralClient

client = MistralClient(api_key=os.getenv("MISTRAL_API_KEY"))

response = client.chat(
    model="mistral-large-latest",
    messages=[{"role": "user", "content": "你好"}]
)

print(response.choices[0].message.content)
```

### 新代码（使用 Kimi）
```python
import sys
sys.path.insert(0, "kimi_patch")

from patches.mistral_patch import MistralClient

client = MistralClient()  # 自动使用 ANTHROPIC_API_KEY

response = client.chat(
    model="mistral-large-latest",  # 自动映射到 kimi-k2-5
    messages=[{"role": "user", "content": "你好"}]
)

print(response.choices[0].message.content)
```

---

## 示例 4: 带图片的调用（视觉输入）

### 原代码（OpenAI GPT-4V）
```python
import base64
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 读取图片
with open("image.png", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode()

response = client.chat.completions.create(
    model="gpt-4-vision-preview",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "描述这张图片"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_base64}"
                    }
                }
            ]
        }
    ]
)
```

### 新代码（Kimi）
```python
import sys
sys.path.insert(0, "kimi_patch")

from kimi_client import KimiClient

client = KimiClient()

response = client.chat_with_image(
    messages=[{"role": "user", "content": "描述这张图片"}],
    image_path="image.png"
)

print(response)
```

---

## 示例 5: 流式输出

### 原代码（OpenAI）
```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "写一个故事"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```

### 新代码（Kimi）
```python
import sys
sys.path.insert(0, "kimi_patch")

from kimi_client import KimiClient

client = KimiClient()

for chunk in client.chat_stream(
    messages=[{"role": "user", "content": "写一个故事"}]
):
    print(chunk, end="")
```

### 新代码（使用 OpenAI 兼容补丁）
```python
import sys
sys.path.insert(0, "kimi_patch")

from patches.openai_patch import OpenAI

client = OpenAI()

stream = client.chat.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "写一个故事"}],
    stream=True
)

for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")
```

---

## 示例 6: 全局补丁（无需修改现有代码）

### 在程序入口处应用补丁
```python
# main.py 或 app.py 开头

import sys
sys.path.insert(0, "kimi_patch")

# 应用补丁 - 之后的 OpenAI 导入都会使用 Kimi
from patches.openai_patch import patch_openai
from patches.azure_patch import patch_azure_openai
from patches.mistral_patch import patch_mistral

patch_openai()
patch_azure_openai()
patch_mistral()

# 之后的代码无需修改
import openai
client = openai.OpenAI()  # 实际使用 Kimi

from openai import AzureOpenAI
azure_client = AzureOpenAI(...)  # 实际使用 Kimi

from mistralai.client import MistralClient
mistral_client = MistralClient(...)  # 实际使用 Kimi
```
