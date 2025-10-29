from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import logging
import traceback
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入大模型相关模块
from 组合5 import initialize_system, generate_response

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('Backend_API')

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局变量存储系统组件
system_components = None
conversation_history = []

# 对话历史配置
HISTORY_CONFIG = {
    "max_rounds": 30,        # 最大对话轮次（从10增加到30）
    "max_messages": 60,      # 最大消息数量（从20增加到60）
    "max_message_length": 10000,  # 单条消息最大长度
    "max_total_length": 50000     # 总历史记录最大长度
}

def initialize_backend():
    """初始化系统组件"""
    global system_components
    try:
        logger.info("正在初始化后端系统...")
        system_components = initialize_system()
        logger.info("后端系统初始化完成")
    except Exception as e:
        logger.error(f"系统初始化失败: {e}")
        logger.error(traceback.format_exc())

def truncate_message(message, max_length):
    """截断过长的消息"""
    if len(message) > max_length:
        return message[:max_length-100] + "...[消息已截断]"
    return message

def manage_history_size():
    """管理历史记录大小"""
    global conversation_history
    
    # 检查总长度
    total_length = sum(len(msg.get('content', '')) for msg in conversation_history)
    if total_length > HISTORY_CONFIG["max_total_length"]:
        # 如果总长度超限，删除最旧的消息
        while total_length > HISTORY_CONFIG["max_total_length"] and len(conversation_history) > 4:
            removed_msg = conversation_history.pop(0)
            total_length -= len(removed_msg.get('content', ''))
        logger.info(f"历史记录总长度超限，已删除旧消息，当前长度: {total_length}")
    
    # 检查消息数量
    if len(conversation_history) > HISTORY_CONFIG["max_messages"]:
        conversation_history[:] = conversation_history[-HISTORY_CONFIG["max_messages"]:]
        logger.info(f"历史记录数量超限，已截断，当前数量: {len(conversation_history)}")

@app.route('/api/chat', methods=['POST'])
def chat():
    """处理聊天请求"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': '消息不能为空'
            }), 400
        
        if system_components is None:
            return jsonify({
                'success': False,
                'error': '系统未初始化，请稍后重试'
            }), 503
        
        logger.info(f"收到用户消息: {user_message[:50]}...")
        
        # 截断过长的用户消息
        user_message = truncate_message(user_message, HISTORY_CONFIG["max_message_length"])
        
        # 构建对话历史 - 使用更大的历史记录容量
        messages = []
        
        # 添加系统消息
        messages.append({
            "role": "system", 
            "content": "你是一个公共艺术专家，请根据提供的文献资料，用专业且详细的方式回答问题。"
        })
        
        # 添加历史对话记录 - 增加保留的对话轮次
        for msg in conversation_history[-HISTORY_CONFIG["max_rounds"]*2:]:  # 保留更多轮对话
            messages.append(msg)
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})
        
        logger.info(f"当前对话历史包含 {len(messages)} 条消息")
        
        # 生成响应
        response = generate_response(system_components, messages, user_message)
        
        # 截断过长的响应
        response = truncate_message(response, HISTORY_CONFIG["max_message_length"])
        
        # 添加助手响应到历史
        messages.append({"role": "assistant", "content": response})
        
        # 更新全局对话历史（只保存用户和助手的对话，不包含系统消息）
        conversation_history.extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": response}
        ])
        
        # 管理历史记录大小
        manage_history_size()
        
        logger.info(f"生成响应完成，长度: {len(response)}")
        logger.info(f"当前历史记录: {len(conversation_history)} 条消息")
        
        return jsonify({
            'success': True,
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'history_info': {
                'message_count': len(conversation_history),
                'total_length': sum(len(msg.get('content', '')) for msg in conversation_history)
            }
        })
        
    except Exception as e:
        logger.error(f"处理聊天请求时出错: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'system_initialized': system_components is not None,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    """清空对话历史"""
    global conversation_history
    conversation_history.clear()
    return jsonify({
        'success': True,
        'message': '对话历史已清空'
    })

@app.route('/api/history', methods=['GET'])
def get_history():
    """获取对话历史"""
    total_length = sum(len(msg.get('content', '')) for msg in conversation_history)
    return jsonify({
        'success': True,
        'history': conversation_history,
        'history_info': {
            'message_count': len(conversation_history),
            'total_length': total_length,
            'max_messages': HISTORY_CONFIG["max_messages"],
            'max_total_length': HISTORY_CONFIG["max_total_length"],
            'max_rounds': HISTORY_CONFIG["max_rounds"]
        }
    })

if __name__ == '__main__':
    # 在应用启动时初始化系统
    with app.app_context():
        initialize_backend()
    
    # 开发模式配置
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    ) 