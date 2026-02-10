# Edit-Banana API 修复建议报告

## 1. API 替换可行性分析表

| 原 API | 用途 | 是否可替换 | 替换方案 | 难度 | 备注 |
|--------|------|-----------|---------|------|------|
| **Azure Document Intelligence** | 文本定位/OCR | ⚠️ 部分可 | PaddleOCR / EasyOCR + Kimi 校验 | 高 | OCR 需要专用模型，Kimi 无法直接替代 |
| **Azure OpenAI (GPT-4V)** | 图像理解/分析 | ✅ 是 | Kimi 视觉模型 (kimi-v1) | 低 | 直接替换，API 格式兼容 |
| **OpenAI GPT-4V** | 图像理解 | ✅ 是 | Kimi 视觉模型 | 低 | 直接替换 |
| **Mistral** | 公式识别/LaTeX | ✅ 是 | Kimi 文本模型 | 低 | Kimi 支持 LaTeX 输出 |
| **Mistral** | 文本修正 | ✅ 是 | Kimi 文本模型 | 低 | 直接替换 |

### Kimi API 能力验证

```bash
# Kimi API 端点
ANTHROPIC_BASE_URL=https://api.kimi.com/coding/
ANTHROPIC_API_KEY=sk-kimi-SckItPdArEsXNGKFoCYHMd8uG1FjpDnG8m1mEi1vQ6VMzhMhtVgFVqKilMthoVXN
```

**Kimi 支持的能力：**
- ✅ 文本生成（与 Claude 兼容的 API 格式）
- ✅ 多模态（图像理解，支持 Vision）
- ✅ 长上下文（支持 128K+ tokens）
- ✅ LaTeX 公式生成（测试通过）
- ❌ 专用 OCR 文本定位（需要替代方案）

---

## 2. 三种方案对比

### 方案 A: 全量替换（推荐）

**方案描述：**
- 将所有 LLM 调用（GPT-4V、Mistral）替换为 Kimi API
- OCR 部分使用开源替代（PaddleOCR）+ Kimi 后处理校验

**优点：**
- 统一使用 Kimi API，维护简单
- 完全摆脱 Azure/OpenAI/Mistral 依赖
- 成本可控（Kimi 价格相对较低）

**缺点：**
- OCR 部分需要额外集成 PaddleOCR
- 需要测试 PaddleOCR 的准确率

**工作量：**
- 修改配置文件和 API 客户端代码
- 集成 PaddleOCR（约 2-3 天）
- 测试和调优（约 1-2 天）

**适用场景：**
- 不想申请多个 API Key
- 希望在本地/私有环境运行

---

### 方案 B: 混合架构

**方案描述：**
- LLM 部分全部使用 Kimi 替代
- OCR 部分保留 Azure Document Intelligence 或申请免费额度

**优点：**
- OCR 准确率有保障（Azure DI 专业级）
- 架构清晰，职责分离

**缺点：**
- 仍需 Azure API Key
- 需要管理多个服务商

**工作量：**
- 修改 LLM 调用代码（约 1 天）
- 配置 Azure OCR（约 0.5 天）

**适用场景：**
- 对 OCR 准确率要求极高
- 可以接受多服务商管理

---

### 方案 C: 简化版（快速启动）

**方案描述：**
- 仅使用 Kimi 进行图像描述和基础分割
- 暂时禁用 OCR 和公式识别功能
- 后续逐步添加

**优点：**
- 最快启动（当天可用）
- 代码改动最小
- 可以快速验证核心流程

**缺点：**
- 功能不完整（无文字提取）
- 输出质量受限

**工作量：**
- 修改配置（约 2 小时）
- 禁用 text 模块（约 1 小时）

**适用场景：**
- 快速验证项目可行性
- MVP 演示

---

## 3. 推荐的修复步骤（分优先级）

### 优先级 1: 立即执行（今天完成）

1. **修改 .env 配置**
   - 添加 Kimi API 配置
   - 保留原有配置（兼容回退）

2. **创建统一 LLM 客户端**
   - 封装 Kimi API 调用
   - 实现与现有接口的适配层

3. **测试 Kimi API 连通性**
   - 验证文本生成功能
   - 验证图像理解功能

### 优先级 2: 短期完成（本周内）

4. **替换 Mistral 调用**
   - 公式识别 → Kimi
   - 文本修正 → Kimi

5. **替换 GPT-4V 调用**
   - 图像分析 → Kimi Vision

