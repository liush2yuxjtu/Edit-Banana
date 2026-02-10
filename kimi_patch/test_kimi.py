"""
Kimi API 测试脚本

测试 KimiClient 的各项功能
"""

import os
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from kimi_client import KimiClient, OpenAICompatibleClient


def test_basic_connection():
    """测试基本连接"""
    print("=" * 60)
    print("测试 1: 基本连接")
    print("=" * 60)
    
    try:
        client = KimiClient()
        health = client.health_check()
        
        if health["status"] == "healthy":
            print(f"✅ API 连接正常")
            print(f"   模型: {health['model']}")
            print(f"   Base URL: {health['base_url']}")
        else:
            print(f"❌ API 连接失败: {health.get('error', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    print()
    return True


def test_text_completion():
    """测试文本补全"""
    print("=" * 60)
    print("测试 2: 文本补全")
    print("=" * 60)
    
    try:
        client = KimiClient()
        
        prompts = [
            "你好，请用一句话介绍自己",
            "1 + 1 = ?",
            "Python 是什么编程语言？"
        ]
        
        for i, prompt in enumerate(prompts, 1):
            print(f"\n提示 {i}: {prompt}")
            response = client.complete(prompt, max_tokens=100)
            print(f"回复: {response[:100]}...")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    print("\n✅ 文本补全测试通过")
    print()
    return True


def test_multi_turn_chat():
    """测试多轮对话"""
    print("=" * 60)
    print("测试 3: 多轮对话")
    print("=" * 60)
    
    try:
        client = KimiClient()
        
        messages = [
            {"role": "user", "content": "你好，我叫小明"},
        ]
        
        print("用户: 你好，我叫小明")
        response1 = client.chat(messages, max_tokens=100)
        print(f"助手: {response1[:100]}...")
        
        messages.append({"role": "assistant", "content": response1})
        messages.append({"role": "user", "content": "我叫什么名字？"})
        
        print("\n用户: 我叫什么名字？")
        response2 = client.chat(messages, max_tokens=100)
        print(f"助手: {response2[:100]}...")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    print("\n✅ 多轮对话测试通过")
    print()
    return True


def test_system_prompt():
    """测试系统提示"""
    print("=" * 60)
    print("测试 4: 系统提示")
    print("=" * 60)
    
    try:
        client = KimiClient()
        
        system = "你是一个专业的 Python 程序员，回答要简洁专业。"
        messages = [{"role": "user", "content": "什么是列表推导式？"}]
        
        print(f"系统提示: {system}")
        print(f"用户: 什么是列表推导式？")
        
        response = client.chat(messages, system=system, max_tokens=150)
        print(f"助手: {response[:150]}...")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    print("\n✅ 系统提示测试通过")
    print()
    return True


def test_streaming():
    """测试流式输出"""
    print("=" * 60)
    print("测试 5: 流式输出")
    print("=" * 60)
    
    try:
        client = KimiClient()
        
        messages = [{"role": "user", "content": "写一首短诗"}]
        
        print("用户: 写一首短诗")
        print("助手: ", end="", flush=True)
        
        full_response = ""
        for chunk in client.chat_stream(messages, max_tokens=200):
            print(chunk, end="", flush=True)
            full_response += chunk
        
        print()  # 换行
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return False
    
    print("\n✅ 流式输出测试通过")
    print()
    return True


def test_openai_compatible():
    """测试 OpenAI 兼容模式"""
    print("=" * 60)
    print("测试 6: OpenAI 兼容模式")
    print("=" * 60)
    
    try:
        client = OpenAICompatibleClient()
        
        messages = [{"role": "user", "content": "Hello"}]
        
        response = client.create_completion(
            model="gpt-4",
            messages=messages,
            max_tokens=50
        )
        
        print(f"模型: {response['model']}")
        print(f"回复: {response['choices'][0]['message']['content'][:100]}...")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    print("\n✅ OpenAI 兼容模式测试通过")
    print()
    return True


def test_patches():
    """测试补丁模块"""
    print("=" * 60)
    print("测试 7: 补丁模块")
    print("=" * 60)
    
    try:
        # 测试 OpenAI 补丁
        from patches.openai_patch import OpenAI, patch_openai
        
        print("\n测试 OpenAI 补丁...")
        client = OpenAI(api_key="dummy")
        
        messages = [{"role": "user", "content": "Hi"}]
        response = client.chat.create(model="gpt-4", messages=messages, max_tokens=50)
        print(f"✅ OpenAI 补丁工作正常")
        print(f"   回复: {response.choices[0].message.content[:50]}...")
        
        # 测试 Azure 补丁
        from patches.azure_patch import AzureOpenAI
        
        print("\n测试 Azure OpenAI 补丁...")
        azure_client = AzureOpenAI(
            api_key="dummy",
            api_version="2024-02-01",
            azure_endpoint="https://dummy.openai.azure.com/"
        )
        response = azure_client.chat.create(model="gpt-4", messages=messages, max_tokens=50)
        print(f"✅ Azure OpenAI 补丁工作正常")
        print(f"   回复: {response.choices[0].message.content[:50]}...")
        
        # 测试 Mistral 补丁
        from patches.mistral_patch import MistralClient
        
        print("\n测试 Mistral 补丁...")
        mistral_client = MistralClient(api_key="dummy")
        response = mistral_client.chat(model="mistral-large-latest", messages=messages)
        print(f"✅ Mistral 补丁工作正常")
        print(f"   回复: {response.choices[0].message.content[:50]}...")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✅ 补丁模块测试通过")
    print()
    return True


def test_list_models():
    """测试列出模型"""
    print("=" * 60)
    print("测试 8: 列出可用模型")
    print("=" * 60)
    
    try:
        client = KimiClient()
        models = client.list_models()
        
        print("可用模型:")
        for model in models:
            print(f"  - {model}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    print("\n✅ 列出模型测试通过")
    print()
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("Kimi API 测试套件")
    print("=" * 60 + "\n")
    
    # 检查环境变量
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ 错误: ANTHROPIC_API_KEY 环境变量未设置")
        print("请运行: export ANTHROPIC_API_KEY=sk-kimi-...")
        print("   或: export ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY")
        return 1
    
    print(f"✅ API Key 已设置: {os.getenv('ANTHROPIC_API_KEY')[:20]}...")
    print()
    
    # 运行所有测试
    tests = [
        ("基本连接", test_basic_connection),
        ("列出模型", test_list_models),
        ("文本补全", test_text_completion),
        ("多轮对话", test_multi_turn_chat),
        ("系统提示", test_system_prompt),
        ("流式输出", test_streaming),
        ("OpenAI 兼容模式", test_openai_compatible),
        ("补丁模块", test_patches),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ 测试 '{name}' 异常: {e}")
            results.append((name, False))
    
    # 汇总结果
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！Kimi API 客户端工作正常。")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个测试失败，请检查配置和网络连接。")
        return 1


if __name__ == "__main__":
    exit(main())
