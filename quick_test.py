#!/usr/bin/env python3
"""
Edit-Banana 快速测试脚本
验证核心模块是否能正确导入和初始化
"""

import sys
import os

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("测试模块导入")
    print("=" * 60)
    
    tests = []
    
    # 1. 测试核心模块
    try:
        from modules import (
            Sam3InfoExtractor, IconPictureProcessor, BasicShapeProcessor,
            ArrowProcessor, XMLMerger, MetricEvaluator, RefinementProcessor,
            ProcessingContext, ProcessingResult, ElementInfo, LayerLevel, get_layer_level
        )
        print("✅ 核心模块导入成功")
        tests.append(("核心模块", True, None))
    except Exception as e:
        print(f"❌ 核心模块导入失败: {e}")
        tests.append(("核心模块", False, str(e)))
    
    # 2. 测试 Kimi 客户端
    try:
        from modules import KimiClient, get_client
        print("✅ Kimi 客户端导入成功")
        tests.append(("Kimi 客户端", True, None))
    except Exception as e:
        print(f"❌ Kimi 客户端导入失败: {e}")
        tests.append(("Kimi 客户端", False, str(e)))
    
    # 3. 测试数据类型
    try:
        from modules.data_types import ElementType, BoundingBox, Element
        print("✅ 数据类型导入成功")
        tests.append(("数据类型", True, None))
    except Exception as e:
        print(f"❌ 数据类型导入失败: {e}")
        tests.append(("数据类型", False, str(e)))
    
    # 4. 测试 main.py Pipeline
    try:
        from main import Pipeline, load_config
        print("✅ Pipeline 导入成功")
        tests.append(("Pipeline", True, None))
    except Exception as e:
        print(f"❌ Pipeline 导入失败: {e}")
        tests.append(("Pipeline", False, str(e)))
    
    # 5. 测试 server_pa.py
    try:
        import server_pa
        print("✅ Server 模块导入成功")
        tests.append(("Server 模块", True, None))
    except Exception as e:
        print(f"❌ Server 模块导入失败: {e}")
        tests.append(("Server 模块", False, str(e)))
    
    # 6. 测试 streamlit_app
    try:
        import streamlit_app
        print("✅ Streamlit App 导入成功")
        tests.append(("Streamlit App", True, None))
    except Exception as e:
        print(f"❌ Streamlit App 导入失败: {e}")
        tests.append(("Streamlit App", False, str(e)))
    
    return tests

def test_config():
    """测试配置文件"""
    print("\n" + "=" * 60)
    print("测试配置文件")
    print("=" * 60)
    
    tests = []
    
    # 检查 config.yaml
    config_path = os.path.join(PROJECT_ROOT, "config", "config.yaml")
    if os.path.exists(config_path):
        print(f"✅ 配置文件存在: {config_path}")
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"✅ 配置文件解析成功")
            tests.append(("配置文件", True, None))
        except Exception as e:
            print(f"⚠️ 配置文件解析警告: {e}")
            tests.append(("配置文件", True, str(e)))
    else:
        print(f"❌ 配置文件不存在: {config_path}")
        tests.append(("配置文件", False, "文件不存在"))
    
    # 检查 .env
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(env_path):
        print(f"✅ 环境文件存在: {env_path}")
        tests.append(("环境文件", True, None))
    else:
        print(f"⚠️ 环境文件不存在: {env_path}")
        tests.append(("环境文件", False, "文件不存在"))
    
    return tests

def test_directories():
    """测试必要目录"""
    print("\n" + "=" * 60)
    print("测试目录结构")
    print("=" * 60)
    
    tests = []
    required_dirs = ['uploads', 'outputs', 'input', 'models', 'logs']
    
    for dir_name in required_dirs:
        dir_path = os.path.join(PROJECT_ROOT, dir_name)
        if os.path.exists(dir_path):
            print(f"✅ 目录存在: {dir_name}/")
            tests.append((f"目录: {dir_name}", True, None))
        else:
            print(f"❌ 目录不存在: {dir_name}/")
            tests.append((f"目录: {dir_name}", False, "目录不存在"))
    
    return tests

def print_summary(all_tests):
    """打印测试汇总"""
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in all_tests if success)
    total = len(all_tests)
    
    for name, success, error in all_tests:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")
        if error:
            print(f"    错误: {error}")
    
    print("-" * 60)
    print(f"总计: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过! 项目可以正常运行。")
        return 0
    else:
        print(f"⚠️ 有 {total - passed} 项测试失败，请检查配置。")
        return 1

def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "Edit-Banana 快速测试脚本" + " " * 23 + "║")
    print("╚" + "=" * 58 + "╝")
    
    all_tests = []
    
    try:
        all_tests.extend(test_imports())
    except Exception as e:
        print(f"导入测试异常: {e}")
    
    try:
        all_tests.extend(test_config())
    except Exception as e:
        print(f"配置测试异常: {e}")
    
    try:
        all_tests.extend(test_directories())
    except Exception as e:
        print(f"目录测试异常: {e}")
    
    return print_summary(all_tests)

if __name__ == "__main__":
    sys.exit(main())
