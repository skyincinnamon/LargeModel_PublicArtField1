import torch
import logging
from transformers import AutoTokenizer, AutoModelForCausalLM
from langchain.embeddings import OllamaEmbeddings
from langchain.vectorstores import Chroma
from langchain.prompts import PromptTemplate
import os
import subprocess
import re
import shutil

# 设置日志配置
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('RAG_Enhanced_Chat')
logger.setLevel(logging.INFO)

# ================== 配置区域 ==================
# 获取项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))

# PDF知识库目录
pdf_directory = os.path.join(project_root, "knowledge_base", "相关文本资料汇总")

# 向量数据库配置
db_directory = os.path.join(project_root, "chroma_db_deepseek_1.5b")
collection_name = "academic_papers_deepseek_1.5b"

# Ollama嵌入模型配置
embedding_model_name = "deepseek-r1:1.5b"

# 微调模型配置
model_path = os.path.join(project_root, "models", "Qwen3-8B-optimized").replace("\\", "/")

# RAG检索配置
retrieval_config = {
    "k": 12,  # 增加检索文档数量，从8增加到12
    "score_threshold": 0.4  # 降低相似度阈值，从0.6降低到0.4，获取更多相关文档
}

# 生成配置
generation_config = {
    "max_new_tokens": 800,   # 增加最大生成长度，从500增加到800
    "min_new_tokens": 20,    # 增加最小生成长度，从10增加到20
    "temperature": 0.7,      # 保持温度设置
    "top_p": 0.9,
    "top_k": 40,
    "repetition_penalty": 1.05,
    "do_sample": True,
    "num_beams": 1,          # 使用贪婪搜索，提高速度
    "length_penalty": 1.0    # 长度惩罚
}

# ================== 辅助函数 ==================
def check_ollama_model(model_name):
    """检查Ollama模型是否已安装"""
    try:
        result = subprocess.run(
            ["ollama", "list"], 
            capture_output=True, 
            text=True
        )
        if model_name in result.stdout:
            logger.info(f"Ollama模型 '{model_name}' 已安装")
            return True
        else:
            logger.error(f"Ollama模型 '{model_name}' 未安装")
            logger.info("请先下载模型: ollama pull " + model_name)
            return False
    except Exception as e:
        logger.error(f"检查Ollama模型时出错: {e}")
        logger.error("请确保Ollama已正确安装并可在命令行中使用")
        return False

def format_context(docs):
    """格式化检索到的上下文文档"""
    formatted = []
    for i, doc in enumerate(docs):
        source = os.path.basename(doc.metadata.get('source', '未知文档'))
        page = doc.metadata.get('page', 'N/A')
        content = re.sub(r'\s+', ' ', doc.page_content.strip())
        
        # 提取文件名作为文献名称（去掉扩展名）
        doc_name = os.path.splitext(source)[0]
        
        # 格式化输出，突出文献名称
        formatted.append(f"【文献 {i+1}】《{doc_name}》 (第{page}页)\n{content[:800]}{'...' if len(content) > 800 else ''}")
    return "\n\n".join(formatted)

