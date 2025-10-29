from fastapi import FastAPI, HTTPException, Request, Response, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from pathlib import Path
import sys
import logging
from uuid import uuid4
from datetime import datetime
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 解决模块导入问题
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from llm_rag import initialize_components, HybridQA

class Config:
    API_TITLE = "公共艺术智能问答系统API"
    API_DESCRIPTION = "提供公共艺术领域的智能问答服务，支持多轮对话"
    API_VERSION = "1.2.0"
    HOST = "0.0.0.0"
    PORT = 8000
    COOKIE_MAX_AGE = 86400  # 24小时

app = FastAPI(
    title=Config.API_TITLE,
    description=Config.API_DESCRIPTION,
    version=Config.API_VERSION
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
    expose_headers=["*"]
)

# 全局变量
qa_system = None

@app.on_event("startup")
async def startup_event():
    """启动时初始化模型"""
    global qa_system
    try:
        logger.info("正在初始化模型组件...")
        components = initialize_components()
        qa_system = HybridQA(components)
        logger.info("模型初始化完成")
    except Exception as e:
        logger.error(f"模型初始化失败: {e}")
        raise

class QuestionRequest(BaseModel):
    question: str
    session_id: str = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: str = None

@app.post("/api/ask")
async def ask_question(
    request: Request, 
    response: Response,
    session_id: str = Cookie(default=None)
):
    """问答接口，支持多轮对话"""
    try:
        # 解析请求体
        body = await request.body()
        data = json.loads(body)
        question = data.get("question", "").strip()
        
        if not question:
            raise HTTPException(status_code=400, detail="问题不能为空")
        
        # 优先使用请求中的session_id，否则使用Cookie中的，否则创建新的
        session_id = data.get("session_id") or session_id or str(uuid4())
        
        # 调用问答系统
        answer = qa_system.ask(question, session_id)
        
        # 设置响应
        resp_data = {
            "success": True,
            "answer": answer,
            "session_id": session_id
        }
        
        response = JSONResponse(resp_data)
        response.set_cookie(
            key="session_id",
            value=session_id,
            max_age=Config.COOKIE_MAX_AGE,
            httponly=True,
            samesite="Lax"
        )
        
        return response
        
    except HTTPException as he:
        logger.error(f"HTTP异常: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"问答处理错误: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "问答处理失败",
                "detail": str(e)
            }
        )

@app.get("/api/history")
async def get_history(session_id: str = Cookie(default=None)):
    """获取对话历史"""
    if not session_id:
        return {"success": False, "error": "无效的会话ID"}
    
    try:
        history = qa_system.get_conversation_history(session_id)
        return {
            "success": True,
            "history": {
                "user_queries": history.user_queries,
                "bot_responses": history.bot_responses,
                "created_at": history.created_at.isoformat(),
                "updated_at": history.updated_at.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"获取历史失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "获取历史失败",
                "detail": str(e)
            }
        )

@app.delete("/api/history")
async def clear_history(response: Response, session_id: str = Cookie(default=None)):
    """清除对话历史"""
    if not session_id:
        return {"success": False, "error": "无效的会话ID"}
    
    try:
        qa_system.db.delete_conversation(session_id)
        # 清除Cookie
        response.delete_cookie("session_id")
        return {"success": True, "message": "对话历史已清除"}
    except Exception as e:
        logger.error(f"清除历史失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "清除历史失败",
                "detail": str(e)
            }
        )

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": Config.API_VERSION,
        "model_loaded": qa_system is not None
    }

if __name__ == "__main__":
    logger.info("\n服务启动信息:")
    logger.info(f"• 本地访问: http://localhost:{Config.PORT}")
    logger.info(f"• API文档: http://localhost:{Config.PORT}/docs")
    
    uvicorn.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        log_level="info",
        reload=True
    )