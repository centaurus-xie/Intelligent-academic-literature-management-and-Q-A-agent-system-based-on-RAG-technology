from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import BaseRetriever
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from typing import Any
from src.llm import get_llm
from src.vector_store import init_qdrant_client, get_embedding_model, search_qdrant

def get_chat_engine():
    """
    初始化问答引擎（使用 Qdrant 检索）
    """
    import streamlit as st
    
    # 1. 加载LLM模型
    llm = get_llm()
    if not llm:
        st.error("❌ LLM模型加载失败")
        return None
    else:
        st.success("✅ LLM模型加载成功")
    
    # 2. 初始化Qdrant客户端
    try:
        client = init_qdrant_client()
        st.success("✅ Qdrant客户端初始化成功")
    except Exception as e:
        st.error(f"❌ Qdrant客户端初始化失败: {e}")
        return None
    
    # 3. 加载Embedding模型
    try:
        embedding_model = get_embedding_model()
        st.success("✅ Embedding模型加载成功")
    except Exception as e:
        st.error(f"❌ Embedding模型加载失败: {e}")
        return None
    
    # 自定义 Prompt
    template = """你是一个专业的学术助手。请严格根据提供的【上下文】回答【问题】。
    要求：
    1. 如果【上下文】中没有答案，请直接回答"文献中未提及相关信息"，不要编造。
    2. 回答要简洁、准确，尽量引用原文数据。
    3. 不要输出与问题无关的寒暄语。

    【上下文】：
    {context}

    【问题】：
    {question}

    【回答】：
    """
    
    prompt = PromptTemplate(template=template, input_variables=["context", "question"])
    
    # 创建简单的检索函数（避免复杂的类继承）
    def qdrant_retriever_func(query: str) -> list[Document]:
        """Qdrant 检索函数"""
        return search_qdrant(client, query, embedding_model)
    
    # 创建兼容 LangChain 的检索器包装
    class SimpleQdrantRetriever(BaseRetriever):
        """简单的 Qdrant 检索器包装"""
        
        def _get_relevant_documents(self, query: str) -> list[Document]:
            return qdrant_retriever_func(query)
        
        async def _aget_relevant_documents(self, query: str) -> list[Document]:
            return self._get_relevant_documents(query)
    
    # 创建检索器实例
    simple_retriever = SimpleQdrantRetriever()
    
    # 创建 QA 链
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=simple_retriever,  # 使用简单的检索器
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )
    
    return qa_chain