#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time

def test_health_check():
    """测试健康检查接口"""
    print("🔍 测试健康检查接口...")
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查通过: {data}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def test_chat_api():
    """测试聊天接口"""
    print("\n💬 测试聊天接口...")
    try:
        test_message = "什么是公共艺术？"
        payload = {"message": test_message}
        
        print(f"发送消息: {test_message}")
        response = requests.post(
            "http://localhost:5000/api/chat",
            json=payload,
            timeout=60  # 聊天接口可能需要更长时间
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ 聊天接口测试通过")
                print(f"响应长度: {len(data.get('response', ''))} 字符")
                print(f"响应预览: {data.get('response', '')[:100]}...")
                return True
            else:
                print(f"❌ 聊天接口返回错误: {data.get('error')}")
                return False
        else:
            print(f"❌ 聊天接口HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 聊天接口异常: {e}")
        return False

def test_history_api():
    """测试历史记录接口"""
    print("\n📚 测试历史记录接口...")
    try:
        response = requests.get("http://localhost:5000/api/history", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 历史记录接口测试通过")
            print(f"历史记录数量: {len(data.get('history', []))}")
            return True
        else:
            print(f"❌ 历史记录接口失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 历史记录接口异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 开始API测试...")
    print("=" * 50)
    
    # 等待服务启动
    print("⏳ 等待服务启动...")
    time.sleep(3)
    
    # 测试健康检查
    health_ok = test_health_check()
    
    if not health_ok:
        print("\n❌ 健康检查失败，请确保后端服务正在运行")
        return
    
    # 测试聊天接口
    chat_ok = test_chat_api()
    
    # 测试历史记录接口
    history_ok = test_history_api()
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"健康检查: {'✅ 通过' if health_ok else '❌ 失败'}")
    print(f"聊天接口: {'✅ 通过' if chat_ok else '❌ 失败'}")
    print(f"历史记录: {'✅ 通过' if history_ok else '❌ 失败'}")
    
    if all([health_ok, chat_ok, history_ok]):
        print("\n🎉 所有测试通过！API服务运行正常")
    else:
        print("\n⚠️  部分测试失败，请检查服务状态")

if __name__ == "__main__":
    main() 