#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
from pathlib import Path
from langchain.embeddings import OllamaEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredExcelLoader,
    CSVLoader
)
from langchain.schema import Document

# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('VectorDB_Builder')

def get_project_root():
    """获取项目根目录"""
    return Path(__file__).parent

def load_json_qa_files(directory_path):
    """加载JSON格式的问答对文件"""
    documents = []
    directory = Path(directory_path)
    
    if not directory.exists():
        logger.warning(f"目录不存在: {directory_path}")
        return documents
    
    # 遍历所有JSON文件
    for file_path in directory.glob("*.json"):
        try:
            logger.info(f"正在加载JSON文件: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 处理Alpaca格式的数据
            if isinstance(data, dict):
                # 单个问答对
                if 'instruction' in data and 'input' in data and 'output' in data:
                    # 构建文档内容
                    content = f"问题：{data['instruction']}\n"
                    if data.get('input'):
                        content += f"输入：{data['input']}\n"
                    content += f"回答：{data['output']}"
                    
                    doc = Document(
                        page_content=content,
                        metadata={
                            'source': str(file_path),
                            'directory': directory.name,
                            'type': 'qa_pair',
                            'instruction': data['instruction']
                        }
                    )
                    documents.append(doc)
            
            elif isinstance(data, list):
                # 多个问答对
                for item in data:
                    if isinstance(item, dict) and 'instruction' in item and 'output' in item:
                        content = f"问题：{item['instruction']}\n"
                        if item.get('input'):
                            content += f"输入：{item['input']}\n"
                        content += f"回答：{item['output']}"
                        
                        doc = Document(
                            page_content=content,
                            metadata={
                                'source': str(file_path),
                                'directory': directory.name,
                                'type': 'qa_pair',
                                'instruction': item['instruction']
                            }
                        )
                        documents.append(doc)
            
            logger.info(f"成功加载 {len(documents)} 个问答对")
            
        except Exception as e:
            logger.error(f"加载JSON文件失败 {file_path}: {e}")
            continue
    
    return documents

def load_documents_from_directory(directory_path):
    """从目录加载所有文档"""
    documents = []
    directory = Path(directory_path)
    
    if not directory.exists():
        logger.warning(f"目录不存在: {directory_path}")
        return documents
    
    # 支持的文件扩展名
    supported_extensions = {
        '.pdf': PyPDFLoader,
        '.txt': TextLoader,
        '.doc': UnstructuredWordDocumentLoader,
        '.docx': UnstructuredWordDocumentLoader,
        '.xls': UnstructuredExcelLoader,
        '.xlsx': UnstructuredExcelLoader,
        '.csv': CSVLoader
    }
    
    # 遍历目录中的所有文件
    for file_path in directory.rglob('*'):
        if file_path.is_file():
            if file_path.suffix.lower() == '.json':
                # 处理JSON文件
                json_docs = load_json_qa_files(file_path.parent)
                documents.extend(json_docs)
                break  # 避免重复处理
            elif file_path.suffix.lower() in supported_extensions:
                try:
                    logger.info(f"正在加载文件: {file_path}")
                    
                    # 根据文件类型选择加载器
                    loader_class = supported_extensions[file_path.suffix.lower()]
                    
                    if file_path.suffix.lower() == '.txt':
                        # 文本文件需要指定编码
                        loader = loader_class(str(file_path), encoding='utf-8')
                    else:
                        loader = loader_class(str(file_path))
                    
                    # 加载文档
                    docs = loader.load()
                    
                    # 为每个文档添加源文件信息
                    for doc in docs:
                        doc.metadata['source'] = str(file_path)
                        doc.metadata['directory'] = directory.name
                    
                    documents.extend(docs)
                    logger.info(f"成功加载 {len(docs)} 个文档片段")
                    
                except Exception as e:
                    logger.error(f"加载文件失败 {file_path}: {e}")
                    continue
    
    return documents

def split_documents(documents, chunk_size=1000, chunk_overlap=200):
    """分割文档为小块"""
    logger.info(f"开始分割 {len(documents)} 个文档...")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
    )
    
    split_docs = text_splitter.split_documents(documents)
    logger.info(f"文档分割完成，共 {len(split_docs)} 个片段")
    
    return split_docs

def build_vector_database():
    """构建向量数据库"""
    project_root = get_project_root()
    
    # 知识库目录
    qa_directory = project_root / "knowledge_base" / "问答对"
    text_directory = project_root / "knowledge_base" / "相关文本资料汇总"
    
    # 向量数据库目录
    db_directory = project_root / "chroma_db_deepseek_1.5b"
    
    logger.info("开始构建向量数据库...")
    logger.info(f"问答对目录: {qa_directory}")
    logger.info(f"文本资料目录: {text_directory}")
    logger.info(f"数据库目录: {db_directory}")
    
    # 1. 删除旧的数据库
    if db_directory.exists():
        logger.info("删除旧的向量数据库...")
        import shutil
        shutil.rmtree(db_directory)
    
    # 2. 加载文档
    logger.info("加载问答对文档...")
    qa_documents = load_json_qa_files(qa_directory)
    
    logger.info("加载文本资料文档...")
    text_documents = load_documents_from_directory(text_directory)
    
    all_documents = qa_documents + text_documents
    logger.info(f"总共加载了 {len(all_documents)} 个文档")
    
    if not all_documents:
        logger.error("没有找到任何文档，请检查知识库目录")
        return False
    
    # 3. 分割文档
    split_docs = split_documents(all_documents)
    
    # 4. 初始化嵌入模型
    logger.info("初始化嵌入模型...")
    try:
        embeddings = OllamaEmbeddings(model="deepseek-r1:1.5b")
        logger.info("嵌入模型初始化成功")
    except Exception as e:
        logger.error(f"嵌入模型初始化失败: {e}")
        logger.error("请确保Ollama服务正在运行，并已安装deepseek-r1:1.5b模型")
        return False
    
    # 5. 创建向量数据库
    logger.info("创建向量数据库...")
    try:
        vector_store = Chroma.from_documents(
            documents=split_docs,
            embedding=embeddings,
            persist_directory=str(db_directory),
            collection_name="academic_papers_deepseek_1.5b"
        )
        
        # 持久化数据库
        vector_store.persist()
        
        # 获取文档数量
        doc_count = vector_store._collection.count()
        logger.info(f"向量数据库创建成功！包含 {doc_count} 个文档片段")
        
        return True
        
    except Exception as e:
        logger.error(f"创建向量数据库失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("公共艺术RAG系统 - 向量数据库重建工具")
    logger.info("=" * 60)
    
    # 检查Ollama
    try:
        import subprocess
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if "deepseek-r1:1.5b" not in result.stdout:
            logger.error("未找到deepseek-r1:1.5b模型")
            logger.info("请运行: ollama pull deepseek-r1:1.5b")
            return
    except Exception as e:
        logger.error(f"检查Ollama失败: {e}")
        logger.error("请确保Ollama已安装并正在运行")
        return
    
    # 构建数据库
    success = build_vector_database()
    
    if success:
        logger.info("=" * 60)
        logger.info("✅ 向量数据库重建完成！")
        logger.info("现在可以启动后端服务了")
        logger.info("=" * 60)
    else:
        logger.error("❌ 向量数据库重建失败")
        logger.error("请检查错误信息并重试")

if __name__ == "__main__":
    main() 