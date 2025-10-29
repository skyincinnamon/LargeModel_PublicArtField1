# -*- coding: utf-8 -*-
"""
后端服务配置文件
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# Flask配置
class Config:
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    DEBUG = False
    TESTING = False
    
    # 服务器配置
    HOST = '0.0.0.0'
    PORT = 5000
    
    # 跨域配置
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "*"  # 开发环境允许所有来源
    ]
    
    # 模型配置
    MODEL_PATH = str(PROJECT_ROOT / "models" / "Qwen3-8B-optimized")
    VECTOR_DB_PATH = str(PROJECT_ROOT / "chroma_db_deepseek_1.5b")
    KNOWLEDGE_BASE_PATH = str(PROJECT_ROOT / "knowledge_base" / "相关文本资料汇总")
    
    # RAG配置
    RETRIEVAL_K = 8
    SCORE_THRESHOLD = 0.6
    
    # 生成配置
    MAX_NEW_TOKENS = 1500
    TEMPERATURE = 0.7
    TOP_P = 0.9
    TOP_K = 50
    REPETITION_PENALTY = 1.15
    
    # 对话历史配置
    MAX_HISTORY_LENGTH = 20
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'backend.log'

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    # 生产环境应该设置具体的CORS来源
    CORS_ORIGINS = [
        "https://your-domain.com"
    ]

# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """获取当前环境的配置"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default']) 