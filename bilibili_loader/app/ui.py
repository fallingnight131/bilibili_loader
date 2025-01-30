import streamlit as st
from bilibili_loader.app.state import StateManager as state

def input_url():
    """输入 Bilibili 视频 URL"""
    return st.text_input("请输入 Bilibili 视频的网址:", value=st.session_state.url, key="url_input")

def start_parsing_button():
    """开始解析按钮"""
    return st.button("开始解析", key="start_btn")

def stop_parsing_button():
    """停止解析按钮"""
    return st.button("停止解析", key="stop_btn")

def render_buttons(url):
    """渲染解析和停止按钮"""
    col1, col2 = st.columns(2)
    with col1:
        if start_parsing_button():
            state.set_url(url)
            state.start_parsing()
    with col2:
        if stop_parsing_button():
            state.reset()