6. **集成 PaddleOCR（方案 A）或保留 Azure OCR（方案 B）**

### 优先级 3: 中期优化（下周）

7. **完善错误处理和降级机制**
8. **添加缓存层减少 API 调用**
9. **性能优化和并发处理**

---

## 4. 代码修改示例

### 4.1 配置文件修改（.env）

**原配置：**
```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-azure-openai-key
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Mistral
MISTRAL_API_KEY=your-mistral-key
MISTRAL_MODEL=mistral-large-latest

# OpenAI
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4
```

**新配置（推荐）：**
```bash
# ============================================
# Kimi API 配置（主用）
# ============================================
KIMI_BASE_URL=https://api.kimi.com/coding/
KIMI_API_KEY=sk-kimi-SckItPdArEsXNGKFoCYHMd8uG1FjpDnG8m1mEi1vQ6VMzhMhtVgFVqKilMthoVXN
KIMI_MODEL=kimi-v1

# ============================================
# LLM 提供商选择
# ============================================
# 可选值: kimi, azure, openai, mistral
LLM_PROVIDER=kimi

# ============================================
# OCR 配置（方案 A: 开源）
# ============================================
OCR_ENGINE=paddleocr  # 可选: paddleocr, azure, easyocr, none
PADDLEOCR_LANG=ch_sim,en

# ============================================
# Azure 配置（方案 B: 保留）
# ============================================
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-azure-openai-key
AZURE_OCR_ENDPOINT=https://your-ocr.cognitiveservices.azure.com/
AZURE_OCR_KEY=your-ocr-key

# ============================================
# 备用配置（可选）
# ============================================
MISTRAL_API_KEY=your-mistral-key
OPENAI_API_KEY=your-openai-key
```

### 4.2 创建统一 LLM 客户端

**新文件：`modules/llm_client.py`**

```python
"""
统一 LLM 客户端
支持 Kimi、Azure、OpenAI、Mistral 等多种后端
"""

import os
import base64
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod

# 尝试导入各种客户端
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from openai import AzureOpenAI, OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import mistralai
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False


class BaseLLMClient(ABC):
    """LLM 客户端基类"""
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """发送聊天请求"""
        pass
    
    @abstractmethod
    def chat_with_image(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """发送带图片的聊天请求"""
        pass


class KimiClient(BaseLLMClient):
    """Kimi API 客户端（Anthropic 格式）"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package required. Install: pip install anthropic")
        
        self.api_key = api_key or os.getenv("KIMI_API_KEY")
        self.base_url = base_url or os.getenv("KIMI_BASE_URL", "https://api.kimi.com/coding/")
        self.model = os.getenv("KIMI_MODEL", "kimi-v1")
        
        self.client = anthropic.Anthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """发送纯文本聊天请求"""
        # 转换消息格式为 Anthropic 格式
        system_msg = ""
        chat_messages = []
        
        for msg in messages:
            if msg.get("role") == "system":
                system_msg = msg.get("content", "")
            else:
                chat_messages.append({
                    "role": msg.get("role"),
                    "content": msg.get("content", "")
                })
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7),
            system=system_msg,
            messages=chat_messages
        )
        
        return response.content[0].text
    
    def chat_with_image(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """发送带图片的聊天请求"""
        system_msg = ""
        chat_messages = []
        
        for msg in messages:
            if msg.get("role") == "system":
                system_msg = msg.get("content", "")
            elif msg.get("role") == "user":
                content = msg.get("content", [])
                # 处理多模态内容
                formatted_content = []
                for item in content:
                    if item.get("type") == "text":
                        formatted_content.append({
                            "type": "text",
                            "text": item.get("text", "")
                        })
                    elif item.get("type") == "image_url":
                        # 处理图片
                        image_url = item.get("image_url", {}).get("url", "")
                        if image_url.startswith("data:image"):
                            # base64 图片
                            import re
                            match = re.match(r'data:image/[^;]+;base64,(.+)', image_url)
                            if match:
                                base64_data = match.group(1)
                                formatted_content.append({
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/png",
                                        "data": base64_data
                                    }
                                })
                
                chat_messages.append({
                    "role": "user",
                    "content": formatted_content
                })
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7),
            system=system_msg,
            messages=chat_messages
        )
        
        return response.content[0].text


class AzureOpenAIClient(BaseLLMClient):
    """Azure OpenAI 客户端"""
    
    def __init__(self):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package required. Install: pip install openai")
        
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7)
        )
        return response.choices[0].message.content
    
    def chat_with_image(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        # Azure 也使用相同的 chat 接口，messages 中包含 image_url
        return self.chat(messages, **kwargs)


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
            elif provider == "azure":
                cls._clients[provider] = AzureOpenAIClient()
            elif provider == "openai":
                # 可扩展
                raise NotImplementedError("OpenAI client not implemented yet")
            elif provider == "mistral":
                raise NotImplementedError("Mistral client not implemented yet")
            else:
                raise ValueError(f"Unknown LLM provider: {provider}")
        
        return cls._clients[provider]
    
    @classmethod
    def reset(cls):
        """重置所有客户端（用于测试）"""
        cls._clients = {}


# 便捷函数
def chat(messages: List[Dict[str, str]], **kwargs) -> str:
    """使用默认 provider 发送聊天请求"""
    client = LLMClientFactory.get_client()
    return client.chat(messages, **kwargs)


def chat_with_image(messages: List[Dict[str, Any]], **kwargs) -> str:
    """使用默认 provider 发送带图片的聊天请求"""
    client = LLMClientFactory.get_client()
    return client.chat_with_image(messages, **kwargs)
```

