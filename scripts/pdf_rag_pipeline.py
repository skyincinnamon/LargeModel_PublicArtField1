import os
import re
import fitz  # PyMuPDF for PDF processing
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.docstore.document import Document
import logging
from tqdm import tqdm
import torch

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 禁用HuggingFace的网络请求（强制离线）
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

class RAGPipeline:
    def __init__(self, pdf_dir, persist_dir="vector_db", local_model_path=None):
        """初始化RAG流水线（纯离线模式，必须指定本地模型路径）"""
        self.pdf_dir = pdf_dir
        self.persist_dir = persist_dir
        
        # 强制检查本地模型路径（必须提供且存在）
        if not local_model_path:
            raise ValueError("请提供本地模型路径（离线模式下必须指定）")
        self.local_model_path = local_model_path
        
        # 验证模型路径存在性
        if not os.path.exists(self.local_model_path):
            raise FileNotFoundError(f"本地模型路径不存在: {self.local_model_path}\n请手动下载模型并放置到该路径")
        
        # 验证模型文件完整性
        self._check_model_files()
        
        # 检查GPU可用性
        self._check_gpu_availability()
        
        # 配置Embeddings（纯本地模式）
        model_kwargs = {
            'device': 'cuda' if torch.cuda.is_available() else 'cpu',
        }
        
        # 仅保留SentenceTransformer支持的参数
        encode_kwargs = {
            'batch_size': 32,
            'show_progress_bar': True,
        }
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.local_model_path,  # 强制使用本地路径
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )
        
        # 验证模型加载
        self._validate_model()
        
        self.text_splitter = self._create_text_splitter()
    
    def _check_model_files(self):
        """检查模型核心文件是否存在"""
        required_files = [
            "config.json",
            "pytorch_model.bin",  # 或model.safetensors
            "sentence_bert_config.json",
            "tokenizer_config.json",
            "vocab.txt"
        ]
        
        missing_files = []
        for file in required_files:
            file_path = os.path.join(self.local_model_path, file)
            if not os.path.exists(file_path):
                # 检查tokenizer子目录
                tokenizer_path = os.path.join(self.local_model_path, "tokenizer", file)
                if not os.path.exists(tokenizer_path):
                    missing_files.append(file)
        
        if missing_files:
            raise FileNotFoundError(
                f"本地模型文件不完整，缺少以下文件：{missing_files}\n"
                f"请确保模型路径包含完整的SentenceTransformer模型文件"
            )
    
    def _check_gpu_availability(self):
        """检查GPU可用性"""
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"使用GPU加速: {gpu_name}")
        else:
            logger.warning("未检测到GPU，使用CPU计算（可能较慢）")
    
    def _validate_model(self):
        """验证模型是否可正常加载"""
        try:
            logger.info(f"验证本地模型: {self.local_model_path}")
            test_embedding = self.embeddings.embed_query("测试文本")
            logger.info(f"模型验证成功，嵌入维度: {len(test_embedding)}")
        except Exception as e:
            raise RuntimeError(f"模型加载失败: {str(e)}\n请检查模型文件是否完整或损坏") from e
    
    def _create_text_splitter(self):
        """创建文本分割器"""
        return RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", "。", "！", "？", " ", ""],
            length_function=len
        )
    
    def _detect_columns(self, pdf_path):
        """检测PDF是否为双栏格式"""
        doc = fitz.open(pdf_path)
        for page_num in range(min(3, len(doc))):
            page = doc[page_num]
            text_blocks = page.get_text("dict")["blocks"]
            x_coords = [block["bbox"][0] for block in text_blocks if block["type"] == 0]
            if len(x_coords) > 3 and np.std(x_coords) > 50:
                return True
        return False
    
    def _process_double_column(self, pdf_path):
        """处理双栏PDF"""
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            sorted_blocks = sorted(blocks, key=lambda b: (b["bbox"][1], b["bbox"][0]))
            page_text = ""
            for block in sorted_blocks:
                if block["type"] == 0:
                    block_text = " ".join(["".join([span["text"] for span in line["spans"]]) for line in block["lines"]])
                    page_text += block_text.strip() + "\n"
            full_text += page_text + "\n\n"
        return full_text
    
    def _clean_text(self, text):
        """清理文本"""
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'[\xa0\x0c]', ' ', text)
        return text
    
    def process_pdfs(self):
        """处理所有PDF文件"""
        documents = []
        pdf_files = [f for f in os.listdir(self.pdf_dir) if f.lower().endswith('.pdf')]
        logger.info(f"找到 {len(pdf_files)} 个PDF文件")
        
        for pdf_file in tqdm(pdf_files, desc="处理PDF"):
            pdf_path = os.path.join(self.pdf_dir, pdf_file)
            try:
                if self._detect_columns(pdf_path):
                    logger.info(f"处理双栏PDF: {pdf_file}")
                    text = self._process_double_column(pdf_path)
                else:
                    from langchain.document_loaders import PyMuPDFLoader
                    loader = PyMuPDFLoader(pdf_path)
                    text = loader.load()[0].page_content
                
                cleaned_text = self._clean_text(text)
                metadata = {'source': pdf_file, 'double_column': self._detect_columns(pdf_path)}
                splits = self.text_splitter.create_documents([cleaned_text], [metadata])
                documents.extend(splits)
                
            except Exception as e:
                logger.error(f"处理 {pdf_file} 失败: {str(e)}")
        
        logger.info(f"生成 {len(documents)} 个文本块")
        return documents
    
    def create_vector_db(self, documents):
        """创建向量数据库"""
        if not documents:
            logger.warning("无文档可处理，跳过向量库创建")
            return None
            
        logger.info("创建向量数据库...")
        vectordb = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_dir
        )
        vectordb.persist()
        logger.info(f"向量库已保存到 {self.persist_dir}")
        return vectordb
    
    def run(self):
        """运行完整流水线"""
        documents = self.process_pdfs()
        return self.create_vector_db(documents)

# 使用说明：
# 1. 手动下载模型到本地（如：https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2）
# 2. 将模型文件解压到指定路径（确保包含所有必要文件）
# 3. 修改下方的local_model_path为你的本地模型路径

if __name__ == "__main__":
    # 配置路径（请根据实际情况修改）
    pdf_directory = r"C:\Users\Lenovo\Desktop\lijing\神经网络\相关文本资料汇总"  # PDF目录
    vector_db_directory = "./public_art_vector_db"  # 向量库保存目录
    local_model_path = r"C:\Users\Lenovo\Desktop\Qwen\微调大模型\qwen-rag-lora\models\all-MiniLM-L6-v2"  # 本地模型路径
    
    # 初始化并运行
    try:
        pipeline = RAGPipeline(
            pdf_dir=pdf_directory,
            persist_dir=vector_db_directory,
            local_model_path=local_model_path  # 必须指定本地路径
        )
        vectordb = pipeline.run()
        
        # 测试检索
        if vectordb:
            query = "请根据你的文档内容提问"  # 替换为你的实际问题
            docs = vectordb.similarity_search(query, k=3)
            print("\n检索结果:")
            for i, doc in enumerate(docs):
                print(f"\n结果 {i+1}:")
                print(f"来源: {doc.metadata['source']}")
                print(f"内容: {doc.page_content[:200]}...")
    except Exception as e:
        logger.error(f"程序运行失败: {str(e)}", exc_info=True)