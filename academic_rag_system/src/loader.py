import streamlit as st
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP

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