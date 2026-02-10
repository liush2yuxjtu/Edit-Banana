# Edit-Banana API 替换分析报告

## 📊 项目现状分析

### 当前 API 使用情况

| 模块 | 当前实现 | 实际使用 API | 说明 |
|------|----------|--------------|------|
| 图像分割 | SAM3 本地模型 | ❌ 无 API 调用 | 使用本地 PyTorch 模型 |
| 背景移除 | RMBG ONNX 本地 | ❌ 无 API 调用 | 使用本地 ONNX Runtime |
| OCR 文字识别 | **占位符** | ❌ 未实现 | 需要实现方案 |
| 文本渲染 | PIL 本地 | ❌ 无 API 调用 | 纯本地图像处理 |
| XML 生成 | 本地模板 | ❌ 无 API 调用 | 纯本地代码生成 |
| 形状识别 | 本地算法 | ❌ 无 API 调用 | 传统 CV 算法 |

### 配置文件 vs 实际代码

```yaml
# config.yaml 中配置了但代码未使用的 API：
- Azure OpenAI (gpt-4)
- Mistral AI (mistral-large-latest)
- OpenAI Direct (gpt-4)
```

**结论**：当前项目**并未实际调用任何 LLM API**，仅在配置层面有预留。

---

## 🎯 API 替换建议

### 1. 可替换为 Kimi API 的功能

| 功能 | 优先级 | 替换难度 | 说明 |
|------|--------|----------|------|
| **OCR 文字识别** | ⭐⭐⭐ 高 | 低 | Kimi 支持图像理解，可做 OCR |
| **图表描述生成** | ⭐⭐ 中 | 低 | 自动生成图表文字描述 |
| **智能提示词优化** | ⭐⭐ 中 | 低 | 优化 SAM3 分割提示词 |
| **错误诊断** | ⭐ 低 | 低 | 处理失败时的智能诊断 |
| **代码补全/生成** | ⭐ 低 | 低 | 辅助生成处理逻辑 |

### 2. 不能替换为 Kimi API 的功能（需要替代方案）

| 功能 | 原因 | 替代方案 |
|------|------|----------|
| **Azure OCR** | Kimi 是 LLM，不是 OCR 专用服务 | 方案A: PaddleOCR (本地开源) |
| | | 方案B: EasyOCR (本地开源) |
| | | 方案C: Tesseract (本地开源) |
| **GPT-4V 结构化输出** | 需要特定格式输出 | 使用 Kimi + JSON 模式 |

---

## 💡 三种实现方案

### 方案一：全量替换方案（推荐）

**架构图：**
```
┌─────────────────────────────────────────────────────────────┐
│                        Edit-Banana                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐  │
│  │ 图像分割  │  │ 背景移除  │  │      文字处理模块        │  │
│  │ SAM3本地  │  │ RMBG本地  │  │  ┌──────────────────┐   │  │
│  │ 无需改动  │  │ 无需改动  │  │  │ OCR: PaddleOCR   │   │  │
│  └──────────┘  └──────────┘  │  │ (本地开源替代)     │   │  │
│                              │  ├──────────────────┤   │  │
│                              │  │ LLM: Kimi API    │   │  │
│                              │  │ (文本理解/生成)   │   │  │
│                              │  └──────────────────┘   │  │
│                              └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**优点：**
- OCR 免费（PaddleOCR 开源）
- LLM 功能由 Kimi 提供
- 成本可控

**缺点：**
- 需要部署 PaddleOCR 环境

**预估成本：**
- OCR: ¥0 (本地)
- Kimi API: 按使用量计费，预计月均 ¥50-200

---

### 方案二：混合架构方案

**架构图：**
```
┌────────────────────────────────────────────────────────────────┐
│                         Edit-Banana                            │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│   简单 OCR（Kimi）         复杂 OCR（本地）      无文字场景      │
│   ┌─────────────┐         ┌─────────────┐                      │
│   │ Kimi Vision │         │ PaddleOCR   │      ┌────────────┐  │
│   │ 直接识别    │◄───────►│ 精确识别    │      │  跳过 OCR  │  │
│   └─────────────┘         └─────────────┘      └────────────┘  │
│         │                                                        │
│         ▼                                                        │
│   ┌─────────────┐                                               │
│   │ Kimi LLM    │                                               │
│   │ 文本理解    │                                               │
│   └─────────────┘                                               │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**智能路由逻辑：**
```python
def select_ocr_engine(image, scene_type):
    """
    根据场景选择 OCR 引擎
    """
    if scene_type == "simple_text":
        return "kimi_vision"  # 简单文字用 Kimi
    elif scene_type == "table":
        return "kimi_vision"  # 表格用 Kimi
    elif scene_type == "formula":
        return "paddleocr"    # 公式用 PaddleOCR
    else:
        return "kimi_vision"  # 默认用 Kimi
```