### 4.3 OCR 客户端（PaddleOCR 方案）

**新文件：`modules/ocr_client.py`**

```python
"""
统一 OCR 客户端
支持 PaddleOCR、Azure、EasyOCR 等多种后端
"""

import os
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
import numpy as np


class BaseOCRClient(ABC):
    """OCR 客户端基类"""
    
    @abstractmethod
    def recognize(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        识别图像中的文字
        
        Returns:
            List[{
                "text": str,
                "confidence": float,
                "bbox": {"x": int, "y": int, "width": int, "height": int}
            }]
        """
        pass


class PaddleOCRClient(BaseOCRClient):
    """PaddleOCR 客户端"""
    
    def __init__(self, lang: str = "ch_sim,en"):
        try:
            from paddleocr import PaddleOCR
        except ImportError:
            raise ImportError("paddleocr required. Install: pip install paddleocr")
        
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang=lang,
            show_log=False
        )
    
    def recognize(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """使用 PaddleOCR 识别文字"""
        result = self.ocr.ocr(image, cls=True)
        
        texts = []
        if result and result[0]:
            for line in result[0]:
                if line:
                    bbox = line[0]  # 四个角点坐标
                    text = line[1][0]  # 文字内容
                    confidence = line[1][1]  # 置信度
                    
                    # 计算矩形框
                    xs = [p[0] for p in bbox]
                    ys = [p[1] for p in bbox]
                    x_min, x_max = min(xs), max(xs)
                    y_min, y_max = min(ys), max(ys)
                    
                    texts.append({
                        "text": text,
                        "confidence": confidence,
                        "bbox": {
                            "x": int(x_min),
                            "y": int(y_min),
                            "width": int(x_max - x_min),
                            "height": int(y_max - y_min)
                        }
                    })
        
        return texts


class AzureOCRClient(BaseOCRClient):
    """Azure Document Intelligence 客户端"""
    
    def __init__(self):
        self.endpoint = os.getenv("AZURE_OCR_ENDPOINT")
        self.key = os.getenv("AZURE_OCR_KEY")
        
        if not self.endpoint or not self.key:
            raise ValueError("Azure OCR credentials not configured")
    
    def recognize(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """使用 Azure DI 识别文字"""
        # Azure DI 实现
        # 参考: https://docs.microsoft.com/azure/ai-services/document-intelligence/
        raise NotImplementedError("Azure OCR implementation pending")


class OCRClientFactory:
    """OCR 客户端工厂"""
    
    _clients: Dict[str, BaseOCRClient] = {}
    
    @classmethod
    def get_client(cls, engine: Optional[str] = None) -> Optional[BaseOCRClient]:
        """获取 OCR 客户端实例"""
        engine = engine or os.getenv("OCR_ENGINE", "paddleocr")
        
        if engine == "none":
            return None
        
        if engine not in cls._clients:
            if engine == "paddleocr":
                lang = os.getenv("PADDLEOCR_LANG", "ch_sim,en")
                cls._clients[engine] = PaddleOCRClient(lang=lang)
            elif engine == "azure":
                cls._clients[engine] = AzureOCRClient()
            elif engine == "easyocr":
                raise NotImplementedError("EasyOCR not implemented yet")
            else:
                raise ValueError(f"Unknown OCR engine: {engine}")
        
        return cls._clients[engine]
```

