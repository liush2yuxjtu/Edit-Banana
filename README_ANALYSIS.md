# Edit-Banana README 分析

## 项目简介

**Edit-Banana** 是一个通用内容重编辑器，能够将静态图片/PDF 转换为可编辑的 DrawIO (XML) 或 PPTX 格式。项目基于 SAM 3 分割模型和多模态大语言模型，实现高保真重建，保留原始图表细节和逻辑关系。

### 核心功能
- **图像分割**：使用微调后的 SAM 3 (Segment Anything Model 3) 进行图表元素分割
- **文本提取**：结合 Azure OCR 和多模态大模型 (Qwen-VL/GPT-4V) 进行高精度文字识别
- **公式识别**：支持数学公式转换为 LaTeX 格式
- **格式转换**：输出可编辑的 DrawIO XML 或 PPTX 格式
- **Web 界面**：基于 React 的前端 + FastAPI 后端

### 在线演示
- 网址: https://editbanana.anxin6.cn/
- 注意：GitHub 仓库版本落后于在线服务

---

## 系统要求

### 基础要求
- **Python**: 3.10+
- **Node.js & npm**: 用于前端 (安装依赖)
- **CUDA-capable GPU**: 强烈推荐 (支持 CUDA/MPS/CPU)

### 支持平台
- macOS (MPS 加速)
- Linux (CUDA 加速)
- Windows (WSL 推荐)

---

## 安装步骤

### 1. 克隆仓库
```bash
git clone https://github.com/BIT-DataLab/Edit-Banana.git
cd Edit-Banana
```

### 2. 创建必要目录
```bash
mkdir -p input
mkdir -p output
mkdir -p sam3_output
mkdir -p uploads
mkdir -p logs
```

### 3. 下载模型权重
| 模型 | 下载地址 | 目标路径 |
|------|---------|---------|
| SAM 3 | https://modelscope.cn/models/facebook/sam3 | `models/sam3_checkpoint.pth` |

当前项目模型目录 (`models/`) 已包含:
- `sam3_checkpoint.pth` (3.45 GB)
- `sam3_model.safetensors` (3.44 GB)

### 4. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件填入 API Keys
```

### 5. 配置 config.yaml
```bash
# 复制配置文件
cp config/config.yaml.example config/config.yaml

# 根据需要修改设备配置 (mps/cuda/cpu)
```

### 6. 安装 Python 依赖
**注意：项目目前没有 requirements.txt 文件，需要手动安装以下依赖：**

```bash
# 核心依赖
pip install torch torchvision
pip install fastapi uvicorn pydantic python-dotenv pyyaml
pip install numpy opencv-python pillow
pip install transformers accelerate

# 可选依赖 (根据功能需要)
pip install spandrel  # 超分模型支持
```

### 7. 安装前端依赖
```bash
cd frontend
npm install
cd ..
```

---

## 启动命令

### 方式一：Web 界面 (推荐)

**启动后端服务：**
```bash
# 使用 FastAPI 服务器
python server_pa.py

# 服务运行在 http://localhost:8000
```

**启动前端服务：**
```bash
cd frontend
npm run dev

# 前端运行在 http://localhost:5173
```

### 方式二：命令行界面 (CLI)

```bash
# 处理单张图片
python main.py -i input/test_diagram.png

# 自定义输出目录
python main.py -i input/test.png -o output/custom/

# 启用精修模式
python main.py -i input/test.png --refine

# 跳过文字处理
python main.py -i input/test.png --no-text
```

### 方式三：仅文字提取
```bash
python flowchart_text/main.py -i input/diagram.png -o output/
```

---

## 配置需求

### API Keys (必需)

项目需要以下 API Keys，在 `.env` 文件中配置：

| 变量名 | 说明 | 来源 |
|-------|------|------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI 服务端点 | Azure Portal |
| `AZURE_OPENAI_KEY` | Azure OpenAI API Key | Azure Portal |
| `AZURE_OPENAI_API_VERSION` | API 版本 | 默认: 2024-02-01 |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | 部署名称 | 默认: gpt-4 |
| `MISTRAL_API_KEY` | Mistral AI API Key | Mistral Platform |
| `OPENAI_API_KEY` | OpenAI API Key (可选) | OpenAI Platform |

### 环境变量完整列表

```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-azure-openai-key-here
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Mistral AI
MISTRAL_API_KEY=your-mistral-api-key-here
MISTRAL_MODEL=mistral-large-latest

