"""
Image Prompt Template
图片相关的提示词模板
"""

IMAGE_DETECTION_PROMPT = """
你是一个专业的图像分析助手。请识别图像中的所有图片区域，并提供以下信息：
1. 图片区域的边界框坐标
2. 图片类型（照片、截图、图标、图表等）
3. 图片内容描述
4. 图片与周围元素的关系

输出格式要求：
- 使用 JSON 格式
- 包含每个图片区域的详细信息
- 坐标使用 (x, y, width, height) 格式
- 图片类型使用标准分类

示例：
{
  "images": [
    {
      "id": "image_001",
      "bbox": [100, 50, 300, 200],
      "type": "photograph",
      "description": "产品照片，显示设备正面",
      "relation_to_elements": ["element_001", "element_002"]
    }
  ]
}
"""

IMAGE_CLASSIFICATION_PROMPT = """
请对检测到的图片进行分类：
- 照片：真实拍摄的照片
- 截图：屏幕截图
- 图标：小尺寸图标
- 图表：数据图表
- 插图：手绘或矢量插图
- 其他：其他类型

根据图片的内容和特征判断其类型。
"""

IMAGE_REFINEMENT_PROMPT = """
请精化图片检测结果：
1. 修正不准确的图片边界
2. 合并重复检测的图片区域
3. 补充缺失的图片（特别是嵌入在文本中的小图片）
4. 验证图片类型的准确性

重点关注图片与文本和其他元素的布局关系。
"""

# 针对不同场景的提示词
SCENE_PROMPTS = {
    "report": IMAGE_DETECTION_PROMPT + "\n\n特别关注报告中的插图和数据图表。",
    "presentation": IMAGE_DETECTION_PROMPT + "\n\n特别关注演示文稿中的图片和截图。",
    "website": IMAGE_DETECTION_PROMPT + "\n\n特别关注网页截图中的图片元素。",
    "general": IMAGE_DETECTION_PROMPT + "\n\n通用图片检测。"
}
