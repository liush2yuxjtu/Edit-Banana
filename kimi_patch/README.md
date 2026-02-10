# Edit-Banana Kimi API Monkey Patch

## 概述

本项目提供将 Edit-Banana 中的 LLM API 调用（OpenAI、Azure OpenAI、Mistral）替换为 **Kimi API** 的补丁方案。

Kimi API 支持 Anthropic API 格式，可以直接通过 `anthropic` Python 库调用。

## 配置信息

```bash
export ANTHROPIC_BASE_URL=https://api.kimi.com/coding/
export ANTHROPIC_API_KEY=sk-kimi-SckItPdArEsXNGKFoCYHMd8uG1FjpDnG8m1mEi1vQ6VMzhMhtVgFVqKilMthoVXN
```

## 文件结构

```
kimi_patch/
├── README.md              # 本文件
├── kimi_client.py         # 统一的 Kimi API 客户端
├── patches/               # 原始文件的修改版本
│   ├── openai_patch.py    # 替换 OpenAI 调用
│   ├── azure_patch.py     # 替换 Azure OpenAI 调用
│   └── mistral_patch.py   # 替换 Mistral 调用
└── test_kimi.py           # 测试脚本
```

## 使用方法

### 1. 安装依赖

```bash
pip install anthropic python-dotenv
```

### 2. 使用 Kimi 客户端

```python
from kimi_client import KimiClient

client = KimiClient()

# 文本补全
response = client.complete("你好，世界！")

# 多轮对话
messages = [
    {"role": "user", "content": "你好"}
]
response = client.chat(messages)

# 视觉输入
response = client.chat_with_image(
    messages=[{"role": "user", "content": "描述这张图片"}],
    image_path="path/to/image.png"
)
```

### 3. 应用补丁

将 `patches/` 目录下的文件复制到对应位置，或参考补丁内容手动修改原始文件。

## 需要修改的文件清单

### 当前项目中 LLM API 使用情况

| 文件 | 当前状态 | 建议操作 |
|------|----------|----------|
| `config/config.yaml` | 配置了 Azure/Mistral/OpenAI | 添加 Kimi 配置选项 |
| `.env` | 配置了 Azure/Mistral/OpenAI | 添加 Kimi 配置 |
| `streamlit_app.py` | 有 API Key 输入界面 | 添加 Kimi 选项 |
| `prompts/*.py` | 有 LLM 提示词模板 | 兼容 Kimi 格式 |

### 注意

目前 Edit-Banana 项目中**尚未实际调用 LLM API**，仅在配置和 UI 层面有准备。本补丁为未来 LLM 集成提供 Kimi 方案。

## 测试

运行测试脚本：

```bash
python test_kimi.py
```

## 支持的模型

- `kimi-k2-5` - Kimi K2.5 系列模型（推荐）

## 特性支持

| 功能 | 支持状态 |
|------|----------|
| 文本补全 | ✅ |
| 多轮对话 | ✅ |
| 流式输出 | ✅ |
| 视觉输入 | ✅ |
| 函数调用 | ✅ |

## 与原 API 的差异

1. **模型名称**: Kimi 使用自己的模型命名（如 `kimi-k2-5`）
2. **API 格式**: 使用 Anthropic 格式而非 OpenAI 格式
3. **Base URL**: `https://api.kimi.com/coding/`
4. **认证**: 使用 `x-api-key` 头而非 `Authorization: Bearer`

## 故障排除

### 问题：连接超时

检查网络连接，确保可以访问 `https://api.kimi.com/coding/`

### 问题：认证失败

确认 `ANTHROPIC_API_KEY` 环境变量已正确设置

### 问题：模型不存在

使用 `kimi_client.list_models()` 查看可用模型

## 参考

- [Kimi API 文档](https://platform.moonshot.cn/docs)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)
