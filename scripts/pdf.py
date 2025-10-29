from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OllamaEmbeddings
from langchain.vectorstores import Chroma
from pathlib import Path
import os
import subprocess
from tqdm import tqdm

# PDF文件目录
pdf_directory = r"knowledge_base\相关文本资料汇总"

# Ollama模型配置
model_name = "deepseek-r1:1.5b"

# 检查Ollama模型是否存在
def check_ollama_model(model_name):
    try:
        # 执行ollama list命令并获取输出
        result = subprocess.run(
            ["ollama", "list"], 
            capture_output=True, 
            text=True
        )
        
        # 检查模型是否在列表中
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

# 检查模型是否存在
if not check_ollama_model(model_name):
    exit(1)

# 初始化文档列表
documents = []

# 遍历目录中的所有PDF文件
if not os.path.exists(pdf_directory):
    print(f"错误：指定的目录不存在 - {pdf_directory}")
    exit(1)

pdf_files = list(Path(pdf_directory).glob("*.pdf"))

if not pdf_files:
    print(f"错误：在目录中未找到PDF文件。请确认文件扩展名是否为.pdf")
    exit(1)

print(f"找到 {len(pdf_files)} 个PDF文件")

# 加载所有PDF文件
for pdf_path in pdf_files:
    try:
        if not os.access(str(pdf_path), os.R_OK):
            print(f"警告：文件 {pdf_path.name} 不可读，跳过")
            continue
            
        loader = PyPDFLoader(str(pdf_path))
        pdf_docs = loader.load()
        
        if not pdf_docs:
            print(f"警告：文件 {pdf_path.name} 加载后没有内容")
        else:
            documents.extend(pdf_docs)
            print(f"成功加载: {pdf_path.name} ({len(pdf_docs)} 页)")
            
    except Exception as e:
        print(f"错误：加载文件 {pdf_path.name} 时出错 - {str(e)}")

# 检查是否有文档被加载
if not documents:
    print("没有成功加载任何文档内容，请检查PDF文件是否损坏")
    exit(1)

print(f"共加载了 {len(documents)} 个文档片段")

# 针对1.5b模型优化文本分块大小
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,          # 小模型使用较小的chunk_size
    chunk_overlap=100,        # 保持一定重叠
    separators=["\n\n", "\n", " ", ""]
)

split_documents = text_splitter.split_documents(documents)
print(f"文本分割完成，共生成 {len(split_documents)} 个文本块")

# 使用Ollama生成文本嵌入
try:
    embeddings = OllamaEmbeddings(
        model=model_name,
        base_url="http://localhost:11434",  # Ollama默认API地址
    )
    print(f"成功连接到Ollama服务，使用模型: {model_name}")
except Exception as e:
    print(f"连接Ollama服务失败: {e}")
    exit(1)

# 创建/连接Chroma数据库
try:
    db_directory = r"chroma_db_deepseek_1.5b"
    collection_name = "academic_papers_deepseek_1.5b"
    
    if os.path.exists(db_directory) and os.listdir(db_directory):
        print(f"连接到现有Chroma数据库: {db_directory}")
        vector_store = Chroma(
            embedding_function=embeddings,
            persist_directory=db_directory,
            collection_name=collection_name
        )
    else:
        print(f"创建新的Chroma数据库: {db_directory}")
        batch_size = 30  # 小模型可以减小批次大小
        total_batches = (len(split_documents) + batch_size - 1) // batch_size
        
        print(f"开始分批处理文档: 共{len(split_documents)}个文档，{total_batches}批")
        
        vector_store = Chroma(
            embedding_function=embeddings,
            persist_directory=db_directory,
            collection_name=collection_name
        )
        
        for i in tqdm(range(0, len(split_documents), batch_size), desc="处理批次"):
            batch = split_documents[i:i+batch_size]
            vector_store.add_documents(batch)
            
            if i % (batch_size * 10) == 0:
                vector_store.persist()
                print(f"已处理 {i+len(batch)}/{len(split_documents)} 个文档")
    
    vector_store.persist()
    print(f"Chroma数据库已成功持久化到: {db_directory}")
    print(f"向量集合名称: {collection_name}")
    print(f"总文档数: {len(vector_store.get()['ids'])}")
    
except Exception as e:
    print(f"处理Chroma数据库时出错: {e}")
    exit(1)