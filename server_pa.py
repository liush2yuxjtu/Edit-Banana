#!/usr/bin/env python3
"""
Edit-Banana Backend Server
FastAPI 后端主文件 - 图片/PDF 分割与转换服务
使用真实实现替代模拟代码
"""

import os
import sys
import json
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 添加项目根目录到 sys.path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# 导入 Edit-Banana 核心模块
from main import Pipeline, load_config
from modules.sam3_info_extractor import PromptGroup

# ============================================
# 配置
# ============================================
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
APP_DEBUG = os.getenv("APP_DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 路径配置
BASE_DIR = Path(__file__).parent.absolute()
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
MODELS_DIR = BASE_DIR / "models"
TEMPLATES_DIR = BASE_DIR / "templates"

# 确保目录存在
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

# 初始化模板引擎
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# 全局 Pipeline 实例
_pipeline: Optional[Pipeline] = None

# ============================================
# 数据模型
# ============================================
class UploadResponse(BaseModel):
    success: bool
    message: str
    file_id: Optional[str] = None
    filename: Optional[str] = None
    file_type: Optional[str] = None
    file_url: Optional[str] = None

class SegmentRequest(BaseModel):
    file_id: str
    auto_segment: bool = True
    prompt: Optional[str] = None
    groups: Optional[List[str]] = None  # 可选的分组: image, arrow, shape, background

class SegmentResponse(BaseModel):
    success: bool
    message: str
    task_id: Optional[str] = None
    segments: Optional[List[Dict[str, Any]]] = None
    preview_url: Optional[str] = None

class ConvertRequest(BaseModel):
    task_id: str
    output_format: str = "drawio"  # drawio 或 pptx
    include_annotations: bool = True

class ConvertResponse(BaseModel):
    success: bool
    message: str
    download_url: Optional[str] = None
    file_size: Optional[int] = None

class StatusResponse(BaseModel):
    status: str
    timestamp: str
    version: str = "1.0.0"
    features: Dict[str, bool]
    models: Dict[str, bool]

class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: int = 0
    message: Optional[str] = None
    created_at: str
    updated_at: str
    result: Optional[Dict[str, Any]] = None

# ============================================
# 任务存储 (内存中，生产环境应使用 Redis)
# ============================================
tasks: Dict[str, TaskStatus] = {}

# ============================================
# 生命周期管理
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global _pipeline

    # 启动时执行
    print("🚀 Edit-Banana Backend 启动中...")
    print(f"📁 上传目录: {UPLOAD_DIR}")
    print(f"📁 输出目录: {OUTPUT_DIR}")
    print(f"📁 模型目录: {MODELS_DIR}")

    # 初始化 Pipeline
    try:
        config = load_config()
        _pipeline = Pipeline(config)
        print("✅ Pipeline 初始化成功")
    except Exception as e:
        print(f"⚠️ Pipeline 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        _pipeline = None

    # 检查模型文件
    sam3_path = MODELS_DIR / "sam3_checkpoint.pth"
    if sam3_path.exists():
        print(f"✅ SAM3 模型已找到: {sam3_path}")
    else:
        print(f"⚠️ SAM3 模型未找到: {sam3_path}")

    yield

    # 关闭时执行
    print("👋 Edit-Banana Backend 已关闭")

# ============================================
# 创建 FastAPI 应用
# ============================================
app = FastAPI(
    title="Edit-Banana API",
    description="图片/PDF 分割与转换服务",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# ============================================
# 辅助函数
# ============================================
def generate_id() -> str:
    """生成唯一 ID"""
    return str(uuid.uuid4())[:8]

def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    return Path(filename).suffix.lower()

def is_valid_image(filename: str) -> bool:
    """检查是否为支持的图片格式"""
    valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    return get_file_extension(filename) in valid_extensions

def is_valid_pdf(filename: str) -> bool:
    """检查是否为 PDF"""
    return get_file_extension(filename) == '.pdf'

def create_task(file_id: str, task_type: str) -> TaskStatus:
    """创建新任务"""
    task_id = generate_id()
    now = datetime.now().isoformat()
    task = TaskStatus(
        task_id=task_id,
        status="pending",
        progress=0,
        message=f"任务已创建: {task_type}",
        created_at=now,
        updated_at=now
    )
    tasks[task_id] = task
    return task

def update_task(task_id: str, status: str = None, progress: int = None,
                message: str = None, result: Dict = None):
    """更新任务状态"""
    if task_id not in tasks:
        return

    task = tasks[task_id]
    if status:
        task.status = status
    if progress is not None:
        task.progress = progress
    if message:
        task.message = message
    if result:
        task.result = result
    task.updated_at = datetime.now().isoformat()

def map_groups_to_prompt_groups(groups: List[str]) -> Optional[List[PromptGroup]]:
    """将字符串组名映射到 PromptGroup 枚举"""
    if not groups:
        return None

    group_map = {
        'image': PromptGroup.IMAGE,
        'arrow': PromptGroup.ARROW,
        'shape': PromptGroup.BASIC_SHAPE,
        'background': PromptGroup.BACKGROUND,
        'text': PromptGroup.TEXT,
        'icon': PromptGroup.ICON,
    }

    result = []
    for g in groups:
        if g in group_map:
            result.append(group_map[g])

    return result if result else None

async def run_segmentation_task(task_id: str, file_id: str, groups: Optional[List[str]] = None):
    """
    执行真实的分割任务

    使用 Pipeline.process_image() 处理图像:
    1. 可选的超分预处理
    2. 文本提取 (OCR)
    3. SAM3 分割
    4. 图标/图片处理
    5. 形状处理
    6. 箭头处理
    7. XML 合并
    """
    global _pipeline

    try:
        update_task(task_id, status="processing", progress=5, message="开始处理...")

        # 检查 pipeline
        if _pipeline is None:
            raise Exception("Pipeline 未初始化")

        # 获取文件路径
        meta_path = UPLOAD_DIR / f"{file_id}.json"
        with open(meta_path, "r") as f:
            metadata = json.load(f)

        image_path = metadata.get("path")
        if not image_path or not os.path.exists(image_path):
            raise Exception(f"文件不存在: {image_path}")

        update_task(task_id, progress=10, message="图像预处理...")

        # 解析分组参数
        prompt_groups = map_groups_to_prompt_groups(groups)

        update_task(task_id, progress=20, message="执行完整处理流程...")

        # 使用 Pipeline 处理图像
        # 注意：这里使用 asyncio.to_thread 将同步的 pipeline 调用转为异步
        loop = asyncio.get_event_loop()
        output_path = await loop.run_in_executor(
            None,
            lambda: _pipeline.process_image(
                image_path=image_path,
                output_dir=str(OUTPUT_DIR),
                with_refinement=False,  # API 模式下不使用 refinement
                with_text=True,
                groups=prompt_groups
            )
        )

        if output_path is None:
            raise Exception("处理失败，未生成输出文件")

        update_task(task_id, progress=80, message="处理完成，提取结果...")

        # 读取生成的元数据
        img_output_dir = OUTPUT_DIR / file_id

        # 尝试读取分割元数据
        elements = []
        sam3_meta_path = img_output_dir / "sam3_metadata.json"
        if sam3_meta_path.exists():
            try:
                with open(sam3_meta_path, "r") as f:
                    sam3_meta = json.load(f)
                    # 从元数据中提取元素信息
                    if "elements" in sam3_meta:
                        for elem in sam3_meta["elements"]:
                            elements.append({
                                "id": elem.get("id", "unknown"),
                                "type": elem.get("type", "unknown"),
                                "bbox": elem.get("bbox", {}),
                                "confidence": elem.get("confidence", 1.0),
                                "metadata": elem.get("metadata", {})
                            })
            except Exception as e:
                print(f"读取元数据失败: {e}")

        # 如果没有从元数据读取到元素，使用默认信息
        if not elements:
            elements = [{"message": "处理完成，元素详情请查看输出文件"}]

        # 获取输出文件信息
        output_file_size = 0
        if os.path.exists(output_path):
            output_file_size = os.path.getsize(output_path)

        # 检查可视化文件
        preview_url = None
        vis_path = img_output_dir / "sam3_extraction.png"
        if vis_path.exists():
            preview_url = f"/outputs/{file_id}/sam3_extraction.png"

        update_task(task_id,
                   status="completed",
                   progress=100,
                   message="分割完成",
                   result={
                       "file_id": file_id,
                       "segments_count": len(elements) if elements else 0,
                       "segments": elements,
                       "preview_url": preview_url,
                       "output_path": output_path,
                       "output_file_size": output_file_size,
                       "output_url": f"/outputs/{file_id}/{Path(output_path).name}" if output_path else None,
                   })

        print(f"✅ 分割任务完成: {task_id}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        update_task(task_id,
                   status="failed",
                   message=f"处理失败: {str(e)}",
                   result={"error": str(e)})
        print(f"❌ 分割任务失败: {task_id} - {e}")

async def run_convert_task(task_id: str, segment_task_id: str, output_format: str):
    """
    执行真实的转换任务

    将分割结果转换为指定格式
    """
    try:
        update_task(task_id, status="processing", progress=10, message="准备转换...")

        # 获取分割任务结果
        if segment_task_id not in tasks:
            raise Exception("分割任务未找到")

        segment_task = tasks[segment_task_id]
        if segment_task.status != "completed":
            raise Exception("分割任务尚未完成")

        result = segment_task.result
        file_id = result.get("file_id")

        update_task(task_id, progress=30, message="生成输出文件...")

        # 生成输出文件
        output_filename = f"{file_id}.{output_format}"
        output_path = OUTPUT_DIR / output_filename

        source_path = result.get("output_path")

        if source_path and os.path.exists(source_path):
            # 复制文件
            import shutil
            shutil.copy2(source_path, output_path)
        else:
            # 查找生成的文件
            img_output_dir = OUTPUT_DIR / file_id
            if img_output_dir.exists():
                for f in img_output_dir.glob(f"*.{output_format}"):
                    import shutil
                    shutil.copy2(f, output_path)
                    break

        if not output_path.exists():
            raise Exception(f"未找到 {output_format} 格式的输出文件")

        file_size = output_path.stat().st_size

        update_task(task_id,
                   status="completed",
                   progress=100,
                   message="转换完成",
                   result={
                       "download_url": f"/outputs/{output_filename}",
                       "file_size": file_size,
                       "format": output_format
                   })

        print(f"✅ 转换任务完成: {task_id}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        update_task(task_id,
                   status="failed",
                   message=f"转换失败: {str(e)}",
                   result={"error": str(e)})
        print(f"❌ 转换任务失败: {task_id} - {e}")

# ============================================
# API 路由
# ============================================

@app.get("/")
async def root():
    """根路径 - API 信息"""
    return {
        "name": "Edit-Banana API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "upload": "/api/v1/upload",
            "segment": "/api/v1/segment",
            "convert": "/api/v1/convert",
            "status": "/api/v1/status"
        }
    }

@app.get("/health")
async def health_check():
    """
    健康检查端点 (前端兼容)

    简单的健康检查，返回 200 OK
    """
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/v1/status", response_model=StatusResponse)
async def get_status():
    """
    健康检查与状态接口

    返回服务器状态、可用功能和模型加载情况
    """
    # 检查模型文件
    sam3_path = MODELS_DIR / "sam3_checkpoint.pth"
    flux_path = MODELS_DIR / "flux"

    # 检查 pipeline 状态
    pipeline_ready = _pipeline is not None

    # 检查 OCR 可用性
    ocr_available = False
    if _pipeline:
        try:
            ocr_available = _pipeline.text_restorer is not None
        except:
            pass

    return StatusResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        features={
            "upload": True,
            "segment": pipeline_ready,
            "convert_drawio": pipeline_ready,
            "convert_pptx": False,  # PPTX 暂未实现
            "batch_processing": False,
            "ocr": ocr_available
        },
        models={
            "sam3": sam3_path.exists(),
            "flux": flux_path.exists(),
            "pipeline_ready": pipeline_ready
        }
    )

@app.post("/api/v1/upload", response_model=UploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None)
):
    """
    文件上传接口

    接收图片或 PDF 文件，返回文件 ID 用于后续处理

    - **file**: 上传的文件 (jpg, png, pdf 等)
    - **description**: 可选的文件描述
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="未提供文件名")

    # 验证文件类型
    if not (is_valid_image(file.filename) or is_valid_pdf(file.filename)):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {get_file_extension(file.filename)}"
        )

    # 生成文件 ID
    file_id = generate_id()
    file_ext = get_file_extension(file.filename)
    safe_filename = f"{file_id}{file_ext}"
    file_path = UPLOAD_DIR / safe_filename

    try:
        # 保存文件
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        file_size = len(content)
        file_type = "image" if is_valid_image(file.filename) else "pdf"

        # 记录元数据
        metadata = {
            "file_id": file_id,
            "original_name": file.filename,
            "file_type": file_type,
            "file_size": file_size,
            "description": description,
            "uploaded_at": datetime.now().isoformat(),
            "path": str(file_path)
        }

        meta_path = UPLOAD_DIR / f"{file_id}.json"
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"📤 文件上传成功: {file.filename} -> {file_id} ({file_size} bytes)")

        return UploadResponse(
            success=True,
            message="文件上传成功",
            file_id=file_id,
            filename=file.filename,
            file_type=file_type,
            file_url=f"/uploads/{safe_filename}"
        )

    except Exception as e:
        print(f"❌ 文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

@app.post("/api/v1/segment", response_model=SegmentResponse)
async def segment_file(request: SegmentRequest):
    """
    图像分割接口

    对上传的图片进行 SAM3 分割，识别并分离图表元素

    - **file_id**: 上传文件时返回的 ID
    - **auto_segment**: 是否自动分割 (默认 True)
    - **prompt**: 可选的文本提示，用于指导分割
    - **groups**: 可选的分组列表 [image, arrow, shape, background]
    """
    # 检查文件是否存在
    meta_path = UPLOAD_DIR / f"{request.file_id}.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="文件未找到，请先上传")

    # 读取元数据
    with open(meta_path, "r") as f:
        metadata = json.load(f)

    if metadata.get("file_type") != "image":
        raise HTTPException(status_code=400, detail="只支持图片文件分割")

    # 检查 pipeline
    if _pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline 未初始化，无法处理分割请求")

    # 创建分割任务
    task = create_task(request.file_id, "segment")
    task_id = task.task_id

    # 启动真实的后台任务
    asyncio.create_task(run_segmentation_task(
        task_id,
        request.file_id,
        groups=request.groups
    ))

    print(f"🔍 分割任务创建: {task_id} for file {request.file_id}")

    return SegmentResponse(
        success=True,
        message="分割任务已启动",
        task_id=task_id,
        segments=[],
        preview_url=f"/uploads/{request.file_id}.png"
    )

@app.get("/api/v1/segment/{task_id}")
async def get_segment_status(task_id: str):
    """
    获取分割任务状态

    - **task_id**: 分割任务 ID
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务未找到")

    return tasks[task_id]

