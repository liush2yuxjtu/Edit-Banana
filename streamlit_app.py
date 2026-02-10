#!/usr/bin/env python3
"""
Edit-Banana Streamlit Web Application
图片/PDF 分割与转换服务的友好用户界面
"""

import os
import sys
import time
import base64
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

import streamlit as st

# ============================================
# 页面配置
# ============================================
st.set_page_config(
    page_title="Edit-Banana 🍌",
    page_icon="🍌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# 常量配置
# ============================================
BASE_DIR = Path(__file__).parent.absolute()
ENV_FILE = BASE_DIR / ".env"
BACKEND_URL = "http://localhost:8000"
SUPPORTED_IMAGE_TYPES = ["jpg", "jpeg", "png", "gif", "bmp", "webp"]
SUPPORTED_PDF_TYPE = "pdf"

# ============================================
# 样式定制
# ============================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF6B35;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .status-pending {
        background-color: #FFF3CD;
        border-left: 4px solid #FFC107;
    }
    .status-processing {
        background-color: #CCE5FF;
        border-left: 4px solid #007BFF;
    }
    .status-completed {
        background-color: #D4EDDA;
        border-left: 4px solid #28A745;
    }
    .status-failed {
        background-color: #F8D7DA;
        border-left: 4px solid #DC3545;
    }
    .api-key-input {
        font-family: monospace;
    }
    .stProgress > div > div {
        background-color: #FF6B35;
    }
    .download-btn {
        background-color: #28A745;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.3rem;
        text-decoration: none;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# 环境变量管理
# ============================================
def load_env_file() -> Dict[str, str]:
    """加载 .env 文件内容"""
    env_vars = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

def save_env_file(env_vars: Dict[str, str]) -> bool:
    """保存环境变量到 .env 文件"""
    try:
        # 读取现有文件保留注释
        existing_lines = []
        if ENV_FILE.exists():
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()
        
        # 构建新的文件内容
        new_lines = []
        updated_keys = set()
        
        # 先处理现有行
        for line in existing_lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key = stripped.split("=", 1)[0].strip()
                if key in env_vars:
                    new_lines.append(f"{key}={env_vars[key]}\n")
                    updated_keys.add(key)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # 添加新变量
        for key, value in env_vars.items():
            if key not in updated_keys:
                new_lines.append(f"{key}={value}\n")
        
        # 写入文件
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        
        return True
    except Exception as e:
        st.error(f"保存 .env 文件失败: {e}")
        return False

def load_example_config() -> Dict[str, str]:
    """加载示例配置"""
    return {
        "AZURE_OPENAI_KEY": "sk-example-azure-key-123456789",
        "MISTRAL_API_KEY": "sk-example-mistral-key-987654321",
        "OPENAI_API_KEY": "sk-example-openai-key-abcdef123",
        "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com/",
        "AZURE_OPENAI_API_VERSION": "2024-02-01",
        "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
        "MISTRAL_MODEL": "mistral-large-latest",
        "OPENAI_MODEL": "gpt-4",
    }

# ============================================
# API 调用函数
# ============================================
def check_backend_status() -> Dict[str, Any]:
    """检查后端服务状态"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/status", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"status": "error", "message": f"HTTP {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"status": "offline", "message": "无法连接到后端服务"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def upload_file(file_data, filename: str) -> Dict[str, Any]:
    """上传文件到后端"""
    try:
        files = {"file": (filename, file_data, "application/octet-stream")}
        response = requests.post(f"{BACKEND_URL}/api/v1/upload", files=files, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "message": f"上传失败: HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "message": f"上传出错: {str(e)}"}

def start_segmentation(file_id: str, auto_segment: bool = True, prompt: str = None) -> Dict[str, Any]:
    """启动分割任务"""
    try:
        payload = {
            "file_id": file_id,
            "auto_segment": auto_segment
        }
        if prompt:
            payload["prompt"] = prompt
        
        response = requests.post(f"{BACKEND_URL}/api/v1/segment", json=payload, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "message": f"启动分割失败: HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "message": f"启动分割出错: {str(e)}"}

def get_segment_status(task_id: str) -> Dict[str, Any]:
    """获取分割任务状态"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/segment/{task_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def start_conversion(task_id: str, output_format: str, include_annotations: bool = True) -> Dict[str, Any]:
    """启动转换任务"""
    try:
        payload = {
            "task_id": task_id,
            "output_format": output_format,
            "include_annotations": include_annotations
        }
        response = requests.post(f"{BACKEND_URL}/api/v1/convert", json=payload, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "message": f"启动转换失败: HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "message": f"启动转换出错: {str(e)}"}

def get_convert_status(task_id: str) -> Dict[str, Any]:
    """获取转换任务状态"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/convert/{task_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ============================================
# 侧边栏 - API 配置
# ============================================
def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.markdown("## 🔧 API 配置")
        st.markdown("---")
        
        # 加载现有配置
        env_vars = load_env_file()
        
        # 后端状态检查
        st.markdown("### 后端状态")
        backend_status = check_backend_status()
        if backend_status.get("status") == "healthy":
            st.success("✅ 后端服务运行中")
            features = backend_status.get("features", {})
            models = backend_status.get("models", {})
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**功能**")
                for feat, enabled in features.items():
                    icon = "✅" if enabled else "❌"
                    st.markdown(f"{icon} {feat}")
            with col2:
                st.markdown("**模型**")
                for model, loaded in models.items():
                    icon = "✅" if loaded else "⚠️"
                    st.markdown(f"{icon} {model}")
        else:
            st.error(f"❌ 后端未连接: {backend_status.get('message', '未知错误')}")
            st.info("请确保后端服务已启动: `python server_pa.py`")
        
        st.markdown("---")
        
        # API Key 输入
        st.markdown("### API Keys")
        
        azure_key = st.text_input(
            "🔷 Azure OpenAI Key",
            value=env_vars.get("AZURE_OPENAI_KEY", ""),
            type="password",
            help="Azure OpenAI 服务的 API Key",
            key="azure_key"
        )
        
        mistral_key = st.text_input(
            "🟣 Mistral API Key",
            value=env_vars.get("MISTRAL_API_KEY", ""),
            type="password",
            help="Mistral AI 服务的 API Key",
            key="mistral_key"
        )
        
        openai_key = st.text_input(
            "🟢 OpenAI API Key",
            value=env_vars.get("OPENAI_API_KEY", ""),
            type="password",
            help="OpenAI 直接 API Key（可选）",
            key="openai_key"
        )
        
        # 高级配置展开
        with st.expander("🔧 高级配置"):
            azure_endpoint = st.text_input(
                "Azure Endpoint",
                value=env_vars.get("AZURE_OPENAI_ENDPOINT", "https://your-resource.openai.azure.com/"),
                key="azure_endpoint"
            )
            azure_version = st.text_input(
                "API Version",
                value=env_vars.get("AZURE_OPENAI_API_VERSION", "2024-02-01"),
                key="azure_version"
            )
            azure_deployment = st.text_input(
                "Deployment Name",
                value=env_vars.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"),
                key="azure_deployment"
            )
        
        st.markdown("---")
        
        # 按钮区域
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 保存配置", type="primary", use_container_width=True):
                new_env = {
                    "AZURE_OPENAI_KEY": azure_key,
                    "MISTRAL_API_KEY": mistral_key,
                    "OPENAI_API_KEY": openai_key,
                    "AZURE_OPENAI_ENDPOINT": azure_endpoint,
                    "AZURE_OPENAI_API_VERSION": azure_version,
                    "AZURE_OPENAI_DEPLOYMENT_NAME": azure_deployment,
                }
                if save_env_file(new_env):
                    st.success("✅ 配置已保存")
                else:
                    st.error("❌ 保存失败")
        
        with col2:
            if st.button("📋 加载示例", use_container_width=True):
                example = load_example_config()
                st.session_state["azure_key"] = example["AZURE_OPENAI_KEY"]
                st.session_state["mistral_key"] = example["MISTRAL_API_KEY"]
                st.session_state["openai_key"] = example["OPENAI_API_KEY"]
                st.session_state["azure_endpoint"] = example["AZURE_OPENAI_ENDPOINT"]
                st.session_state["azure_version"] = example["AZURE_OPENAI_API_VERSION"]
                st.session_state["azure_deployment"] = example["AZURE_OPENAI_DEPLOYMENT_NAME"]
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📚 关于")
        st.markdown("**Edit-Banana** v1.0")
        st.markdown("图片/PDF 分割与转换工具")
        st.markdown("[文档](http://localhost:8000/docs) | [GitHub](https://github.com)")

# ============================================
# 主页面 - 文件上传
# ============================================
def render_upload_section():
    """渲染文件上传区域"""
    st.markdown("## 📤 文件上传")
    
    uploaded_file = st.file_uploader(
        "拖拽文件到此处或点击上传",
        type=SUPPORTED_IMAGE_TYPES + [SUPPORTED_PDF_TYPE],
        accept_multiple_files=False,
        help="支持图片格式: JPG, PNG, GIF, BMP, WebP 或 PDF"
    )
    
    if uploaded_file is not None:
        # 显示文件信息
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**文件名:** {uploaded_file.name}")
        with col2:
            st.markdown(f"**大小:** {uploaded_file.size / 1024:.1f} KB")
        with col3:
            file_type = "图片" if uploaded_file.type.startswith("image") else "PDF"
            st.markdown(f"**类型:** {file_type}")
        
        # 图片预览
        if uploaded_file.type.startswith("image"):
            st.image(uploaded_file, caption="预览", use_container_width=True)
        elif uploaded_file.type == "application/pdf":
            st.info("📄 PDF 文件已上传（暂不支持预览）")
        
        return uploaded_file
    
    return None

# ============================================
# 主页面 - 处理选项
# ============================================
def render_processing_options():
    """渲染处理选项"""
    st.markdown("## ⚙️ 处理选项")
    
    col1, col2 = st.columns(2)
    
    with col1:
        output_format = st.selectbox(
            "输出格式",
            options=["drawio", "pptx"],
            format_func=lambda x: "Draw.io (XML)" if x == "drawio" else "PowerPoint (PPTX)",
            help="选择输出文件格式"
        )
        
        auto_segment = st.checkbox(
            "自动分割",
            value=True,
            help="自动识别并分割图表元素"
        )
    
    with col2:
        include_annotations = st.checkbox(
            "包含注释",
            value=True,
            help="在输出中包含分割标注"
        )
        
        prompt = st.text_area(
            "分割提示词（可选）",
            placeholder="例如: 分割图表中的柱状图和折线图",
            help="提供文本提示指导分割过程"
        )
    
    return {
        "output_format": output_format,
        "auto_segment": auto_segment,
        "include_annotations": include_annotations,
        "prompt": prompt if prompt else None
    }

# ============================================
# 主页面 - 进度显示
# ============================================
def render_progress(task_type: str, task_id: str, progress: int, message: str, status: str):
    """渲染进度显示"""
    status_class = {
        "pending": "status-pending",
        "processing": "status-processing",
        "completed": "status-completed",
        "failed": "status-failed"
    }.get(status, "status-pending")
    
    status_icon = {
        "pending": "⏳",
        "processing": "🔄",
        "completed": "✅",
        "failed": "❌"
    }.get(status, "⏳")
    
    st.markdown(f"""
    <div class="status-box {status_class}">
        <strong>{status_icon} {task_type}</strong><br>
        <small>任务ID: {task_id}</small><br>
        {message}
    </div>
    """, unsafe_allow_html=True)
    
    st.progress(progress / 100, text=f"{progress}%")

# ============================================
# 主页面 - 结果展示
# ============================================
def render_results(result: Dict[str, Any], output_format: str):
    """渲染处理结果"""
    st.markdown("---")
    st.markdown("## ✅ 处理结果")
    
    if result.get("status") == "completed":
        result_data = result.get("result", {})
        
        # 显示分割信息
        if "segments_count" in result_data:
            st.success(f"🎯 成功分割 {result_data['segments_count']} 个元素")
        
        # 显示分割详情
        if "segments" in result_data:
            st.markdown("### 📊 分割详情")
            for seg in result_data["segments"]:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**ID:** {seg.get('id', 'N/A')}")
                with col2:
                    st.markdown(f"**类型:** {seg.get('type', 'unknown')}")
                with col3:
                    bbox = seg.get('bbox', [])
                    if bbox:
                        st.markdown(f"**位置:** [{bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}]")
        
        # 显示预览
        if "preview_url" in result_data:
            preview_url = f"{BACKEND_URL}{result_data['preview_url']}"
            st.markdown("### 👁️ 预览")
            st.image(preview_url, use_container_width=True)
        
        # 下载链接
        if "download_url" in result_data:
            download_url = f"{BACKEND_URL}{result_data['download_url']}"
            filename = result_data['download_url'].split('/')[-1]
            file_size = result_data.get('file_size', 0)
            
            st.markdown("### 📥 下载")
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**文件名:** {filename}")
                if file_size:
                    st.markdown(f"**大小:** {file_size / 1024:.1f} KB")
            with col2:
                st.markdown(f"<a href='{download_url}' class='download-btn' target='_blank'>⬇️ 下载文件</a>", 
                          unsafe_allow_html=True)
    else:
        st.error("处理失败或未完成")

# ============================================
# 主处理流程
# ============================================
def process_file(uploaded_file, options: Dict[str, Any]):
    """处理文件的完整流程"""
    
    # 创建进度容器
    progress_container = st.container()
    
    with progress_container:
        # 步骤 1: 上传文件
        st.markdown("### 步骤 1/4: 上传文件")
        file_bytes = uploaded_file.getvalue()
        
        with st.spinner("正在上传..."):
            upload_result = upload_file(file_bytes, uploaded_file.name)
        
        if not upload_result.get("success"):
            st.error(f"上传失败: {upload_result.get('message', '未知错误')}")
            return
        
        file_id = upload_result.get("file_id")
        st.success(f"✅ 文件上传成功! ID: {file_id}")
        
        # 步骤 2: 启动分割
        st.markdown("### 步骤 2/4: 图像分割")
        
        with st.spinner("启动分割任务..."):
            segment_result = start_segmentation(
                file_id,
                auto_segment=options["auto_segment"],
                prompt=options["prompt"]
            )
        
        if not segment_result.get("success"):
            st.error(f"分割启动失败: {segment_result.get('message', '未知错误')}")
            return
        
        segment_task_id = segment_result.get("task_id")
        st.info(f"🔄 分割任务已启动: {segment_task_id}")
        
        # 步骤 3: 轮询分割状态
        segment_placeholder = st.empty()
        segment_progress = st.progress(0)
        
        max_retries = 60  # 最多等待 60 * 2 = 120 秒
        retry_count = 0
        
        while retry_count < max_retries:
            status = get_segment_status(segment_task_id)
            current_status = status.get("status", "unknown")
            current_progress = status.get("progress", 0)
            current_message = status.get("message", "处理中...")
            
            with segment_placeholder:
                render_progress("分割任务", segment_task_id, current_progress, 
                              current_message, current_status)
            
            segment_progress.progress(current_progress / 100, text=f"{current_progress}%")
            
            if current_status == "completed":
                st.success("✅ 分割完成!")
                break
            elif current_status == "failed":
                st.error(f"❌ 分割失败: {current_message}")
                return
            
            time.sleep(2)
            retry_count += 1
        
        if retry_count >= max_retries:
            st.error("⏱️ 分割任务超时")
            return
        
        # 步骤 4: 启动转换
        st.markdown("### 步骤 3/4: 格式转换")
        
        with st.spinner("启动转换任务..."):
            convert_result = start_conversion(
                segment_task_id,
                options["output_format"],
                include_annotations=options["include_annotations"]
            )
        
        if not convert_result.get("success"):
            st.error(f"转换启动失败: {convert_result.get('message', '未知错误')}")
            return
        
        convert_task_id = convert_result.get("task_id")
        st.info(f"🔄 转换任务已启动: {convert_task_id}")
        
        # 轮询转换状态
        convert_placeholder = st.empty()
        convert_progress = st.progress(0)
        
        retry_count = 0
        
        while retry_count < max_retries:
            status = get_convert_status(convert_task_id)
            current_status = status.get("status", "unknown")
            current_progress = status.get("progress", 0)
            current_message = status.get("message", "处理中...")
            
            with convert_placeholder:
                render_progress("转换任务", convert_task_id, current_progress,
                              current_message, current_status)
            
            convert_progress.progress(current_progress / 100, text=f"{current_progress}%")
            
            if current_status == "completed":
                st.success("✅ 转换完成!")
                render_results(status, options["output_format"])
                break
            elif current_status == "failed":
                st.error(f"❌ 转换失败: {current_message}")
                return
            
            time.sleep(2)
            retry_count += 1
        
        if retry_count >= max_retries:
            st.error("⏱️ 转换任务超时")
            return

# ============================================
# 主函数
# ============================================
def main():
    """主应用入口"""
    
    # 渲染侧边栏
    render_sidebar()
    
    # 主页面标题
    st.markdown('<div class="main-header">🍌 Edit-Banana</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">智能图片/PDF 分割与转换工具</div>', unsafe_allow_html=True)
    
    # 文件上传
    uploaded_file = render_upload_section()
    
    if uploaded_file is not None:
        st.markdown("---")
        
        # 处理选项
        options = render_processing_options()
        
        st.markdown("---")
        
        # 开始处理按钮
        if st.button("🚀 开始处理", type="primary", use_container_width=True):
            process_file(uploaded_file, options)
    else:
        # 显示提示信息
        st.info("👆 请先上传图片或 PDF 文件开始处理")
        
        # 显示功能介绍
        st.markdown("---")
        st.markdown("## ✨ 功能特性")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 📤 文件上传")
            st.markdown("- 支持多种图片格式")
            st.markdown("- PDF 文档导入")
            st.markdown("- 拖拽上传")
        
        with col2:
            st.markdown("### 🔍 智能分割")
            st.markdown("- SAM3 模型分割")
            st.markdown("- 自动识别图表")
            st.markdown("- 文本提示引导")
        
        with col3:
            st.markdown("### 🔄 格式转换")
            st.markdown("- Draw.io (XML)")
            st.markdown("- PowerPoint (PPTX)")
            st.markdown("- 可编辑矢量图")

# ============================================
# 应用入口
# ============================================
if __name__ == "__main__":
    main()