### 4.4 TextRestorer 修改

**修改：`modules/text/text_render.py`**

```python
"""
Text Render Module
文字渲染和恢复 - 支持多种 LLM 和 OCR 后端
"""

import os
from typing import Optional, Dict, Any, List
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# 导入统一客户端
try:
    from modules.llm_client import chat, chat_with_image, LLMClientFactory
    from modules.ocr_client import OCRClientFactory
    CLIENTS_AVAILABLE = True
except ImportError:
    CLIENTS_AVAILABLE = False


class TextRestorer:
    """文字恢复器 - 支持 Kimi/Azure/OpenAI/Mistral"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.default_font_size = self.config.get("default_font_size", 14)
        self.default_font_family = self.config.get("default_font_family", "Arial")
        self.formula_engine = self.config.get("formula_engine", "kimi")  # kimi / none
        
        # 初始化客户端
        self._ocr_client = None
        self._llm_client = None
        
        if CLIENTS_AVAILABLE:
            try:
                self._ocr_client = OCRClientFactory.get_client()
            except Exception as e:
                print(f"OCR client initialization failed: {e}")
            
            try:
                self._llm_client = LLMClientFactory.get_client()
            except Exception as e:
                print(f"LLM client initialization failed: {e}")
    
    def process(self, image_path: str) -> str:
        """
        处理图像，提取文字并生成 XML
        
        Args:
            image_path: 输入图像路径
            
        Returns:
            str: DrawIO XML 格式字符串
        """
        import cv2
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Cannot load image: {image_path}")
        
        # 1. OCR 检测文字区域
        text_regions = self._detect_text_regions(image)
        
        # 2. 对每个区域进行详细识别
        recognized_texts = []
        for region in text_regions:
            text_info = self._recognize_text_detail(image, region)
            recognized_texts.append(text_info)
        
        # 3. 生成 XML
        xml_content = self._generate_xml(recognized_texts)
        return xml_content
    
    def _detect_text_regions(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """检测文字区域"""
        if self._ocr_client:
            return self._ocr_client.recognize(image)
        return []
    
    def _recognize_text_detail(self, image: np.ndarray, region: Dict[str, Any]) -> Dict[str, Any]:
        """详细识别文字内容（包括公式）"""
        bbox = region.get("bbox", {})
        x, y = bbox.get("x", 0), bbox.get("y", 0)
        w, h = bbox.get("width", 0), bbox.get("height", 0)
        
        # 裁剪区域
        crop = image[y:y+h, x:x+w]
        
        # 基础文字
        text = region.get("text", "")
        
        # 如果是公式模式，使用 LLM 进一步识别
        if self.formula_engine != "none" and self._llm_client:
            text = self._recognize_formula(crop, text)
        
        return {
            "text": text,
            "bbox": bbox,
            "confidence": region.get("confidence", 0),
            "is_formula": self._is_formula(text)
        }
    
    def _recognize_formula(self, image_crop: np.ndarray, hint_text: str) -> str:
        """使用 LLM 识别公式"""
        try:
            # 将图片转为 base64
            import cv2
            from PIL import Image
            import io
            import base64
            
            # 转换颜色空间
            if len(image_crop.shape) == 3:
                image_crop = cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB)
            
            pil_image = Image.fromarray(image_crop)
            buffer = io.BytesIO()
            pil_image.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # 构建提示
            prompt = f"""识别图片中的数学公式或文字。
如果包含数学公式，请转换为 LaTeX 格式（使用 $ 包裹）。
如果只有普通文字，直接返回文字内容。
OCR 提示: {hint_text}

只返回识别结果，不要解释。"""
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
                    ]
                }
            ]
            
            result = self._llm_client.chat_with_image(messages, temperature=0.3)
            return result.strip()
            
        except Exception as e:
            print(f"Formula recognition failed: {e}")
            return hint_text
    
    def _is_formula(self, text: str) -> bool:
        """判断是否为公式"""
        formula_indicators = ['$', '\\', '^', '_', '{', '}', 'frac', 'sum', 'int', 'sqrt']
        return any(indicator in text for indicator in formula_indicators)
    
    def _generate_xml(self, texts: List[Dict[str, Any]]) -> str:
        """生成 DrawIO XML"""
        # 简化版 XML 生成
        xml_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<mxfile version="21.0">',
            '<diagram name="Page-1">',
            '<mxGraphModel dx="800" dy="600" grid="1">',
            '<root>',
            '<mxCell id="0" />',
            '<mxCell id="1" parent="0" />'
        ]
        
        for i, text_info in enumerate(texts, start=2):
            bbox = text_info.get("bbox", {})
            x, y = bbox.get("x", 0), bbox.get("y", 0)
            w, h = bbox.get("width", 100), bbox.get("height", 20)
            text = text_info.get("text", "")
            
            # 转义特殊字符
            text_escaped = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
            
            xml_parts.append(
                f'<mxCell id="{i}" value="{text_escaped}" style="text;html=1;" '
                f'vertex="1" parent="1">'
                f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />'
                f'</mxCell>'
            )
        
        xml_parts.extend([
            '</root>',
            '</mxGraphModel>',
            '</diagram>',
            '</mxfile>'
        ])
        
        return '\n'.join(xml_parts)
    
    def restore_text(self, image: np.ndarray, text_info: Dict[str, Any]) -> np.ndarray:
        """在图像上恢复文字（原有功能保留）"""
        if len(image.shape) == 2:
            pil_image = Image.fromarray(image).convert('RGB')
        else:
            pil_image = Image.fromarray(image)
        
        draw = ImageDraw.Draw(pil_image)
        text = text_info.get("text", "")
        bbox = text_info.get("bbox", {"x": 0, "y": 0, "width": 100, "height": 20})
        
        x = int(bbox.get("x", 0))
        y = int(bbox.get("y", 0))
        
        try:
            font = ImageFont.truetype(self.default_font_family, self.default_font_size)
        except:
            font = ImageFont.load_default()
        
        draw.text((x, y), text, fill=(0, 0, 0), font=font)
        return np.array(pil_image)
```