**优点：**
- 灵活性最高
- 根据场景优化
- 成本可控

**缺点：**
- 架构稍复杂
- 需要场景检测逻辑

---

### 方案三：简化版方案（最小改动）

**仅添加 Kimi 作为可选 LLM：**

```yaml
# config.yaml 新增
api:
  kimi:
    api_key: ""          # KIMI_API_KEY
    base_url: "https://api.kimi.com/coding/"
    model: "kimi-k2-5"
```

**使用场景：**
- 仅在需要智能功能时调用 Kimi
- OCR 暂不实现或简单实现
- 保持现有架构不变

**优点：**
- 改动最小
- 快速上线
- 风险最低

**缺点：**
- OCR 功能弱
- 依赖外部服务较多

---

## 📝 代码修改示例

### 1. 新增 Kimi OCR 模块

**文件：** `modules/text/kimi_ocr.py`

```python
"""
Kimi OCR Module
使用 Kimi API 进行图像文字识别
"""

import os
import base64
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class KimiOCR:
    """
    Kimi OCR 识别器
    使用 Kimi Vision 能力识别图像中的文字
    """
    
    DEFAULT_BASE_URL = "https://api.kimi.com/coding/"
    DEFAULT_MODEL = "kimi-k2-5"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic 库未安装，请运行: pip install anthropic")
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API Key 未设置")
        
        self.base_url = base_url or os.getenv(
            "ANTHROPIC_BASE_URL", 
            self.DEFAULT_BASE_URL
        )
        self.model = model or self.DEFAULT_MODEL
        
        self.client = anthropic.Anthropic(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=60.0
        )
    
    def recognize(
        self,
        image_path: str,
        prompt: str = "识别图片中的所有文字，按行输出。",
        output_format: str = "json"
    ) -> List[Dict[str, Any]]:
        """
        识别图像中的文字
        
        Args:
            image_path: 图像路径
            prompt: 识别提示词
            output_format: 输出格式 (json/text)
            
        Returns:
            List[Dict]: 识别结果列表，包含 text, bbox 等信息
        """
        # 读取并编码图片
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # 检测 MIME 类型
        mime_type = self._detect_mime_type(image_path)
        
        # 构建提示词
        if output_format == "json":
            system_prompt = """你是一个 OCR 助手。请识别图片中的所有文字。
请按 JSON 格式返回结果：
[
  {"text": "文字内容", "bbox": [x1, y1, x2, y2], "confidence": 0.95}
]
如果没有文字，返回空数组 []。"""
        else:
            system_prompt = "识别图片中的所有文字，按行输出。"
        
        # 调用 Kimi API
        messages = [
            {
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
        ]
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=messages
        )
        
        # 解析结果
        text_content = ""
        for block in response.content:
            if hasattr(block, 'text'):
                text_content += block.text
        
        # 解析 JSON
        if output_format == "json":
            return self._parse_json_response(text_content)
        else:
            return [{"text": text_content, "bbox": None, "confidence": 1.0}]
    
    def _detect_mime_type(self, image_path: str) -> str:
        """检测图片 MIME 类型"""
        ext = Path(image_path).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
        }
        return mime_types.get(ext, 'image/png')
    
    def _parse_json_response(self, text: str) -> List[Dict[str, Any]]:
        """解析 JSON 响应"""
        import json
        import re
        
        # 尝试提取 JSON
        json_match = re.search(r'\[.*?\]', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # 回退到文本
        return [{"text": text.strip(), "bbox": None, "confidence": 1.0}]


# 兼容 TextRestorer 接口
class KimiTextRestorer(KimiOCR):
    """
    兼容 TextRestorer 接口的 Kimi OCR 实现
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        super().__init__(
            api_key=config.get("api_key"),
            base_url=config.get("base_url"),
            model=config.get("model")
        )
    
    def detect_text(self, image) -> list:
        """
        检测图像中的文字 (兼容接口)
        
        Args:
            image: 图像路径或 numpy 数组
            
        Returns:
            list: 检测到的文字列表
        """
        import numpy as np
        from PIL import Image
        import tempfile
        
        # 如果是 numpy 数组，保存为临时文件
        if isinstance(image, np.ndarray):
            pil_img = Image.fromarray(image)
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                pil_img.save(f.name)
                image_path = f.name
                temp_file = True
        else:
            image_path = image
            temp_file = False
        
        try:
            results = self.recognize(image_path)
            return results
        finally:
            if temp_file:
                os.unlink(image_path)
```