@app.post("/api/v1/convert", response_model=ConvertResponse)
async def convert_file(request: ConvertRequest):
    """
    文件转换接口

    将分割结果转换为 DrawIO 或 PPTX 格式

    - **task_id**: 分割任务 ID
    - **output_format**: 输出格式 (drawio 或 pptx)
    - **include_annotations**: 是否包含注释
    """
    # 验证任务
    if request.task_id not in tasks:
        raise HTTPException(status_code=404, detail="分割任务未找到")

    segment_task = tasks[request.task_id]
    if segment_task.status != "completed":
        raise HTTPException(status_code=400, detail="分割任务尚未完成")

    # 验证格式
    if request.output_format not in ["drawio", "pptx"]:
        raise HTTPException(status_code=400, detail="不支持的输出格式")

    if request.output_format == "pptx":
        raise HTTPException(status_code=501, detail="PPTX 格式暂未实现")

    # 创建转换任务
    convert_task = create_task(request.task_id, f"convert_{request.output_format}")
    convert_task_id = convert_task.task_id

    # 启动真实的转换任务
    asyncio.create_task(run_convert_task(
        convert_task_id,
        request.task_id,
        request.output_format
    ))

    print(f"🔄 转换任务创建: {convert_task_id} from {request.task_id}")

    # 返回临时响应
    return ConvertResponse(
        success=True,
        message=f"正在转换为 {request.output_format} 格式",
        download_url=None,
        file_size=None
    )

