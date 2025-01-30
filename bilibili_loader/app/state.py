import streamlit as st

class StateManager:
    @staticmethod
    def init():
        """初始化 Streamlit 会话状态"""
        if "url" not in st.session_state:
            st.session_state.url = ""
        if "is_parsing" not in st.session_state:
            st.session_state.is_parsing = False
        if "is_downloaded" not in st.session_state:
            st.session_state.is_downloaded = False

    @staticmethod
    def set_url(url: str):
        """设置 URL"""
        st.session_state.url = url

    @staticmethod
    def start_parsing():
        """开始解析"""
        st.session_state.is_parsing = True
        st.session_state.is_downloaded = False

    @staticmethod
    def reset():
        """重置状态"""
        st.session_state.url = ""
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

