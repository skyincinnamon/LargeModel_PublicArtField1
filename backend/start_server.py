#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import traceback
from pathlib import Path

# 设置项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('backend.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_dependencies():
    """检查必要的依赖和文件"""
    logger = logging.getLogger('Startup')
    
    # 检查组合5.py文件
    model_file = project_root / "组合5.py"
    if not model_file.exists():
        logger.error(f"找不到模型文件: {model_file}")
        return False
    
    # 检查向量数据库目录
    db_dir = project_root / "chroma_db_deepseek_1.5b"
    if not db_dir.exists():
        logger.error(f"找不到向量数据库目录: {db_dir}")
        return False
    
    # 检查模型目录
    model_dir = project_root / "models" / "Qwen3-8B-optimized"
    if not model_dir.exists():
        logger.error(f"找不到模型目录: {model_dir}")
        return False
    
    logger.info("所有依赖检查通过")
    return True

def main():
    """主启动函数"""
    setup_logging()
    logger = logging.getLogger('Startup')
    
    logger.info("正在启动公共艺术RAG后端服务...")
    
    # 检查依赖
    if not check_dependencies():
        logger.error("依赖检查失败，服务启动终止")
        sys.exit(1)
    
    try:
        # 导入Flask应用
        from app import app, initialize_backend
        
        # 在应用上下文中初始化系统
        with app.app_context():
            initialize_backend()
        
        logger.info("后端服务启动成功")
        logger.info("服务地址: http://localhost:5000")
        logger.info("API文档:")
        logger.info("  - POST /api/chat - 聊天接口")
        logger.info("  - GET  /api/health - 健康检查")
        logger.info("  - POST /api/clear-history - 清空历史")
        logger.info("  - GET  /api/history - 获取历史")
        
        # 启动Flask应用
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,  # 生产环境设为False
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"启动服务时出错: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main() 