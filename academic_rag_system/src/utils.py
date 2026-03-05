# h:\Coding\GDS\Intelligent-academic-literature-management-and-Q-A-agent-system-based-on-RAG-technology\academic_rag_system\src\utils.py

import streamlit as st
from datetime import datetime
import time

def auto_disappear_message(message, msg_type, duration=3000):
    """
    使用 JavaScript 实现的自动消失消息
    
    Args:
        message: 消息内容
        msg_type: 消息类型 ("info", "success", "warning", "error")
        duration: 持续时间（毫秒）
    """
    # 生成唯一的元素ID，避免冲突
    element_id = f"auto_msg_{datetime.now().timestamp() * 1000000:.0f}_{abs(hash(message)) % 10000}"
    
    # 根据消息类型选择相应的 HTML 和样式
    if msg_type == "success":
        msg_html = f"""<div id='{element_id}' class='auto-msg success' style='padding: 10px; margin: 5px 0; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; color: #155724;'>{message}</div>"""
    elif msg_type == "warning":
        msg_html = f"""<div id='{element_id}' class='auto-msg warning' style='padding: 10px; margin: 5px 0; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; color: #856404;'>{message}</div>"""
    elif msg_type == "error":
        msg_html = f"""<div id='{element_id}' class='auto-msg error' style='padding: 10px; margin: 5px 0; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; color: #721c24;'>{message}</div>"""
    else:  # info
        msg_html = f"""<div id='{element_id}' class='auto-msg info' style='padding: 10px; margin: 5px 0; background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 4px; color: #0c5460;'>{message}</div>"""
    
    # JavaScript 代码：在指定时间后隐藏消息
    js_code = f"""
    <script>
    setTimeout(function() {{
        var element = document.getElementById('{element_id}');
        if(element) {{
            element.style.display = 'none';
        }}
    }}, {duration});
    </script>
    """
    
    # 显示消息和JavaScript代码
    st.markdown(msg_html, unsafe_allow_html=True)
    st.markdown(js_code, unsafe_allow_html=True)

def auto_success(message, duration=3000):
    """便捷的成功消息函数"""
    auto_disappear_message(message, "success", duration)

def auto_warning(message, duration=3000):
    """便捷的警告消息函数"""
    auto_disappear_message(message, "warning", duration)

def auto_error(message, duration=3000):
    """便捷的错误消息函数"""
    auto_disappear_message(message, "error", duration)

def auto_info(message, duration=3000):
    """便捷的信息消息函数"""
    auto_disappear_message(message, "info", duration)

def auto_spinner(message, duration=3000):
    """自动消失的加载提示"""
    auto_disappear_message(f"⏳ {message}", "info", duration)