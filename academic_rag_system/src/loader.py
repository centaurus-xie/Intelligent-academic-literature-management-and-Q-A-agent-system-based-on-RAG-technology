import streamlit as st
import fitz  # PyMuPDF
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP
import re
import os
from datetime import datetime


def extract_pdf_metadata(file_path, file_name):
    """
    提取PDF文件的详细元数据
    """
    metadata = {
        "file_name": file_name,
        "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "title": "",
        "author": "",
        "abstract": "",
        "year": "",
        "keywords": [],
        "sections": [],
        "page_count": 0,
        "file_size": 0,
        "DOI": ""
    }
    
    try:
        doc = fitz.open(file_path)
        metadata["page_count"] = len(doc)
        metadata["file_size"] = os.path.getsize(file_path)
        
        # 提取PDF内置元数据
        pdf_metadata = doc.metadata
        if pdf_metadata:
            metadata["title"] = pdf_metadata.get("title", "")
            metadata["author"] = pdf_metadata.get("author", "")
            #metadata["year"] = pdf_metadata.get("creationDate", "").split(" ")[0][2:]
            metadata["DOI"] = pdf_metadata.get("doi", "")

        # 若无法读取内置元数据，尝试从第一页文本提取
        if metadata["title"] == "Unknown":
            first_page = doc[0].get_text()
            lines = first_page.split('\n')
            if lines:
                metadata["title"] = lines[0].strip()[:100]  # 假设第一行是标题
            
            # 提取年份（4 位数字）
            year_match = re.search(r'\b(19|20)\d{2}\b', first_page)
            if year_match:
                metadata["year"] = year_match.group()

        # 智能识别章节结构（简单实现）
        sections = []
        for page_num in range(min(3, len(doc))):  # 只分析前3页
            page = doc[page_num]
            text = page.get_text()
            
            # 识别章节标题（以数字开头的大写标题）
            section_pattern = r'\n(\d+\.\d*\s+[A-Z][^\n]{5,50})\n'
            matches = re.findall(section_pattern, text)
            sections.extend(matches)
        
        metadata["sections"] = sections[:10]  # 最多显示10个章节
        
        doc.close()
        
    except Exception as e:
        st.warning(f"元数据提取失败: {e}")
    
    return metadata

def process_pdf(uploaded_files):
    """
    处理上传的 PDF 文件，解析并分块
    参数：
        uploaded_files: Streamlit 上传的文件列表
    返回：
        docs: 文档块列表
    """
    all_docs = []
    
    for uploaded_file in uploaded_files:
        try:
            # 保存临时文件 (PyMuPDFLoader 需要文件路径)
            temp_path = f"./data/uploads/{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 加载 PDF
            loader = PyMuPDFLoader(temp_path)
            docs = loader.load()
            
            # 添加文件名到元数据
            for doc in docs:
                doc.metadata["source"] = uploaded_file.name
            
            # 文本分块
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                length_function=len,
                separators=["\n\n", "\n", "。", "!", "!", "?", "？", " ", ""]
            )
            split_docs = text_splitter.split_documents(docs)
            
            all_docs.extend(split_docs)
            
        except Exception as e:
            st.error(f"处理文件 {uploaded_file.name} 时出错：{str(e)}")
    
    return all_docs