#!/usr/bin/env python3
"""
Qdrant数据库查看工具
用于查看app.py中使用的向量数据库内容
"""
import streamlit as st
from qdrant_client import QdrantClient
from config import QDRANT_COLLECTION_NAME, QDRANT_PERSIST_PATH
import pandas as pd

st.title("🔍 Qdrant 向量数据库查看器")

try:
    # 连接到Qdrant（使用app.py中的相同配置）
    client = QdrantClient(path=QDRANT_PERSIST_PATH)
    
    # 获取集合信息
    collection_info = client.get_collection(QDRANT_COLLECTION_NAME)
    
    # 显示集合概览
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("文档总数", collection_info.points_count)
    with col2:
        st.metric("向量维度", collection_info.config.params.vectors.size)
    with col3:
        st.metric("距离类型", collection_info.config.params.vectors.distance)
    
    # 分页显示文档
    st.subheader("📖 文档列表")
    limit = st.slider("每页显示数量", 5, 50, 10)
    
    # 计算总页数
    total_points = collection_info.points_count
    total_pages = (total_points + limit - 1) // limit
    
    page = st.number_input("页码", 1, total_pages, 1)
    offset = (page - 1) * limit
    
    # 获取文档
    points = client.scroll(
        collection_name=QDRANT_COLLECTION_NAME,
        limit=limit,
        offset=offset,
        with_payload=True,
        with_vectors=False
    )[0]
    
    # 创建DataFrame显示
    data = []
    for i, point in enumerate(points):
        data.append({
            "ID": point.id,
            "来源": point.payload.get('source', '未知'),
            "页码": point.payload.get('page', 0),
            "内容预览": point.payload.get('content', '')[:200] + "...",
            "文档ID": point.payload.get('doc_id', 0)
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    
    # 显示详细信息
    if st.checkbox("显示详细信息"):
        for i, point in enumerate(points):
            with st.expander(f"详细信息 - {point.payload.get('source', '未知')} (ID: {point.id})"):
                st.write(f"**来源**: {point.payload.get('source', '未知')}")
                st.write(f"**页码**: {point.payload.get('page', 0)}")
                st.write(f"**文档ID**: {point.payload.get('doc_id', 0)}")
                st.write(f"**内容**: {point.payload.get('content', '')}")
    
    st.success(f"✅ 显示 {len(points)} 个文档片段 (第 {page}/{total_pages} 页)")
    
except Exception as e:
    st.error(f"❌ 数据库连接失败: {e}")
    st.info("请确保已上传文献并构建了向量索引")