"""
Arrow Prompt Template
箭头相关的提示词模板
"""

ARROW_DETECTION_PROMPT = """
你是一个专业的图表分析助手。请识别图像中的所有箭头，并提供以下信息：
1. 箭头的起点和终点坐标
2. 箭头的方向（上、下、左、右、斜向等）
3. 箭头的类型（实线、虚线、带箭头的连接线等）
4. 箭头连接的元素（如果有）

输出格式要求：
- 使用 JSON 格式
- 包含每个箭头的详细信息
- 坐标使用 (x, y) 格式，原点在左上角
- 方向使用标准方向描述

示例：
{
  "arrows": [
    {
      "id": "arrow_001",
      "start": [120, 85],
      "end": [240, 185],
      "direction": "down-right",
      "type": "solid_line_with_arrow",
      "connected_to": ["element_001", "element_002"]
    }
  ]
}
"""

ARROW_CLASSIFICATION_PROMPT = """
请对检测到的箭头进行分类：
- 功能性箭头：表示流程、步骤、数据流向
- 装饰性箭头：仅用于视觉装饰
- 关系箭头：表示元素之间的关系（如包含、依赖等）

根据箭头的上下文和位置判断其功能类型。
"""

ARROW_REFINEMENT_PROMPT = """
请精化箭头检测结果：
1. 修正不准确的起点/终点坐标
2. 合并重复检测的箭头
3. 补充缺失的箭头（特别是连接关键元素的箭头）
4. 验证箭头方向的准确性

重点关注箭头与图表其他元素的连接关系。
"""

# 针对不同场景的提示词
SCENE_PROMPTS = {
    "flowchart": ARROW_DETECTION_PROMPT + "\n\n特别关注流程图中的步骤连接箭头。",
    "architecture": ARROW_DETECTION_PROMPT + "\n\n特别关注系统架构图中的数据流向和依赖关系。",
    "mindmap": ARROW_DETECTION_PROMPT + "\n\n特别关注思维导图中的概念关联箭头。",
    "diagram": ARROW_DETECTION_PROMPT + "\n\n通用图表箭头检测。"
}