# ================== 初始化系统 ==================
def initialize_system():
    """初始化所有组件"""
    # 检查Ollama模型
    if not check_ollama_model(embedding_model_name):
        logger.error("必要的Ollama模型未安装，系统退出")
        exit(1)
    
    # 加载向量数据库
    if not os.path.exists(db_directory) or not os.listdir(db_directory):
        logger.error(f"向量数据库目录不存在或为空: {db_directory}")
        logger.error("请先创建向量数据库")
        exit(1)
    
    logger.info("正在加载嵌入模型和向量数据库...")
    embeddings = OllamaEmbeddings(model=embedding_model_name)
    
    # 尝试加载向量数据库，如果失败则重新创建
    try:
        vector_store = Chroma(
            embedding_function=embeddings,
            persist_directory=db_directory,
            collection_name=collection_name
        )
        # 尝试获取文档数量
        doc_count = vector_store._collection.count()
        logger.info(f"向量数据库加载成功，包含 {doc_count} 个文档")
    except Exception as e:
        logger.warning(f"向量数据库加载失败: {e}")
        logger.info("尝试重新创建向量数据库...")
        
        # 删除损坏的数据库
        if os.path.exists(db_directory):
            shutil.rmtree(db_directory)
        
        # 重新创建数据库
        vector_store = Chroma(
            embedding_function=embeddings,
            persist_directory=db_directory,
            collection_name=collection_name
        )
        logger.info("向量数据库重新创建成功")
    
    retriever = vector_store.as_retriever(
        search_kwargs={
            "k": retrieval_config["k"],
            "score_threshold": retrieval_config["score_threshold"]
        }
    )
    
    # 加载微调模型
    logger.info(f"正在加载微调模型: {model_path}")
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True,
        padding_side="right",
        use_fast=False
    )
    tokenizer.truncation_side = "left"
    tokenizer.pad_token = tokenizer.eos_token

    # 使用基础模型路径加载模型
    base_model_path = os.path.join(project_root, "models", "Qwen3-8B").replace("\\", "/")
    logger.info(f"基础模型路径: {base_model_path}")
    
    model = AutoModelForCausalLM.from_pretrained(
        base_model_path,
        trust_remote_code=True,
        device_map="auto",
        torch_dtype=torch.bfloat16
    )
    
    # 加载LoRA适配器
    if os.path.exists(os.path.join(model_path, "adapter_model.safetensors")):
        logger.info("正在加载LoRA适配器...")
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, model_path)
        logger.info("LoRA适配器加载完成")
    
    model.eval()
    logger.info(f"模型加载完成，使用的设备: {model.device}")
    
    # 定义提示模板
    prompt_template = PromptTemplate(
        input_variables=["context", "history", "question"],
        template="""
[系统提示]
你是一位精通公共艺术领域的专业学术助手，请严格使用中文回答问题。

[回答要求]
1. 全程使用中文回答，禁止使用英文（技术术语除外）
2. 不要输出思考过程，直接给出答案
3. 不要使用**符号，使用其他方式强调重点
4. 合理换行，使回答结构清晰
5. 逻辑清晰地回答问题，必要时刻可分点叙述
6. 严格基于文献回答，必须明确引用：
   - 在回答中明确提到文献资料的名称
   - 使用"根据《文献名称》"、"《文献名称》指出"等表达方式
   - 先总结核心观点，再进行详细解释
   - 如果引用多个文献，要分别说明每个文献的观点
7. 学术规范：
   - 使用专业术语但避免晦涩
   - 保持客观中立立场
   - 文献未涵盖的内容无需明确说明"未找到相关依据"，但是也不能臆想，随意乱说
8. 如果需要可以提供详细解释和具体案例，确保回答内容丰富
9. 引用格式示例：
   - "根据《社会艺术——公共艺术发展的另一种可能》..."
   - "《公共艺术理论与实践》指出..."
   - "在《当代公共艺术研究》中，作者认为..."

当前对话历史：
{history}

[相关文献]
{context}

[用户问题]
{question}

请基于上述文献资料回答，必须明确引用文献名称：
        """
    )
    
    return {
        "retriever": retriever,
        "model": model,
        "tokenizer": tokenizer,
        "prompt_template": prompt_template
    }

