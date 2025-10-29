#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import time
import threading
import webbrowser
from pathlib import Path

def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    公共艺术RAG系统启动器                      ║
    ║                                                              ║
    ║  🎨 前端界面: http://localhost:8080                          ║
    ║  🔧 后端API:  http://localhost:5000                          ║
    ║  📊 健康检查: http://localhost:5000/api/health               ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_dependencies():
    """检查系统依赖"""
    print("🔍 检查系统依赖...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        return False
    
    # 检查必要文件
    required_files = [
        "组合5.py",
        "backend/app.py",
        "backend/requirements.txt",
        "frontend/index.html"
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ 错误: 找不到文件 {file_path}")
            return False
    
    print("✅ 系统依赖检查通过")
    return True

def install_backend_dependencies():
    """安装后端依赖"""
    print("📦 安装后端依赖...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"
        ], check=True, capture_output=True, text=True)
        print("✅ 后端依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 后端依赖安装失败: {e}")
        return False

def start_backend():
    """启动后端服务"""
    print("🚀 启动后端服务...")
    try:
        # 切换到backend目录
        os.chdir("backend")
        
        # 启动Flask应用
        process = subprocess.Popen([
            sys.executable, "start_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # 等待服务启动
        time.sleep(5)
        
        # 检查服务是否正常启动
        if process.poll() is None:
            print("✅ 后端服务启动成功")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ 后端服务启动失败:")
            print(f"stdout: {stdout}")
            print(f"stderr: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ 启动后端服务时出错: {e}")
        return None

def start_frontend():
    """启动前端服务"""
    print("🌐 启动前端服务...")
    try:
        # 切换到frontend目录
        os.chdir("../frontend")
        
        # 使用Python内置的HTTP服务器
        process = subprocess.Popen([
            sys.executable, "-m", "http.server", "8080"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # 等待服务启动
        time.sleep(2)
        
        if process.poll() is None:
            print("✅ 前端服务启动成功")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ 前端服务启动失败:")
            print(f"stdout: {stdout}")
            print(f"stderr: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ 启动前端服务时出错: {e}")
        return None

def open_browser():
    """打开浏览器"""
    print("🌍 正在打开浏览器...")
    time.sleep(3)  # 等待服务完全启动
    try:
        webbrowser.open("http://localhost:8080")
        print("✅ 浏览器已打开")
    except Exception as e:
        print(f"⚠️  无法自动打开浏览器: {e}")
        print("请手动访问: http://localhost:8080")

def monitor_services(backend_process, frontend_process):
    """监控服务状态"""
    try:
        while True:
            # 检查后端服务
            if backend_process and backend_process.poll() is not None:
                print("❌ 后端服务已停止")
                break
            
            # 检查前端服务
            if frontend_process and frontend_process.poll() is not None:
                print("❌ 前端服务已停止")
                break
            
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n🛑 收到停止信号，正在关闭服务...")
        
        # 关闭后端服务
        if backend_process:
            backend_process.terminate()
            backend_process.wait()
            print("✅ 后端服务已关闭")
        
        # 关闭前端服务
        if frontend_process:
            frontend_process.terminate()
            frontend_process.wait()
            print("✅ 前端服务已关闭")
        
        print("👋 系统已完全关闭")

def main():
    """主函数"""
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        print("❌ 系统依赖检查失败，请检查文件结构")
        return
    
    # 安装后端依赖
    if not install_backend_dependencies():
        print("❌ 后端依赖安装失败")
        return
    
    # 启动后端服务
    backend_process = start_backend()
    if not backend_process:
        print("❌ 后端服务启动失败")
        return
    
    # 启动前端服务
    frontend_process = start_frontend()
    if not frontend_process:
        print("❌ 前端服务启动失败")
        backend_process.terminate()
        return
    
    # 打开浏览器
    open_browser()
    
    print("\n🎉 系统启动完成！")
    print("按 Ctrl+C 停止所有服务")
    
    # 监控服务状态
    monitor_services(backend_process, frontend_process)

if __name__ == "__main__":
    main() 