@app.get("/api/v1/convert/{task_id}")
async def get_convert_status(task_id: str):
    """
    获取转换任务状态

    - **task_id**: 转换任务 ID
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务未找到")

    return tasks[task_id]

@app.get("/api/v1/download/{filename}")
async def download_file(filename: str):
    """
    下载生成的文件

    - **filename**: 文件名
    """
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件未找到")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )

@app.get("/api/v1/tasks")
async def list_tasks():
    """
    列出所有任务 (调试用)
    """
    return {
        "tasks": [
            {
                "task_id": t.task_id,
                "status": t.status,
                "progress": t.progress,
                "created_at": t.created_at
            }
            for t in tasks.values()
        ]
    }

@app.delete("/api/v1/tasks/{task_id}")
async def delete_task(task_id: str):
    """
    删除任务

    - **task_id**: 任务 ID
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务未找到")

    del tasks[task_id]
    return {"success": True, "message": "任务已删除"}


# ============================================
# 预览功能路由
# ============================================

@app.get("/preview/drawio/{task_id}", response_class=HTMLResponse)
async def preview_drawio(request: Request, task_id: str):
    """
    DrawIO 在线预览和编辑

    - **task_id**: 转换任务 ID
    返回嵌入 DrawIO 编辑器的 HTML 页面
    """
    # 查找对应的 drawio 文件
    drawio_file = OUTPUT_DIR / f"{task_id}.drawio"

    # 如果没有找到具体任务文件，尝试列出所有 drawio 文件
    if not drawio_file.exists():
        drawio_files = list(OUTPUT_DIR.glob("*.drawio"))
        if drawio_files:
            drawio_file = drawio_files[0]
        else:
            # 返回空模板
            xml_content = '''<mxfile host="app.diagrams.net" modified="2024-01-01T00:00:00.000Z">
                <diagram name="Page-1" id="preview">
                    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
                        <root>
                            <mxCell id="0" />
                            <mxCell id="1" parent="0" />
                            <mxCell id="2" value="&lt;h1&gt;Edit-Banana&lt;/h1&gt;&lt;p&gt;No diagram file found yet.&lt;/p&gt;" style="text;html=1;strokeColor=none;fillColor=none;spacing=5;spacingTop=-20;whiteSpace=wrap;overflow=hidden;rounded=0;" vertex="1" parent="1">
                                <mxGeometry x="400" y="350" width="400" height="100" as="geometry" />
                            </mxCell>
                        </root>
                    </mxGraphModel>
                </diagram>
            </mxfile>'''
            return templates.TemplateResponse("drawio_preview.html", {
                "request": request,
                "task_id": task_id,
                "xml_content": xml_content.replace('"', '&quot;')
            })

    # 读取并编码 XML 内容
    try:
        with open(drawio_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取 DrawIO 文件失败: {str(e)}")

    return templates.TemplateResponse("drawio_preview.html", {
        "request": request,
        "task_id": task_id,
        "xml_content": xml_content.replace('"', '&quot;')
    })


@app.get("/preview/pptx/{task_id}", response_class=HTMLResponse)
async def preview_pptx(request: Request, task_id: str):
    """
    PPTX 在线预览

    - **task_id**: 转换任务 ID
    支持 Office Online 预览、Google Docs 预览或本地图片预览
    """
    pptx_file = OUTPUT_DIR / f"{task_id}.pptx"
    pdf_file = OUTPUT_DIR / f"{task_id}.pdf"

    # 收集幻灯片预览图
    slides = []
    slide_images_dir = OUTPUT_DIR / f"{task_id}_slides"

    if slide_images_dir.exists():
        for img_file in sorted(slide_images_dir.glob("slide_*.png")):
            slide_num = img_file.stem.replace("slide_", "")
            slides.append({
                "name": f"幻灯片 {slide_num}",
                "url": f"/outputs/{task_id}_slides/{img_file.name}"
            })

    if not slides:
        slides = [{"name": "幻灯片 1", "url": ""}]

    # 文件信息
    file_size = "未知"
    if pptx_file.exists():
        size_bytes = pptx_file.stat().st_size
        if size_bytes > 1024 * 1024:
            file_size = f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            file_size = f"{size_bytes / 1024:.2f} KB"

    file_url = f"{request.base_url}outputs/{task_id}.pptx"

    return templates.TemplateResponse("pptx_preview.html", {
        "request": request,
        "task_id": task_id,
        "filename": f"{task_id}.pptx",
        "file_size": file_size,
        "slide_count": len(slides),
        "slides": slides,
        "file_url": str(file_url),
        "use_office_online": False,
        "preview_images": len(slides) > 0 and slides[0]["url"] != ""
    })


@app.get("/preview/compare/{file_id}", response_class=HTMLResponse)
async def preview_compare(request: Request, file_id: str):
    """
    原始图片 vs 分割结果 对比视图

    - **file_id**: 上传的文件 ID
    支持滑块对比、并列显示、叠加显示三种模式
    """
    # 检查文件是否存在
    meta_path = UPLOAD_DIR / f"{file_id}.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="文件未找到")

    with open(meta_path, "r") as f:
        metadata = json.load(f)

    # 查找原始图片
    original_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
    original_url = None
    for ext in original_extensions:
        orig_file = UPLOAD_DIR / f"{file_id}{ext}"
        if orig_file.exists():
            original_url = f"/uploads/{file_id}{ext}"
            break

    if not original_url:
        original_url = "/static/banana.jpg"

    # 查找标注后的图片
    annotated_url = f"/outputs/{file_id}_annotated.png"
    annotated_file = OUTPUT_DIR / f"{file_id}_annotated.png"
    if not annotated_file.exists():
        annotated_url = original_url

    # 查找分割后的元素缩略图
    segments_dir = OUTPUT_DIR / f"{file_id}_segments"
    segments = []

    if segments_dir.exists():
        for seg_file in sorted(segments_dir.glob("segment_*.png")):
            seg_id = int(seg_file.stem.replace("segment_", ""))
            segments.append({
                "id": seg_id,
                "type": "element",
                "thumbnail_url": f"/outputs/{file_id}_segments/{seg_file.name}",
                "bbox": [0.1, 0.1, 0.3, 0.3]
            })

    if not segments:
        segments = [
            {"id": 1, "type": "图表", "thumbnail_url": annotated_url, "bbox": [0.2, 0.2, 0.6, 0.6]},
            {"id": 2, "type": "文本", "thumbnail_url": annotated_url, "bbox": [0.1, 0.1, 0.3, 0.2]},
            {"id": 3, "type": "标题", "thumbnail_url": annotated_url, "bbox": [0.3, 0.05, 0.7, 0.15]},
        ]

    task_id = None
    for tid, task in tasks.items():
        if task.result and task.result.get("file_id") == file_id:
            task_id = tid
            break

    if not task_id:
        task_id = file_id

    return templates.TemplateResponse("compare_view.html", {
        "request": request,
        "file_id": file_id,
        "task_id": task_id,
        "original_url": original_url,
        "annotated_url": annotated_url,
        "segments": segments
    })


@app.get("/api/v1/files")
async def list_files():
    """
    列出所有上传的文件和处理结果
    """
    files = []

    for meta_file in UPLOAD_DIR.glob("*.json"):
        try:
            with open(meta_file, "r") as f:
                metadata = json.load(f)

            file_id = metadata.get("file_id")

            has_drawio = (OUTPUT_DIR / f"{file_id}.drawio").exists()
            has_pptx = (OUTPUT_DIR / f"{file_id}.pptx").exists()
            has_pdf = (OUTPUT_DIR / f"{file_id}.pdf").exists()
            has_segments = (OUTPUT_DIR / f"{file_id}_segments").exists()

            file_tasks = []
            for tid, task in tasks.items():
                if task.result and task.result.get("file_id") == file_id:
                    file_tasks.append({
                        "task_id": tid,
                        "status": task.status,
                        "progress": task.progress
                    })

            files.append({
                "file_id": file_id,
                "filename": metadata.get("original_name", "Unknown"),
                "file_type": metadata.get("file_type", "unknown"),
                "file_size": metadata.get("file_size", 0),
                "uploaded_at": metadata.get("uploaded_at"),
                "description": metadata.get("description"),
                "status": {
                    "has_drawio": has_drawio,
                    "has_pptx": has_pptx,
                    "has_pdf": has_pdf,
                    "has_segments": has_segments
                },
                "tasks": file_tasks,
                "preview_urls": {
                    "compare": f"/preview/compare/{file_id}",
                    "drawio": f"/preview/drawio/{file_id}" if has_drawio else None,
                    "pptx": f"/preview/pptx/{file_id}" if has_pptx else None
                }
            })
        except Exception as e:
            print(f"读取元数据文件失败 {meta_file}: {e}")
            continue

    files.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)

    return {
        "success": True,
        "count": len(files),
        "files": files
    }


