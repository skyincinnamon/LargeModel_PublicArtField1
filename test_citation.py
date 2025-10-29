#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试文献引用功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from 组合5 import initialize_system, generate_response

def test_citation():
    """测试文献引用功能"""
    print("正在初始化系统...")
    components = initialize_system()
    
    # 测试问题
    test_questions = [
        "社会艺术是什么？",
        "公共艺术有哪些特点？",
        "艺术教育在高校中的作用是什么？"
    ]
    
    # 初始化对话历史
    messages = [
        {
            "role": "system",
            "content": "你是一个公共艺术专家，请根据提供的文献资料，用专业且详细的方式回答问题。"
        }
    ]
    
    print("\n" + "="*60)
    print("文献引用功能测试")
    print("="*60)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n测试 {i}: {question}")
        print("-" * 40)
        
        # 添加用户消息
        messages.append({"role": "user", "content": question})
        
        try:
            # 生成响应
            response = generate_response(components, messages, question)
            print(f"回答: {response}")
            
            # 添加助手响应
            messages.append({"role": "assistant", "content": response})
            
            # 检查是否包含文献引用
            if "《" in response and "》" in response:
                print("✓ 包含文献引用")
            else:
                print("✗ 缺少文献引用")
                
        except Exception as e:
            print(f"生成响应时出错: {e}")
        
        # 限制历史长度
        if len(messages) > 11:  # 保留系统消息 + 5轮对话
            messages = [messages[0]] + messages[-10:]
    
    print("\n测试完成！")

if __name__ == "__main__":
    test_citation() 