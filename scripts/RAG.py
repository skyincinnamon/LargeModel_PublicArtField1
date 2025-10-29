from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OllamaEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
from pathlib import Path
import os
import subprocess
from tqdm import tqdm

# PDF文件目录
pdf_directory = r"knowledge_base\相关文本资料汇总"

# Ollama模型配置
embedding_model_name = "deepseek-r1:1.5b"  # 用于嵌入的模型
llm_model_name = "llama2-chinese:7b"              # 用于生成回答的模型

# 检查Ollama模型是否存在
def check_ollama_model(model_name):
    try:
        result = subprocess.run(
            ["ollama", "list"], 
            capture_output=True, 
            text=True
        )
        if model_name in result.stdout:
            print(f"Ollama模型 '{model_name}' 已安装")
            return True
        else:
            print(f"错误: Ollama模型 '{model_name}' 未安装")
            print("请先下载模型: ollama pull " + model_name)
            return False
    except Exception as e:
        print(f"检查Ollama模型时出错: {e}")
        print("请确保Ollama已正确安装并可在命令行中使用")
        return False

# 检查所有需要的模型
for model in [embedding_model_name, llm_model_name]:
    if not check_ollama_model(model):
        exit(1)

# 加载文档并创建向量数据库（如果不存在）
db_directory = r"chroma_db_deepseek_1.5b"
collection_name = "academic_papers_deepseek_1.5b"

# 检查数据库是否存在
if os.path.exists(db_directory) and os.listdir(db_directory):
    print(f"加载现有Chroma数据库: {db_directory}")
    embeddings = OllamaEmbeddings(model=embedding_model_name)
    vector_store = Chroma(
        embedding_function=embeddings,
        persist_directory=db_directory,
        collection_name=collection_name
    )
    print(f"数据库加载成功，包含 {len(vector_store.get()['ids'])} 个文档")
else:
    print(f"错误: 数据库目录 {db_directory} 不存在或为空")
    print("请先运行向量化脚本创建数据库")
    exit(1)

# 初始化LLM（调用Ollama本地模型）
llm = Ollama(
    model=llm_model_name,
    temperature=0.7,
    base_url="http://localhost:11434"
)

# ======提示词模板 ======
prompt_template = """
您是一位精通公共艺术领域的专业学术助手，请严格使用中文，根据以下10篇文献内容回答问题：

{context}

问题：{question}

回答要求：
1. 全程使用中文回答，禁止使用英文（除非必要的技术术语）
2. 结构化输出：按"总-分-总"结构组织答案
3. 严格基于文献：
   - 先总结核心观点（标注来源页码）
   - 分点列出关键证据（每个论点注明出处）
   - 最后进行综合评述
4. 学术规范：
   - 使用专业术语但避免晦涩
   - 保持客观中立立场
   - 文献未涵盖的内容明确说明"未找到相关依据"

示例格式：
【总述】主要观点是...  
【分述】  
1. 观点1...  
2. 观点2...  
【结论】综合来看...
"""
PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "question"]
)

# 构建RAG链（检索+生成）
rag_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",  # 直接将检索结果传入模型（适合小规模数据）
    retriever=vector_store.as_retriever(
        search_kwargs={"k": 10}  # 每次检索前10条相关文档
    ),
    return_source_documents=True,  # 输出答案时附带来源
    chain_type_kwargs={
        "prompt": PROMPT  # 使用自定义提示词
    }
)

# 定义一个函数来处理用户查询
def ask_question(query):
    print(f"\n查询: {query}")
    result = rag_chain({"query": query})
    
    print("\n答案:")
    print(result["result"])
    
    print("-" * 80)

while True:
    user_query = input("\n请输入您的问题（输入'q'退出）: ")
    if user_query.lower() == 'q':
        break
    ask_question(user_query)