---

## 5. 配置建议

### 5.1 环境变量 (.env)

```bash
# ============================================
# 主配置：Kimi API
# ============================================
KIMI_BASE_URL=https://api.kimi.com/coding/
KIMI_API_KEY=sk-kimi-SckItPdArEsXNGKFoCYHMd8uG1FjpDnG8m1mEi1vQ6VMzhMhtVgFVqKilMthoVXN
KIMI_MODEL=kimi-v1

# ============================================
# 提供商选择
# ============================================
LLM_PROVIDER=kimi           # 主 LLM: kimi / azure / openai / mistral
OCR_ENGINE=paddleocr        # OCR: paddleocr / azure / easyocr / none

# ============================================
# OCR 配置
# ============================================
PADDLEOCR_LANG=ch_sim,en    # PaddleOCR 语言包

# ============================================
# 备用配置（可选）
# ============================================
# Azure OpenAI（如需要）
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-azure-openai-key
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Azure OCR（如需要）
AZURE_OCR_ENDPOINT=https://your-ocr.cognitiveservices.azure.com/
AZURE_OCR_KEY=your-ocr-key

# Mistral（如需要）
MISTRAL_API_KEY=your-mistral-key
MISTRAL_MODEL=mistral-large-latest

# OpenAI（如需要）
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4

# ============================================
# 模型路径
# ============================================
SAM3_CHECKPOINT_PATH=models/sam3_checkpoint.pth

# ============================================
# 应用配置
# ============================================
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
```

### 5.2 依赖安装 (requirements.txt)

```txt
# 基础依赖
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0
python-dotenv>=1.0.0
pyyaml>=6.0

# 图像处理
numpy>=1.24.0
opencv-python>=4.8.0
pillow>=10.0.0

# 深度学习
torch>=2.0.0
torchvision>=0.15.0
transformers>=4.35.0
accelerate>=0.24.0

# LLM 客户端（必选其一）
anthropic>=0.8.0          # Kimi API（Anthropic 格式）
# openai>=1.0.0           # Azure/OpenAI（可选）
# mistralai>=0.0.8        # Mistral（可选）

# OCR 引擎（根据配置选择）
paddleocr>=2.7.0          # 推荐中文 OCR
paddlepaddle>=2.5.0       # Paddle 基础库
# easyocr>=1.7.0          # 备选 OCR

# 可选依赖
spandrel>=0.1.0           # 超分模型
python-pptx>=0.6.21       # PPTX 生成
```

### 5.3 安装脚本