### 2. 修改 config.yaml

```yaml
# Edit-Banana Backend Configuration
# 复制此文件为 config.yaml 并根据需要修改

app:
  name: "Edit-Banana"
  version: "1.0.0"
  debug: false
  host: "0.0.0.0"
  port: 8000

# 模型配置
models:
  # SAM 3 分割模型
  sam3:
    checkpoint: "models/sam3_checkpoint.pth"
    device: "mps"  # Mac MPS 加速，可选: cuda, cpu, mps
    
  # Stable Diffusion / Flux 图像生成
  diffusion:
    model_id: "black-forest-labs/FLUX.1-dev"
    device: "mps"
    dtype: "float16"
    
  # 可选: DINOv2 特征提取
  dinov2:
    model_name: "dinov2_vitb14"
    device: "mps"

# OCR 配置 (新增)
ocr:
  # OCR 引擎选择: "kimi" | "paddle" | "none"
  engine: "kimi"
  
  # Kimi OCR 配置
  kimi:
    api_key: ""           # KIMI_API_KEY 或 ANTHROPIC_API_KEY
    base_url: "https://api.kimi.com/coding/"
    model: "kimi-k2-5"
    
  # PaddleOCR 配置 (备用)
  paddle:
    lang: "ch"            # 语言: ch(中文), en(英文), ch_sim(简体中文)
    use_gpu: false        # 是否使用 GPU

# API Keys (优先从环境变量读取)
api:
  # Kimi API 配置 (新增，推荐)
  kimi:
    api_key: ""           # KIMI_API_KEY 或 ANTHROPIC_API_KEY
    base_url: "https://api.kimi.com/coding/"
    model: "kimi-k2-5"
  
  # Azure OpenAI 配置 (保留兼容)
  azure:
    openai_endpoint: ""   # AZURE_OPENAI_ENDPOINT
    openai_key: ""        # AZURE_OPENAI_KEY
    openai_api_version: "2024-02-01"
    deployment_name: "gpt-4"
    
  # Mistral AI 配置 (保留兼容)
  mistral:
    api_key: ""           # MISTRAL_API_KEY
    model: "mistral-large-latest"
    
  # OpenAI 直接配置 (保留兼容)
  openai:
    api_key: ""           # OPENAI_API_KEY
    model: "gpt-4"

# 路径配置
paths:
  input: "input"
  output: "output"
  models: "models"
  temp: "/tmp/edit-banana"

# 处理配置
processing:
  max_image_size: 2048
  supported_formats: ["jpg", "jpeg", "png", "webp"]
  
# 日志配置
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/edit-banana.log"
```

### 3. 修改 modules/__init__.py

