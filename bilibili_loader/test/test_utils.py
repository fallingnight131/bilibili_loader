import streamlit as st
import time

st.title("进度条示例")

progress_bar = st.progress(0)  # 创建一个进度条
status_text = st.empty()  # 用于显示状态文本

for percent in range(101):
    time.sleep(0.05)  # 模拟耗时任务
    progress_bar.progress(percent)  # 更新进度条
    status_text.text(f"进度: {percent}%")

st.success("任务完成！")
