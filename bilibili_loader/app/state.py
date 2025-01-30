import streamlit as st
from bilibili_loader.utils.file_utils import remove_file

class StateManager:
    @staticmethod
    def init():
        """初始化 Streamlit 会话状态"""
        if "url" not in st.session_state:
            st.session_state.url = ""
        if "name" not in st.session_state:
            st.session_state.name = ""
        if "is_parsing" not in st.session_state:
            st.session_state.is_parsing = False
        if "is_downloaded" not in st.session_state:
            st.session_state.is_downloaded = False




    @staticmethod
    def set_url(url: str):
        """设置 URL"""
        st.session_state.url = url
        
    @staticmethod
    def set_name(name: str):
        """设置视频名称"""
        st.session_state.name = name

    def set_parsing(status: bool):
        """设置正在解析"""
        st.session_state.is_parsing = status
        
    @staticmethod
    def set_downloaded(status: bool):
        """设置已下载"""
        st.session_state.is_downloaded = status

    @staticmethod
    def start_parsing():
        """开始解析"""
        st.session_state.name = ""
        st.session_state.is_parsing = True
        st.session_state.is_downloaded = False
        
    @staticmethod
    def reset():
        """重置状态"""
        st.session_state.url = ""
        st.session_state.name = ""
        st.session_state.is_parsing = False
        st.session_state.is_downloaded = False
        st.rerun()
        
    @staticmethod
    def is_parsing() -> bool:
        """是否正在解析"""
        return st.session_state.is_parsing

    @staticmethod
    def is_downloaded() -> bool:
        """是否已下载"""
        return st.session_state.is_downloaded

    @staticmethod
    def with_url() -> bool:
        """是否有 URL"""
        return bool(st.session_state.url)
    
    @staticmethod
    def with_name() -> bool:
        """是否有视频名称"""
        return bool(st.session_state.name)
    
    @staticmethod
    def get_url() -> str:
        """获取 URL"""
        return st.session_state.url
    
    @staticmethod
    def get_name() -> str:
        """获取视频名称"""
        return st.session_state.name
    