# 学术文献管理系统 - 模块初始化

__version__ = "1.0.0"
__author__ = "Academic RAG System"

# 导入主要模块
from . import pdf_processor
from . import vector_store
from . import llm
from . import agent
from .library_manager import get_library_manager, display_library_ui

__all__ = [
    "pdf_processor",
    "vector_store",
    "llm",
    "agent",
    "get_library_manager",
    "display_library_ui"
]