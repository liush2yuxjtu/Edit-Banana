"""
Shape Prompt Template
形状相关的提示词模板
"""

SHAPE_DETECTION_PROMPT = """
你是一个专业的图表分析助手。请识别图像中的所有基本形状，并提供以下信息：
1. 形状的边界框坐标
2. 形状类型（矩形、圆形、椭圆、三角形等）
3. 形状属性（填充颜色、边框颜色、线宽等）
4. 形状与周围元素的关系

输出格式要求：
- 使用 JSON 格式
- 包含每个形状的详细信息
- 坐标使用 (x, y, width, height) 格式
- 形状类型使用标准分类

示例：
{
  "shapes": [
    {
      "id": "shape_001",
      "bbox": [50, 30, 120, 80],
      "type": "rectangle",
      "properties": {
        "fill_color": "#ffffff",
        "border_color": "#000000",
        "border_width": 1
      },
      "relation_to_elements": ["element_001"]
    }
  ]
}
"""

SHAPE_CLASSIFICATION_PROMPT = """
请对检测到的形状进行分类：
- 矩形：包括正方形
- 圆形：完美的圆形
- 椭圆：椭圆形
- 三角形：三边形
- 多边形：四边及以上
- 其他：不规则形状

根据形状的几何特征判断其类型。
"""

SHAPE_REFINEMENT_PROMPT = """
请精化形状检测结果：
1. 修正不准确的形状边界
2. 合并重复检测的形状
3. 补充缺失的形状（特别是小尺寸形状）
4. 验证形状类型的准确性

重点关注形状的几何特征和与其他元素的相对位置。
"""

# 针对不同场景的提示词
SCENE_PROMPTS = {
    "flowchart": SHAPE_DETECTION_PROMPT + "\n\n特别关注流程图中的处理框、决策框等。",
    "architecture": SHAPE_DETECTION_PROMPT + "\n\n特别关注系统架构图中的组件形状。",
    "mindmap": SHAPE_DETECTION_PROMPT + "\n\n特别关注思维导图中的节点形状。",
    "general": SHAPE_DETECTION_PROMPT + "\n\n通用形状检测。"
}