```python
# modules/__init__.py
# Edit-Banana 核心模块包

from .sam3_info_extractor import SAM3InfoExtractor
# 添加别名以兼容 main.py
Sam3InfoExtractor = SAM3InfoExtractor

from .icon_picture_processor import IconPictureProcessor
from .basic_shape_processor import BasicShapeProcessor
from .arrow_processor import ArrowProcessor
from .xml_merger import XMLMerger
from .metric_evaluator import MetricEvaluator
from .refinement_processor import RefinementProcessor
from .data_types import (
    ProcessingContext,
    ProcessingResult,
    ElementInfo,
    LayerLevel,
    get_layer_level,
)

# 从 text 子模块导入
try:
    from .text import TextRestorer
except ImportError:
    TextRestorer = None

# OCR 引擎导入 (新增)
def get_ocr_engine(engine_type: str = "kimi", config: dict = None):
    """
    获取 OCR 引擎实例
    
    Args:
        engine_type: "kimi" | "paddle" | "none"
        config: 配置字典
        
    Returns:
        OCR 引擎实例
    """
    if engine_type == "kimi":
        try:
            from .text.kimi_ocr import KimiTextRestorer
            return KimiTextRestorer(config)
        except ImportError as e:
            print(f"Kimi OCR 不可用: {e}")
            return None
    
    elif engine_type == "paddle":
        try:
            # PaddleOCR 实现
            from .text.paddle_ocr import PaddleTextRestorer
            return PaddleTextRestorer(config)
        except ImportError as e:
            print(f"Paddle OCR 不可用: {e}")
            return None
    
    elif engine_type == "none":
        return None
    
    else:
        raise ValueError(f"未知的 OCR 引擎: {engine_type}")


__all__ = [
    'SAM3InfoExtractor',
    'Sam3InfoExtractor',  # 别名
    'IconPictureProcessor',
    'BasicShapeProcessor',
    'ArrowProcessor',
    'XMLMerger',
    'MetricEvaluator',
    'RefinementProcessor',
    'TextRestorer',
    'ProcessingContext',
    'ProcessingResult',
    'ElementInfo',
    'LayerLevel',
    'get_layer_level',
    'get_ocr_engine',  # 新增
]
```

### 4. 修改 streamlit_app.py 侧边栏

```python
# 在 render_sidebar() 函数中新增 Kimi 配置

def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.markdown("## 🔧 API 配置")
        st.markdown("---")
        
        # 加载现有配置
        env_vars = load_env_file()
        
        # 后端状态检查
        # ... (原有代码)
        
        st.markdown("---")
        
        # API Key 输入 (新增 Kimi 选项)
        st.markdown("### API Keys")
        
        # Kimi API (新增，推荐)
        kimi_key = st.text_input(
            "🌙 Kimi API Key (推荐)",
            value=env_vars.get("KIMI_API_KEY", env_vars.get("ANTHROPIC_API_KEY", "")),
            type="password",
            help="Kimi API Key，用于 OCR 和智能功能",
            key="kimi_key"
        )
        
        # OCR 引擎选择 (新增)
        ocr_engine = st.selectbox(
            "OCR 引擎",
            options=["kimi", "paddle", "none"],
            format_func=lambda x: {
                "kimi": "🌙 Kimi (智能识别)",
                "paddle": "📄 PaddleOCR (本地)",
                "none": "❌ 禁用 OCR"
            }[x],
            help="选择文字识别引擎"
        )
        
        # 保留原有 Azure/Mistral/OpenAI 配置（向后兼容）
        with st.expander("🔧 其他 API (兼容)"):
            azure_key = st.text_input(
                "🔷 Azure OpenAI Key",
                value=env_vars.get("AZURE_OPENAI_KEY", ""),
                type="password",
                key="azure_key"
            )
            
            mistral_key = st.text_input(
                "🟣 Mistral API Key",
                value=env_vars.get("MISTRAL_API_KEY", ""),
                type="password",
                key="mistral_key"
            )
            
            openai_key = st.text_input(
                "🟢 OpenAI API Key",
                value=env_vars.get("OPENAI_API_KEY", ""),
                type="password",
                key="openai_key"
            )
        
        st.markdown("---")
        
        # 按钮区域
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 保存配置", type="primary", use_container_width=True):
                new_env = {
                    "KIMI_API_KEY": kimi_key,
                    "ANTHROPIC_API_KEY": kimi_key,  # 同时设置 Anthropic 格式
                    "OCR_ENGINE": ocr_engine,
                    "AZURE_OPENAI_KEY": azure_key,
                    "MISTRAL_API_KEY": mistral_key,
                    "OPENAI_API_KEY": openai_key,
                }
                if save_env_file(new_env):
                    st.success("✅ 配置已保存")
                else:
                    st.error("❌ 保存失败")
        
        with col2:
            if st.button("📋 加载示例", use_container_width=True):
                example = load_example_config()
                st.session_state["kimi_key"] = example.get("KIMI_API_KEY", "")
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📚 关于")
        st.markdown("**Edit-Banana** v1.0")
        st.markdown("图片/PDF 分割与转换工具")
```

