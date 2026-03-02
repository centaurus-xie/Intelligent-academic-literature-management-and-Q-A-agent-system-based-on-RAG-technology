import os
import streamlit as st
# 解决 PyTorch 在 Windows 上与 Streamlit 的兼容性问题
os.environ["PYTORCH_JIT"] = "0"  # 禁用 JIT 编译
from src.loader import process_pdf
from src.vector_store import init_qdrant_client, get_embedding_model, add_documents_to_qdrant
from src.agent import get_chat_engine

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

# 侧边栏
with st.sidebar:
    st.title("📚 文献库管理")
    uploaded_files = st.file_uploader("上传 PDF 文献", type="pdf", accept_multiple_files=True)
    
    if st.button("🚀 导入并构建索引", type="primary"):
        if uploaded_files:
            # 创建进度显示区域
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # 步骤1: 初始化组件 (20%)
                status_text.text("🔄 初始化组件...")
                if st.session_state.qdrant_client is None:
                    st.session_state.qdrant_client = init_qdrant_client()
                    st.session_state.embedding_model = get_embedding_model()
                progress_bar.progress(0.2)
                
                # 步骤2: 解析 PDF (40%)
                status_text.text("📄 解析 PDF 文件...")
                docs = process_pdf(uploaded_files)
                progress_bar.progress(0.4)
                
                # 步骤3: 向量化处理 (70%)
                status_text.text("🔢 生成向量嵌入...")
                add_documents_to_qdrant(
                    st.session_state.qdrant_client,
                    docs,
                    st.session_state.embedding_model
                )
                progress_bar.progress(0.7)
                
                # 步骤4: 初始化问答引擎 (90%)
                status_text.text("🤖 初始化问答引擎...")
                st.session_state.chat_engine = get_chat_engine()
                progress_bar.progress(0.9)
                
                # 完成 (100%)
                status_text.text("✅ 准备就绪！")
                progress_bar.progress(1.0)
                
                st.success(f"✅ 成功导入 {len(uploaded_files)} 个文件，生成 {len(docs)} 个文档块")
                
            except Exception as e:
                status_text.text("❌ 处理失败")
                st.error(f"❌ 错误：{str(e)}")
                st.exception(e)  # 显示完整堆栈便于调试
        else:
            st.warning("请先上传文件")

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