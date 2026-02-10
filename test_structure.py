#!/usr/bin/env python3
"""
Edit-Banana 基础结构测试
不依赖外部库，只验证代码结构和配置
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def test_structure():
    """测试项目结构"""
    print("=" * 60)
    print("项目结构测试")
    print("=" * 60)
    
    tests = []
    
    # 核心文件
    core_files = [
        'main.py', 'server_pa.py', 'streamlit_app.py',
        'requirements.txt', 'config/config.yaml'
    ]
    
    for f in core_files:
        path = os.path.join(PROJECT_ROOT, f)
        if os.path.exists(path):
            print(f"✅ {f}")
            tests.append((f, True, None))
        else:
            print(f"❌ {f} (缺失)")
            tests.append((f, False, "文件不存在"))
    
    return tests

def test_agent_teams():
    """测试 Agent Teams 文档"""
    print("\n" + "=" * 60)
    print("Agent Teams 文档测试")
    print("=" * 60)
    
    tests = []
    
    report_path = os.path.join(PROJECT_ROOT, 'AGENT_TEAMS_REPORT.md')
    if os.path.exists(report_path):
        size = os.path.getsize(report_path)
        print(f"✅ AGENT_TEAMS_REPORT.md ({size} bytes)")
        
        # 检查报告内容
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = [
            ('包含 Mermaid 图', 'flowchart' in content or 'mermaid' in content.lower()),
            ('包含 Pipeline 架构', 'Pipeline' in content),
            ('包含测试用例', '测试用例' in content or 'Test Case' in content),
            ('包含 Agent 定义', 'Agent' in content),
        ]
        
        for name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {name}")
            tests.append((name, passed, None))
        
        tests.append(("报告文件", True, None))
    else:
        print(f"❌ AGENT_TEAMS_REPORT.md 不存在")
        tests.append(("报告文件", False, "文件不存在"))
    
    return tests

def test_scripts():
    """测试启动脚本"""
    print("\n" + "=" * 60)
    print("启动脚本测试")
    print("=" * 60)
    
    tests = []
    
    scripts = ['start.sh', 'quick_test.py']
    
    for script in scripts:
        path = os.path.join(PROJECT_ROOT, script)
        if os.path.exists(path):
            executable = os.access(path, os.X_OK) if script.endswith('.sh') else True
            status = "✅" if executable else "⚠️"
            print(f"{status} {script}")
            tests.append((script, True, None if executable else "无执行权限"))
        else:
            print(f"❌ {script} (缺失)")
            tests.append((script, False, "文件不存在"))
    
    return tests

def print_summary(all_tests):
    """打印汇总"""
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in all_tests if success)
    total = len(all_tests)
    
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有基础结构测试通过!")
        print("\n下一步:")
        print("1. 安装依赖: pip install -r requirements.txt")
        print("2. 配置 API Keys: 编辑 .env 文件")
        print("3. 启动服务: ./start.sh")
        return 0
    else:
        print(f"⚠️ 有 {total - passed} 项需要关注")
        return 1

def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Edit-Banana 基础结构测试" + " " * 25 + "║")
    print("╚" + "=" * 58 + "╝")
    
    all_tests = []
    all_tests.extend(test_structure())
    all_tests.extend(test_agent_teams())
    all_tests.extend(test_scripts())
    
    return print_summary(all_tests)

if __name__ == "__main__":
    sys.exit(main())