---

## 📋 实施计划

### Phase 1: 基础替换 (1-2 天)

- [ ] 1. 验证 Kimi API 连接
  ```bash
  cd Edit-Banana/kimi_patch
  python test_kimi.py
  ```

- [ ] 2. 创建 Kimi OCR 模块
  ```bash
  touch modules/text/kimi_ocr.py
  # 复制上面代码示例
  ```

- [ ] 3. 更新配置文件
  ```bash
  cp config/config.yaml config/config.yaml.backup
  # 添加 Kimi 配置
  ```

### Phase 2: 集成测试 (1-2 天)

- [ ] 4. 测试 OCR 功能
  ```bash
  python -c "
  from modules.text.kimi_ocr import KimiOCR
  ocr = KimiOCR()
  result = ocr.recognize('input/test.png')
  print(result)
  "
  ```

- [ ] 5. 测试 Pipeline 集成
  ```bash
  python main.py -i input/test.png
  ```

### Phase 3: UI 更新 (1 天)

- [ ] 6. 更新 Streamlit 界面
- [ ] 7. 添加 OCR 引擎选择器
- [ ] 8. 测试完整流程

---

## 💰 成本预估

### Kimi API 费用（按 OCR 场景）

| 场景 | 图片大小 | Token 消耗 | 单次成本 |
|------|----------|------------|----------|
| 简单文字 | 512x512 | ~2K | ~¥0.01 |
| 中等复杂 | 1024x1024 | ~4K | ~¥0.02 |
| 复杂图表 | 2048x2048 | ~8K | ~¥0.04 |

**月使用量预估：**
- 轻度使用 (100张/月): ¥1-4
- 中度使用 (1000张/月): ¥10-40
- 重度使用 (10000张/月): ¥100-400

### 对比其他方案

| 方案 | 月成本(1000张) | 优点 | 缺点 |
|------|----------------|------|------|
| **Kimi OCR** | ¥10-40 | 智能识别，无需部署 | 依赖网络 |
| **PaddleOCR** | ¥0 (免费) | 本地运行，隐私安全 | 部署复杂 |
| **Azure OCR** | ¥50-100 | 企业级稳定 | 成本较高 |

---

## 🚀 推荐方案总结

### 推荐方案：全量替换 + PaddleOCR 备用

```
┌─────────────────────────────────────────────────────────┐
│                    Edit-Banana v2.0                     │
├─────────────────────────────────────────────────────────┤
│  OCR 引擎: Kimi (主) + PaddleOCR (备)                    │
│  LLM 功能: Kimi                                         │
│  图像分割: SAM3 本地                                     │
│  背景移除: RMBG 本地                                     │
└─────────────────────────────────────────────────────────┘
```

**理由：**
1. Kimi OCR 足够应对大多数场景
2. PaddleOCR 作为离线备用
3. 无 Azure/OpenAI 依赖，成本可控
4. 实现简单，快速上线

---

## 📞 后续支持

如有问题，可以：
1. 查看 `kimi_patch/README.md` 已有文档
2. 测试 `kimi_patch/test_kimi.py` 验证连接
3. 参考本报告代码示例进行实现

---

**报告生成时间**: 2026-02-10
**分析师**: AI Assistant
**版本**: v1.0
