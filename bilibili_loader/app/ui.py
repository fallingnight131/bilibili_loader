import streamlit as st
import bilibili_loader.app.state as state

def input_url():
    return st.text_input("请输入 Bilibili 视频的网址:", value=st.session_state.url, key="url_input")

def start_parsing_button():
    return st.button("开始解析")

def stop_parsing_button():
    return st.button("停止解析")

def render_buttons(url):
    """渲染解析和停止按钮"""
    col1, col2 = st.columns(2)
    with col1:
        if st.button("开始解析"):
            state.set_url(url)
            state.start_parsing()
    with col2:
        if st.button("停止解析"):
            state.reset()