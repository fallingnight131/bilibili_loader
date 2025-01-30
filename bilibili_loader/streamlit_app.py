import streamlit as st
import os
import sys

# 添加根目录到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bilibili_loader.app.state as state
import bilibili_loader.app.ui as ui
import bilibili_loader.app.logic as logic

# 初始化 Streamlit 应用状态
state.init()

# Streamlit 应用标题
st.title("Bilibili 视频下载器")
st.write("输入 Bilibili 视频 URL，下载并合并视频和音频到本地。")

# 输入框和按钮
url = ui.input_url()

# 解析和下载按钮
ui.render_buttons(url)

# 解析和下载逻辑
if state.is_parsing() and not state.is_downloaded() and state.get_url():
    logic.process_download()