```bash
#!/bin/bash
# setup.sh - 快速安装脚本

echo "🚀 Edit-Banana 安装脚本"

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装基础依赖
echo "📦 安装基础依赖..."
pip install fastapi uvicorn pydantic python-dotenv pyyaml
pip install numpy opencv-python pillow

# 安装深度学习框架
echo "📦 安装 PyTorch..."
pip install torch torchvision

# 安装 LLM 客户端
echo "📦 安装 LLM 客户端..."
pip install anthropic  # Kimi

# 安装 OCR 引擎
echo "📦 安装 PaddleOCR..."
pip install paddlepaddle paddleocr

# 可选依赖
echo "📦 安装可选依赖..."
pip install transformers accelerate

echo "✅ 安装完成！"
echo ""
echo "下一步："
echo "1. 复制 .env.example 为 .env"
echo "2. 填入你的 API Keys"
echo "3. 运行: python server_pa.py"
```

---

## 6. 测试验证清单

### 6.1 单元测试

```python
# tests/test_llm_client.py
import pytest
from modules.llm_client import KimiClient, LLMClientFactory

def test_kimi_client_init():
    """测试 Kimi 客户端初始化"""
    client = KimiClient()
    assert client.api_key is not None
    assert client.base_url is not None

def test_kimi_chat():
    """测试 Kimi 聊天功能"""
    client = KimiClient()
    messages = [
        {"role": "user", "content": "Hello, this is a test."}
    ]
    response = client.chat(messages, max_tokens=50)
    assert len(response) > 0

def test_kimi_vision():
    """测试 Kimi 图像理解"""
    client = KimiClient()
    # 使用 base64 测试图片
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What is this image?"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
            ]
        }
    ]
    response = client.chat_with_image(messages, max_tokens=100)
    assert len(response) > 0
```

### 6.2 集成测试

```python
# tests/test_text_restorer.py
import pytest
import numpy as np
from modules.text.text_render import TextRestorer

def test_text_restorer_init():
    """测试 TextRestorer 初始化"""
    restorer = TextRestorer()
    assert restorer.default_font_size == 14

def test_text_restorer_process():
    """测试文字提取流程"""
    restorer = TextRestorer()
    # 创建测试图像
    image = np.ones((100, 200, 3), dtype=np.uint8) * 255
    # 测试处理（需要真实图像文件）
    # xml = restorer.process("test_image.png")
    # assert "mxfile" in xml
```

---

## 7. 常见问题 FAQ

### Q1: Kimi API 是否支持 LaTeX 公式？
**A:** ✅ 支持。Kimi 可以理解和生成 LaTeX 格式的数学公式。

### Q2: PaddleOCR 的中文识别准确率如何？
**A:** PaddleOCR 是开源 OCR 中中文识别效果最好的之一，支持中英文混合识别，准确率接近商业 API。

### Q3: 如果不想用 PaddleOCR，还有什么选择？
**A:** 可选方案：
- EasyOCR（多语言支持好）
- Tesseract（老牌开源 OCR）
- 阿里云/腾讯云 OCR（国内 API）

### Q4: Kimi API 的调用限制是什么？
**A:** 请参考 Moonshot AI 官方文档获取最新的速率限制信息。

### Q5: 如何回退到原来的 Azure/OpenAI？
**A:** 只需修改 `.env` 中的 `LLM_PROVIDER` 和 `OCR_ENGINE` 配置即可无缝切换。

---

## 8. 总结与建议

### 推荐方案：方案 A（全量替换）

**理由：**
1. 完全摆脱对 Azure/OpenAI/Mistral 的依赖
2. Kimi 在中文场景下表现优异
3. PaddleOCR 开源免费，准确率可接受
4. 统一技术栈，维护简单

### 实施时间线

| 阶段 | 任务 | 预计时间 |
|------|------|---------|
| Day 1 | 创建 LLM/OCR 客户端 | 4 小时 |
| Day 2 | 修改 TextRestorer | 4 小时 |
| Day 3 | 集成测试 | 4 小时 |
| Day 4 | Bug 修复和优化 | 4 小时 |

### 风险提示

1. **PaddleOCR 首次运行会自动下载模型**（约 100MB），需要网络连接
2. **Kimi API 可能需要申请内测/正式账号**
3. **OCR 准确率可能略低于 Azure DI**，需要针对具体场景调优

### 下一步行动

等待 Team Lead 确认方案后，开始实施代码修改。

---

**报告生成时间:** 2026-02-10
**报告作者:** API Fix Suggestion Agent
**状态:** 待确认
