# 公共艺术RAG后端启动脚本
Write-Host "正在启动公共艺术RAG后端服务..." -ForegroundColor Green

# 切换到后端目录
Set-Location ".\backend"

# 检查Python环境
Write-Host "检查Python环境..." -ForegroundColor Yellow
python --version

# 启动后端服务
Write-Host "启动后端服务..." -ForegroundColor Yellow
python start_server.py

# 保持窗口打开
Write-Host "服务已停止，按任意键退出..." -ForegroundColor Red
Read-Host 