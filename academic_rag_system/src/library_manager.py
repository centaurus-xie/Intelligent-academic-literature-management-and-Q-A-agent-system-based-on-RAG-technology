import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path

class LibraryManager:
    """
    文献库管理类
    负责文献的存储、检索和管理
    """
    
    def __init__(self, db_path="./data/library.json"):
        self.db_path = db_path
        self.library_data = self._load_library()
    
    def _load_library(self):
        """加载文献库数据"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 确保数据格式正确
                if "papers" not in data:
                    data["papers"] = []
                if "last_updated" not in data:
                    data["last_updated"] = datetime.now().isoformat()
                    
                # 确保所有论文都有正确的元数据结构
                for paper in data.get("papers", []):
                    if "metadata" not in paper:
                        paper["metadata"] = {}
                    if "chunks_info" not in paper:
                        paper["chunks_info"] = []
                    if "status" not in paper:
                        paper["status"] = "active"
                    
                return data
            except Exception as e:
                print(f"加载文献库失败: {e}")
                return {"papers": [], "last_updated": datetime.now().isoformat()}
        else:
            return {"papers": [], "last_updated": datetime.now().isoformat()}
    
    def _save_library(self):
        """保存文献库数据"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.library_data, f, ensure_ascii=False, indent=2)
    
    def add_paper(self, metadata, chunks_info):
        """添加文献到库中"""
        paper_data = {
            "id": len(self.library_data["papers"]) + 1,
            "metadata": metadata,
            "chunks_info": chunks_info,
            "added_time": datetime.now().isoformat(),
            "status": "active"
        }
        
        self.library_data["papers"].append(paper_data)
        self.library_data["last_updated"] = datetime.now().isoformat()
        self._save_library()
        
        return paper_data["id"]
    
    def get_all_papers(self):
        """获取所有文献"""
        return [p for p in self.library_data["papers"] if p["status"] == "active"]
    
    def search_papers(self, query):
        """搜索文献"""
        results = []
        for paper in self.library_data["papers"]:
            if paper["status"] != "active":
                continue
                
            # 在标题、作者、文件名中搜索
            metadata = paper.get("metadata", {})
            search_fields = [
                metadata.get("title", ""),
                metadata.get("author", ""),
                metadata.get("original_filename", ""),  # 修复：使用正确的字段名
                metadata.get("file_name", "")  # 保持兼容性
            ]
            
            if any(query.lower() in field.lower() for field in search_fields if field):
                results.append(paper)
        
        return results
    
    def delete_paper(self, paper_id):
        """删除文献（软删除）"""
        for paper in self.library_data["papers"]:
            if paper["id"] == paper_id:
                paper["status"] = "deleted"
                paper["deleted_time"] = datetime.now().isoformat()
                self._save_library()
                return True
        return False
    
    def get_paper_stats(self):
        """获取文献库统计信息"""
        active_papers = self.get_all_papers()
        total_chunks = sum(len(p["chunks_info"]) for p in active_papers)
        
        return {
            "total_papers": len(active_papers),
            "total_chunks": total_chunks,
            "last_updated": self.library_data["last_updated"]
        }

def display_library_ui(library_manager):
    """显示文献库管理界面"""
    st.subheader("📚 文献库管理")
    
    # 搜索框
    search_query = st.text_input("🔍 搜索文献", placeholder="输入标题、作者或文件名...")
    
    # 获取文献列表
    if search_query:
        papers = library_manager.search_papers(search_query)
    else:
        papers = library_manager.get_all_papers()
    
    # 显示统计信息
    stats = library_manager.get_paper_stats()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("文献数量", stats["total_papers"])
    with col2:
        st.metric("文档块数", stats["total_chunks"])
    with col3:
        st.metric("最后更新", stats["last_updated"][:10])
    
    # 文献列表
    if papers:
        st.write(f"### 找到 {len(papers)} 篇文献")
        
        for paper in papers:
            # 安全获取标题，优先使用title，否则使用original_filename
            title = paper['metadata'].get('title', paper['metadata'].get('original_filename', '未知文献'))
            with st.expander(f"📄 {title}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**作者:** {paper['metadata'].get('author', '未知')}")
                    # 安全获取文件名
                    filename = paper['metadata'].get('original_filename', paper['metadata'].get('file_name', '未知文件'))
                    st.write(f"**文件名:** {filename}")
                    st.write(f"**页数:** {paper['metadata'].get('pages', paper['metadata'].get('page_count', 0))}")
                    st.write(f"**章节数:** {len(paper['metadata'].get('sections', []))}")
                    st.write(f"**文档块数:** {len(paper['chunks_info'])}")
                    st.write(f"**添加时间:** {paper.get('added_time', '未知')[:19] if paper.get('added_time') else '未知'}")
                
                with col2:
                    if st.button("🗑️ 删除", key=f"delete_{paper['id']}"):
                        if library_manager.delete_paper(paper['id']):
                            st.success("文献已删除")
                            st.rerun()
    else:
        st.info("📝 文献库为空，请先上传文献")

# 全局文献库管理器实例
_library_manager = None

def get_library_manager():
    """获取文献库管理器实例"""
    global _library_manager
    if _library_manager is None:
        _library_manager = LibraryManager()
    return _library_manager