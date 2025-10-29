# 公共艺术RAG后端服务

这是一个基于Flask的后端API服务，用于连接前端界面和本地大模型，提供公共艺术领域的智能问答功能。

## 功能特性

- 🔍 **RAG检索增强生成**：基于向量数据库的智能文档检索
- 💬 **对话历史管理**：支持多轮对话，保持上下文连贯性
- 🚀 **异步处理**：支持并发请求处理
- 🔒 **错误处理**：完善的异常处理和日志记录
- 🌐 **跨域支持**：支持前端跨域请求

## 系统要求

- Python 3.8+
- CUDA支持的GPU（推荐）
- 至少8GB内存
- Ollama服务

## 安装步骤

1. **安装Python依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **确保Ollama服务运行**
   ```bash
   # 检查Ollama是否安装
   ollama --version
   
   # 拉取必要的嵌入模型
   ollama pull deepseek-r1:1.5b
   ```

3. **检查文件结构**
   ```
   qwen-rag-lora/
   ├── backend/           # 后端服务目录
   ├── models/            # 大模型文件
   ├── chroma_db_deepseek_1.5b/  # 向量数据库
   ├── knowledge_base/    # 知识库文档
   └── 组合5.py          # 大模型核心文件
   ```

## 启动服务

### 方法1：使用启动脚本（推荐）
```bash
cd backend
python start_server.py
```

### 方法2：直接运行Flask应用
```bash
cd backend
python app.py
```

### 方法3：使用Flask命令
```bash
cd backend
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
```

## API接口

### 1. 聊天接口
- **URL**: `POST /api/chat`
- **功能**: 处理用户提问并返回AI回答
- **请求体**:
  ```json
  {
    "message": "用户的问题内容"
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "response": "AI的回答内容",
    "timestamp": "2024-01-01T12:00:00"
  }
  ```

### 2. 健康检查
- **URL**: `GET /api/health`
- **功能**: 检查服务状态和系统初始化情况

### 3. 清空对话历史
- **URL**: `POST /api/clear-history`
- **功能**: 清空当前对话历史

### 4. 获取对话历史
- **URL**: `GET /api/history`
- **功能**: 获取当前对话历史记录

## 配置说明

配置文件位于 `config.py`，主要配置项：

- **服务器配置**: 主机地址、端口号
- **模型配置**: 模型路径、向量数据库路径
- **RAG配置**: 检索参数、相似度阈值
- **生成配置**: 温度、最大token数等
- **跨域配置**: 允许的前端域名

## 日志文件

- 日志文件: `backend.log`
- 日志级别: INFO（开发环境为DEBUG）
- 日志格式: 时间戳 - 模块名 - 级别 - 消息

## 故障排除

### 常见问题

1. **模型加载失败**
   - 检查模型文件路径是否正确
   - 确认GPU内存是否充足
   - 检查CUDA版本兼容性

2. **向量数据库错误**
   - 确认 `chroma_db_deepseek_1.5b` 目录存在
   - 检查数据库文件完整性

3. **Ollama连接失败**
   - 确认Ollama服务正在运行
   - 检查嵌入模型是否已安装

4. **内存不足**
   - 减少 `MAX_NEW_TOKENS` 参数
   - 降低 `RETRIEVAL_K` 参数
   - 使用CPU模式（修改设备映射）

### 性能优化

1. **GPU内存优化**
   - 使用 `torch.bfloat16` 精度
   - 启用梯度检查点
   - 使用模型量化

2. **响应速度优化**
   - 调整检索参数
   - 优化提示模板
   - 使用缓存机制

## 开发说明

### 项目结构
```
backend/
├── app.py              # 主应用文件
├── config.py           # 配置文件
├── start_server.py     # 启动脚本
├── requirements.txt    # 依赖列表
├── README.md          # 说明文档
└── backend.log        # 日志文件（运行时生成）
```

### 扩展开发

1. **添加新的API接口**
   - 在 `app.py` 中添加新的路由
   - 更新配置和文档

2. **修改模型配置**
   - 编辑 `config.py` 中的参数
   - 重启服务生效

3. **自定义提示模板**
   - 修改 `组合5.py` 中的提示模板
   - 调整生成参数

## 许可证

本项目仅供学习和研究使用。 