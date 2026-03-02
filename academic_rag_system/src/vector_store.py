import os
import streamlit as st
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_community.embeddings import HuggingFaceEmbeddings
from config import (
    EMBEDDING_MODEL_NAME,
    QDRANT_COLLECTION_NAME,
    QDRANT_VECTOR_SIZE,
    QDRANT_PERSIST_PATH
)

@st.cache_resource
def get_embedding_model():
    """
    缓存 Embedding 模型，避免重复加载
    """
    # 环境变量已在 config.py 中设置
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={
            'device': 'cpu',
            'trust_remote_code': True
        },
        encode_kwargs={'normalize_embeddings': True}  # Qdrant 需要归一化向量
    )

@st.cache_resource
def init_qdrant_client():
    """
    初始化 Qdrant 客户端（本地持久化模式，无需 Docker）
    """
    client = QdrantClient(path=QDRANT_PERSIST_PATH)
    
    # 检查 collection 是否存在
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]
    
    if QDRANT_COLLECTION_NAME not in collection_names:
        # 创建 collection
        client.create_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=QDRANT_VECTOR_SIZE,
                distance=models.Distance.COSINE  # 余弦相似度
            ),
            # 添加元数据字段索引，支持过滤
            optimizers_config=models.OptimizersConfigDiff(
                default_segment_number=2,
                memmap_threshold=20000  # 内存优化
            )
        )
        st.success(f"✅ Qdrant 集合 '{QDRANT_COLLECTION_NAME}' 创建成功")
    
    return client

def add_documents_to_qdrant(client, docs, embedding_model):
    """
    将文档添加到 Qdrant，包含去重机制
    """
    from uuid import uuid4
    import hashlib
    
    points = []
    existing_hashes = set()
    
    # 获取已存在的文档哈希（简单去重）
    try:
        existing_points = client.scroll(
            collection_name=QDRANT_COLLECTION_NAME,
            limit=1000,
            with_payload=True
        )[0]
        existing_hashes = {point.payload.get("content_hash", "") for point in existing_points}
    except:
        pass
    
    for i, doc in enumerate(docs):
        # 生成内容哈希用于去重
        content_hash = hashlib.md5(doc.page_content.encode()).hexdigest()
        
        # 跳过已存在的文档
        if content_hash in existing_hashes:
            continue
        
        # 生成向量
        vector = embedding_model.embed_query(doc.page_content)
        
        # 构建 payload（元数据）
        payload = {
            "content": doc.page_content,
            "source": doc.metadata.get("source", "unknown"),
            "page": doc.metadata.get("page", 0),
            "doc_id": i,
            "content_hash": content_hash,  # 用于去重
            "chunk_index": i
        }
        
        # 构建 point
        point = models.PointStruct(
            id=str(uuid4()),  # Qdrant 需要 string 或 int 类型的 ID
            vector=vector,
            payload=payload
        )
        points.append(point)
    
    # 批量上传
    if points:
        client.upsert(
            collection_name=QDRANT_COLLECTION_NAME,
            points=points,
            wait=True
        )
        st.success(f"✅ 成功导入 {len(points)} 个文档块")

def search_qdrant(client, query, embedding_model, top_k=3):
    """
    从 Qdrant 检索相关文档
    """
    # 生成查询向量
    query_vector = embedding_model.embed_query(query)
    
    # 执行搜索
    hits = client.search(
        collection_name=QDRANT_COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True  # 返回元数据
    )
    
    # 转换为 LangChain 格式（兼容后续处理）
    from langchain_core.documents import Document
    results = []
    for hit in hits:
        doc = Document(
            page_content=hit.payload.get("content", ""),
            metadata={
                "source": hit.payload.get("source", ""),
                "page": hit.payload.get("page", 0),
                "score": hit.score
            }
        )
        results.append(doc)
    
    return results

def get_retriever(client, embedding_model):
    """
    返回一个可调用检索函数（兼容 LangChain 接口）
    """
    def retriever_func(query):
        return search_qdrant(client, query, embedding_model)
    return retriever_func