"""
PDF处理核心模块
实现完整的PDF解析流程：版面分析 -> 元素提取 -> 多模态解析 -> 文本融合
"""
import streamlit as st
import fitz  # PyMuPDF
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP
from .layout_analyzer import LayoutAnalyzer
from .element_extractor import ElementExtractor
from .multimodal_parser import MultimodalParser
import tempfile
import os
from typing import List, Dict, Any
from datetime import datetime

class PDFProcessor:
    """PDF处理器主类"""
    
    def __init__(self):
        self.layout_analyzer = LayoutAnalyzer()
        self.element_extractor = ElementExtractor()
        self.multimodal_parser = MultimodalParser()
    
    def process_pdf(self, uploaded_files) -> List[Document]:
        """
        处理上传的PDF文件
        实现完整的处理流程
        """
        all_docs = []
        
        for uploaded_file in uploaded_files:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_file.getbuffer())
                    temp_path = tmp_file.name
                
                # 使用fitz打开PDF进行版面分析
                doc = fitz.open(temp_path)
                
                for page_num in range(len(doc)):
                    # 1. 版面分析
                    layout_elements = self.layout_analyzer.analyze_page(doc, page_num)
                    
                    # 2. 元素提取
                    extracted_elements = self.element_extractor.extract_elements(
                        doc, page_num, layout_elements
                    )
                    
                    # 3. 多模态解析
                    processed_content = self.multimodal_parser.parse_elements(extracted_elements)
                    
                    # 4. 生成文档块
                    page_content = self._build_page_content(processed_content)
                    
                    doc_chunk = Document(
                        page_content=page_content,
                        metadata={
                            "source": uploaded_file.name,
                            "page": page_num + 1,
                            "processed_elements": processed_content
                        }
                    )
                    all_docs.append(doc_chunk)
                
                doc.close()
                os.unlink(temp_path)
                
            except Exception as e:
                st.error(f"处理文件 {uploaded_file.name} 时出错：{str(e)}")
        
        # 5. 文本分块
        return self._split_documents(all_docs)
    
    def _build_page_content(self, processed_content: Dict[str, Any]) -> str:
        """构建页面内容字符串"""
        content_parts = []
        
        # 添加文本内容
        if 'text' in processed_content:
            content_parts.append(processed_content['text'])
        
        # 添加公式内容
        if 'formulas' in processed_content:
            for formula in processed_content['formulas']:
                content_parts.append(f"[FORMULA: {formula['content']}]")
        
        # 添加表格内容
        if 'tables' in processed_content:
            for table in processed_content['tables']:
                content_parts.append(f"[TABLE: {table['content']}]")
        
        # 添加图片描述
        if 'images' in processed_content:
            for img in processed_content['images']:
                content_parts.append(f"[IMAGE: {img['description']}]")
        
        return '\n'.join(content_parts)
    
    def _split_documents(self, docs: List[Document]) -> List[Document]:
        """分割文档"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", "。", "!", "!", "?", "？", " ", ""]
        )
        return text_splitter.split_documents(docs)

def extract_pdf_metadata(file_path, original_filename):
    """提取PDF元数据"""
    try:
        doc = fitz.open(file_path)
        metadata = doc.metadata
        
        # 构建元数据字典
        paper_metadata = {
            "title": metadata.get("title", original_filename.replace(".pdf", "")),
            "author": metadata.get("author", "Unknown"),
            "subject": metadata.get("subject", ""),
            "keywords": metadata.get("keywords", ""),
            "producer": metadata.get("producer", ""),
            "creation_date": metadata.get("creationDate", ""),
            "modification_date": metadata.get("modDate", ""),
            "pages": doc.page_count,
            "original_filename": original_filename,
            "file_size": os.path.getsize(file_path),
            "added_date": datetime.now().isoformat()
        }
        
        doc.close()
        return paper_metadata
    except Exception as e:
        print(f"提取PDF元数据失败: {e}")
        return {
            "title": original_filename.replace(".pdf", ""),
            "author": "Unknown",
            "pages": 0,
            "original_filename": original_filename,
            "added_date": datetime.now().isoformat()
        }



# 全局PDF处理器实例
_pdf_processor = None

def process_pdf(uploaded_files):
    """处理PDF文件的统一接口"""
    global _pdf_processor
    if _pdf_processor is None:
        _pdf_processor = PDFProcessor()
    return _pdf_processor.process_pdf(uploaded_files)