# OpenAI (可选)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4

# 模型路径
SAM3_CHECKPOINT_PATH=models/sam3_checkpoint.pth
FLUX_MODEL_PATH=models/flux

# Mac MPS 配置
PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.7

# 应用配置
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
```

### 模型文件

| 文件 | 路径 | 大小 |
|-----|------|------|
| SAM 3 Checkpoint | `models/sam3_checkpoint.pth` | ~3.45 GB |
| SAM 3 SafeTensors | `models/sam3_model.safetensors` | ~3.44 GB |

### 配置文件 (config.yaml)

关键配置项：
```yaml
models:
  sam3:
    checkpoint: "models/sam3_checkpoint.pth"
    device: "mps"  # 可选: cuda, cpu, mps
  
  diffusion:
    model_id: "black-forest-labs/FLUX.1-dev"
    device: "mps"
```

---

## 关键发现

### 1. 项目结构
```
Edit-Banana/
├── config/           # 配置文件
├── flowchart_text/   # OCR & 文本提取模块
├── frontend/         # React 前端
├── input/            # 输入图片目录
├── models/           # 模型权重
├── modules/          # 核心处理模块
│   ├── arrow_processor.py
│   ├── icon_picture_processor.py
│   ├── sam3_info_extractor.py
│   ├── text/         # 文字处理模块 (部分文件缺失)
│   └── utils/        # 工具函数
├── output/           # 输出结果目录
├── sam3/             # SAM3 模型库
├── sam3_service/     # SAM3 服务 (client/server)
├── scripts/          # 实用脚本
├── static/           # 静态资源
├── uploads/          # 上传文件目录
├── main.py           # CLI 入口
└── server_pa.py      # FastAPI 后端
```

### 2. 处理流程
```
输入 (图片/PDF) → SAM3 分割 → 文本提取 (OCR) → XML/PPTX 生成
```

### 3. 文字处理模块状态
- `modules/text/` 目录下的部分核心文件为空或仅包含占位符内容
- `restorer.py` 文件缺失，可能导致文字提取功能无法正常使用
- `font_recognize.py`, `font_renderer.py`, `ocr_recognize.py` 等文件需要完善

### 4. 依赖分析
从代码导入分析，需要的 Python 包包括：
- `torch`, `torchvision` - 深度学习框架
- `fastapi`, `uvicorn` - Web 服务
- `pydantic` - 数据验证
- `python-dotenv` - 环境变量
- `pyyaml` - YAML 配置
- `numpy`, `opencv-python`, `pillow` - 图像处理
- `transformers`, `accelerate` - Hugging Face 模型
- `spandrel` (可选) - 超分模型

### 5. 设备支持
- 优先使用 GPU (CUDA for NVIDIA, MPS for Apple Silicon)
- 支持 CPU 回退模式

---

## 潜在问题

### 1. **缺少 requirements.txt**
- 项目没有提供 requirements.txt 文件
- 需要用户手动安装依赖，容易遗漏或版本冲突
- **建议**: 创建 requirements.txt 文件

### 2. **文字处理模块不完整**
- `modules/text/` 目录下的多个文件为空
- `restorer.py` 文件缺失
- **影响**: 可能导致文字提取和 OCR 功能无法正常工作

### 3. **API Key 依赖**
- 需要 Azure OpenAI 和 Mistral AI 的 API Keys
- 没有提供免费的替代方案
- **建议**: 考虑添加本地模型支持

### 4. **模型文件体积大**
- SAM 3 模型约 6.9 GB
- 需要足够的磁盘空间和内存

### 5. **前端缺失**
- 项目没有包含前端代码 (frontend 目录可能为空)
- 需要单独开发或从其他来源获取

### 6. **文档与代码不同步**
- README 提到的一些功能可能在代码中未实现
- 开发路线图中的部分功能标记为"进行中"或"计划中"

### 7. **多用户并发**
- 使用内存中的任务存储 (`tasks: Dict`)
- 生产环境需要使用 Redis 等持久化存储

---

## 建议

1. **创建 requirements.txt** 以简化依赖安装
2. **完善 text 模块** 实现文字提取功能
3. **提供前端代码** 或详细的 API 文档
4. **添加本地模型支持** 减少对 API 的依赖
5. **完善错误处理和日志记录**
6. **添加 Docker 支持** 简化部署
