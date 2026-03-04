import os
import streamlit as st
# 解决 PyTorch 在 Windows 上与 Streamlit 的兼容性问题
os.environ["PYTORCH_JIT"] = "0"  # 禁用 JIT 编译
from src.loader import process_pdf, extract_pdf_metadata
from src.vector_store import init_qdrant_client, get_embedding_model, add_documents_to_qdrant
from src.agent import get_chat_engine
from src.library_manager import get_library_manager, display_library_ui


st.set_page_config(page_title="学术文献智能管理系统", layout="wide")

# 初始化 Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_engine" not in st.session_state:
    st.session_state.chat_engine = None
if "qdrant_client" not in st.session_state:
    st.session_state.qdrant_client = None
if "embedding_model" not in st.session_state:
    st.session_state.embedding_model = None

# 预加载关键组件（避免重复加载）
if "components_loaded" not in st.session_state:
    with st.spinner("🚀 正在初始化系统组件..."):
        # 预加载Qdrant客户端
        st.session_state.qdrant_client = init_qdrant_client()
        # 预加载Embedding模型（使用缓存）
        st.session_state.embedding_model = get_embedding_model()
        st.session_state.components_loaded = True
        st.success("✅ 系统初始化完成！")

# 侧边栏：文献上传、文献库管理
tab1, tab2 = st.sidebar.tabs(["📤 上传文献", "📚 文献库"])

with tab1:
    st.subheader("📤 上传 PDF 文献")
    uploaded_files = st.file_uploader("请在下面上传单个或多个PDF文件", type="pdf", accept_multiple_files=True)
    
    if st.button("🚀 导入并构建索引", type="primary"):
        if uploaded_files:
            with st.spinner("正在解析 PDF 并构建向量索引..."):
                try:
                    # 初始化组件
                    if st.session_state.qdrant_client is None:
                        st.session_state.qdrant_client = init_qdrant_client()
                        st.session_state.embedding_model = get_embedding_model()
                    
                    # 处理 PDF（增强版）
                    docs = process_pdf(uploaded_files)
                    
                    # 提取元数据并保存到文献库
                    library_manager = get_library_manager()
                    for uploaded_file in uploaded_files:
                        temp_path = f"./data/uploads/{uploaded_file.name}"
                        metadata = extract_pdf_metadata(temp_path, uploaded_file.name)
                        chunks_info = [{"chunk_id": i, "length": len(doc.page_content)} 
                                     for i, doc in enumerate(docs) 
                                     if doc.metadata.get("source") == uploaded_file.name]
                        library_manager.add_paper(metadata, chunks_info)
                    
                    # 存入 Qdrant
                    add_documents_to_qdrant(
                        st.session_state.qdrant_client,
                        docs,
                        st.session_state.embedding_model
                    )
                    
                    # 初始化问答引擎
                    st.session_state.chat_engine = get_chat_engine()
                    
                    # 不再设置临时状态标记，状态由数据库决定
                    
                    st.success("✅ 准备就绪！")
                    
                    # 显示分块预览
                    st.subheader("📊 文档分块预览")
                    total_chunks = len(docs)
                    avg_length = sum(len(doc.page_content) for doc in docs) / total_chunks
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("总文档块数", total_chunks)
                    with col2:
                        st.metric("平均长度", f"{avg_length:.0f} 字符")
                    with col3:
                        st.metric("处理文件", len(uploaded_files))
                    
                    # 显示前5个文档块预览
                    with st.expander("📝 查看前5个文档块"):
                        for i, doc in enumerate(docs[:5]):
                            st.write(f"**块 {i+1}** (来源: {doc.metadata.get('source', '未知')})")
                            st.text_area(f"内容预览", doc.page_content[:200] + "...", key=f"chunk_{i}")
                    
                except Exception as e:
                    error_msg = str(e)
                    st.error(f"❌ 错误：{error_msg}")
        else:
            st.warning("请先上传文件")

with tab2:
    # 显示文献库管理界面
    library_manager = get_library_manager()
    display_library_ui(library_manager)

# 在侧边栏顶部显示上传状态（基于数据库状态）
library_manager = get_library_manager()
stats = library_manager.get_paper_stats()

if stats["total_papers"] > 0:
    st.sidebar.success("✅ 文献已上传")
    st.sidebar.info(f"📚 已上传 {stats['total_papers']} 篇文献，{stats['total_chunks']} 个文档块")
else:
    st.sidebar.warning("⚠️ 请先上传文献")

# 主界面
st.title("💬 学术文献智能助手 (Qdrant + 本地模型)")
st.markdown("基于 **Qwen-4B** 本地大模型 + **Qdrant** 向量数据库，数据完全本地化。")

# 聊天历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("🔍 查看引用来源"):
                for i, source in enumerate(message["sources"]):
                    st.markdown(f"**片段 {i+1}:** {source.page_content[:200]}...")
                    st.caption(f"📄 {source.metadata.get('source')} | P{source.metadata.get('page')} | 相似度: {source.metadata.get('score', 0):.3f}")

# 用户输入
if prompt := st.chat_input("请输入关于文献的问题..."):
    # 检查是否已上传文件（基于数据库状态）
    library_manager = get_library_manager()
    stats = library_manager.get_paper_stats()
    #st.info(f"当前已上传 {stats['total_papers']} 篇文献，{stats['total_chunks']} 个文档块")
    if stats["total_papers"] == 0:
        st.warning("⚠️ 请先上传PDF文献并构建索引")
        st.info("请在左侧边栏的'上传文献'选项卡中上传文件")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if st.session_state.chat_engine:
                with st.spinner("正在检索文献并生成答案..."):
                    try:
                        response = st.session_state.chat_engine.invoke({"query": prompt})
                        content = response.get("result", "无法回答")
                        sources = response.get("source_documents", [])
                    
                        st.markdown(content)
                        if sources:
                            with st.expander("🔍 查看引用来源"):
                                for i, source in enumerate(sources):
                                    st.markdown(f"**片段 {i+1}:** {source.page_content[:200]}...")
                                    st.caption(f"📄 {source.metadata.get('source')} | P{source.metadata.get('page')} | 相似度: {source.metadata.get('score', 0):.3f}")
                        
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": content,
                            "sources": sources
                        })
                    except Exception as e:
                        st.error(f"发生错误：{str(e)}")
                        st.exception(e)
            else:
                st.warning("请先在左侧上传文献并构建索引。")