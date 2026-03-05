import streamlit as st
from langchain_community.llms import LlamaCpp
from config import LOCAL_LLM_PATH, LOCAL_LLM_N_CTX, LOCAL_LLM_N_THREADS

@st.cache_resource
def load_local_llm():
    """
    加载本地 GGUF 模型，使用缓存避免重复加载
    """
    try:
        llm = LlamaCpp(
            model_path=LOCAL_LLM_PATH,
            n_ctx=LOCAL_LLM_N_CTX,      # 上下文窗口
            n_batch=512,                # 批处理大小
            n_threads=LOCAL_LLM_N_THREADS, # 线程数
            verbose=False,              # 关闭日志
            temperature=0.7,            # 温度参数
            top_p=0.9,
            # 如果模型是 Chat 模型，可能需要指定 chat_format，一般 Qwen 指令模型默认即可
            # chat_format="chatml" 
        )
        st.success("✅ 本地模型加载成功")
        return llm
    except Exception as e:
        st.error(f"❌ 模型加载失败：{str(e)}")
        return None

def get_llm():
    return load_local_llm()