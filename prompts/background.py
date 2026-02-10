"""
Background Prompt Template
背景相关的提示词模板
"""

BACKGROUND_DETECTION_PROMPT = """
你是一个专业的图像分析助手。请识别图像中的背景区域，并提供以下信息：
1. 背景区域的边界框坐标
2. 背景类型（纯色、渐变、图案、图片等）
3. 背景颜色或主要特征
4. 背景与前景元素的关系

输出格式要求：
- 使用 JSON 格式
- 包含背景区域的详细信息
- 坐标使用 (x, y, width, height) 格式
- 背景类型使用标准分类

示例：
{
  "background": {
    "bbox": [0, 0, 800, 600],
    "type": "solid_color",
    "color": "#f5f5f5",
    "features": ["light_gray", "uniform"],
    "relation_to_foreground": "behind_all_elements"
  }
}
"""

BACKGROUND_CLASSIFICATION_PROMPT = """
请对检测到的背景进行分类：
- 纯色背景：单一颜色
- 渐变背景：颜色渐变
- 图案背景：重复图案
- 图片背景：使用图片作为背景
- 透明背景：无背景或透明

根据背景的视觉特征判断其类型。
"""

BACKGROUND_REFINEMENT_PROMPT = """
请精化背景检测结果：
1. 修正不准确的背景边界
2. 区分主背景和次要背景区域
3. 识别背景中的特殊元素（如水印、装饰等）
4. 验证背景与前景的分离准确性

重点关注背景区域的完整性和一致性。
"""

# 针对不同场景的提示词
SCENE_PROMPTS = {
    "presentation": BACKGROUND_DETECTION_PROMPT + "\n\n特别关注演示文稿的背景设计。",
    "document": BACKGROUND_DETECTION_PROMPT + "\n\n特别关注文档页面的背景特征。",
    "dashboard": BACKGROUND_DETECTION_PROMPT + "\n\n特别关注数据仪表板的背景布局。",
    "general": BACKGROUND_DETECTION_PROMPT + "\n\n通用背景检测。"
}