# ================== 核心聊天功能 ==================
def generate_response(components, history, question):
    """生成RAG增强的响应"""
    # 1. 构建对话历史 - 修复历史记录处理
    history_str = ""
    for i, msg in enumerate(history):
        if msg["role"] == "system":
            # 跳过系统消息，因为已经在模板中包含了
            continue
        elif msg["role"] == "user":
            history_str += f"用户: {msg['content']}\n"
        elif msg["role"] == "assistant":
            history_str += f"助手: {msg['content']}\n"
    
    # 如果历史为空，添加默认提示
    if not history_str.strip():
        history_str = "这是对话的开始。\n"
    
    logger.info(f"对话历史长度: {len(history_str)} 字符")
    
    # 2. 智能检索 - 结合对话历史和当前问题
    # 如果当前问题很短（少于10个字符），结合最近的对话历史进行检索
    if len(question.strip()) < 10:
        # 获取最近的用户问题和助手回答
        recent_context = ""
        for msg in reversed(history[-4:]):  # 获取最近2轮对话
            if msg["role"] == "user":
                recent_context = msg["content"] + " " + recent_context
            elif msg["role"] == "assistant":
                recent_context = msg["content"] + " " + recent_context
        
        # 结合当前问题和历史上下文进行检索
        search_query = f"{recent_context} {question}".strip()
        logger.info(f"简短问题，使用扩展查询: {search_query}")
    else:
        search_query = question
    
    # 执行检索
    retrieved_docs = components["retriever"].get_relevant_documents(search_query)
    context = format_context(retrieved_docs)
    
    logger.info(f"检索到 {len(retrieved_docs)} 个相关文档")
    
    # 3. 构建提示
    prompt = components["prompt_template"].format(
        context=context,
        history=history_str,
        question=question
    )
    
    # 4. 添加特殊标记
    input_text = f"[|im_start|]user\n{prompt}\n[|im_end|]\n[|im_start|]assistant\n"
    
    # 5. 生成响应
    inputs = components["tokenizer"](
        input_text,
        return_tensors="pt",
        max_length=2048,     # 增加输入长度以支持更长的对话历史
        truncation=True,
        padding=True,        # 启用padding
        add_special_tokens=True
    )
    
    input_ids = inputs.input_ids.to(components["model"].device)
    attention_mask = inputs.attention_mask.to(components["model"].device)
    
    with torch.no_grad():
        outputs = components["model"].generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            **generation_config
        )
    
    # 6. 解码并清理响应
    full_response = components["tokenizer"].decode(outputs[0], skip_special_tokens=False)
    
    if "[|im_start|]assistant" in full_response:
        response = full_response.split("[|im_start|]assistant")[-1]
    else:
        response = full_response
    
    # 移除特殊标记
    special_tokens = ["[|im_end|]", "<|im_end|>", "]", "|im_end|", "<|im_start|>", "|im_start|"]
    for token in special_tokens:
        response = response.split(token)[0].strip()
    
    return response.strip()

# ================== 主程序 ==================
def main():
    # 初始化系统
    components = initialize_system()
    
    # 初始化对话历史
    messages = [
        {
            "role": "system",
            "content": "你是一个公共艺术专家，请根据提供的文献资料，用专业且详细的方式回答问题。"
        }
    ]
    
    logger.info("系统初始化完成，可以开始对话...")
    print("=" * 60)
    print("公共艺术学术助手 (RAG增强版)")
    print("输入 '退出' 结束对话")
    print("=" * 60)
    
    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ['退出', 'exit', 'quit']:
            print("对话结束。")
            break
        
        # 添加用户消息到历史
        messages.append({"role": "user", "content": user_input})
        
        try:
            # 生成响应
            response = generate_response(components, messages, user_input)
            print("\n助手: " + response)
            
            # 添加助手响应到历史
            messages.append({"role": "assistant", "content": response})
            
            # 限制历史长度
            max_history = 5
            if len(messages) > max_history * 2 + 1:
                messages = [messages[0]] + messages[-max_history*2:]
                logger.info(f"对话历史截断，保留最近{max_history}轮对话")
                
        except Exception as e:
            logger.error(f"生成响应时出错: {e}")
            print("抱歉，处理您的请求时出现问题，请重新提问。")
        
        # 清理GPU内存
        torch.cuda.empty_cache()

if __name__ == "__main__":
    main()