@app.delete("/api/v1/files/{file_id}")
async def delete_file(file_id: str):
    """
    删除上传的文件和关联结果
    """
    deleted_items = []

    for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.pdf']:
        file_path = UPLOAD_DIR / f"{file_id}{ext}"
        if file_path.exists():
            file_path.unlink()
            deleted_items.append(f"uploads/{file_id}{ext}")

    meta_path = UPLOAD_DIR / f"{file_id}.json"
    if meta_path.exists():
        meta_path.unlink()
        deleted_items.append(f"uploads/{file_id}.json")

    output_files = [
        f"{file_id}.drawio",
        f"{file_id}.pptx",
        f"{file_id}.pdf",
        f"{file_id}_annotated.png"
    ]
    for output_file in output_files:
        output_path = OUTPUT_DIR / output_file
        if output_path.exists():
            output_path.unlink()
            deleted_items.append(f"outputs/{output_file}")

    segments_dir = OUTPUT_DIR / f"{file_id}_segments"
    if segments_dir.exists():
        import shutil
        shutil.rmtree(segments_dir)
        deleted_items.append(f"outputs/{file_id}_segments/")

    slides_dir = OUTPUT_DIR / f"{file_id}_slides"
    if slides_dir.exists():
        import shutil
        shutil.rmtree(slides_dir)
        deleted_items.append(f"outputs/{file_id}_slides/")

    tasks_to_delete = []
    for tid, task in tasks.items():
        if task.result and task.result.get("file_id") == file_id:
            tasks_to_delete.append(tid)

    for tid in tasks_to_delete:
        del tasks[tid]
        deleted_items.append(f"task:{tid}")

    if not deleted_items:
        raise HTTPException(status_code=404, detail="文件未找到或已被删除")

    return {
        "success": True,
        "message": f"文件 {file_id} 及其关联资源已删除",
        "deleted_items": deleted_items
    }


# ============================================
# 主函数
# ============================================
if __name__ == "__main__":
    print("=" * 50)
    print("🍌 Edit-Banana Backend Server")
    print("=" * 50)
    print(f"🌐 服务地址: http://{APP_HOST}:{APP_PORT}")
    print(f"📖 API 文档: http://{APP_HOST}:{APP_PORT}/docs")
    print(f"🔧 调试模式: {APP_DEBUG}")
    print("=" * 50)

    uvicorn.run(
        "server_pa:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=APP_DEBUG,
        log_level=LOG_LEVEL.lower()
    )
