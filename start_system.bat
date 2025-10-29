@echo off
chcp 65001 >nul
title 公共艺术RAG系统启动器

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    公共艺术RAG系统启动器                      ║
echo ║                                                              ║
echo ║  🎨 前端界面: http://localhost:8080                          ║
echo ║  🔧 后端API:  http://localhost:5000                          ║
echo ║  📊 健康检查: http://localhost:5000/api/health               ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo 🔍 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python环境检查通过
echo.

echo 🚀 启动公共艺术RAG系统...
echo.

python start_system.py

echo.
echo 👋 系统已关闭
pause 