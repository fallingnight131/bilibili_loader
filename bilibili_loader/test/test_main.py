import streamlit as st
import os
import sys

# 添加顶级包目录到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bilibili_loader.core.bili_api_spider import BiliApiSpider
from bilibili_loader.utils.video_utils import merge_video
import bilibili_loader.app.state as state
import bilibili_loader.app.ui as ui
import bilibili_loader.app.logic as logic


# Streamlit 应用标题
st.title("Bilibili 视频下载器")
st.write("输入 Bilibili 视频 URL，下载并合并视频和音频到本地。")

# **状态管理**
if "url" not in st.session_state:
    st.session_state.url = ""
if "is_parsing" not in st.session_state:
    st.session_state.is_parsing = False
if "is_downloaded" not in st.session_state:
    st.session_state.is_downloaded = False
    
# 重置状态函数
def reset_state():
    st.session_state.url = ""
    st.session_state.is_parsing = False
    st.session_state.is_downloaded = False
    st.rerun() # 重新运行脚本以更新界面

# 开始解析函数
def start_parsing():
    st.session_state.is_parsing = True
    st.session_state.is_downloaded = False  # 重置下载状态

# 输入框和按钮
url = st.text_input("请输入 Bilibili 视频的网址:", value=st.session_state.url, key="url_input")
col1, col2 = st.columns(2)
with col1:
    if st.button("开始解析"):
        st.session_state.url = url
        start_parsing()
with col2:
    if st.button("停止解析"):
        reset_state()

# **解析和下载逻辑**
if st.session_state.is_parsing and not st.session_state.is_downloaded and st.session_state.url:
    st.write("正在解析，请稍候...")

    bili_api_spider = BiliApiSpider(url=st.session_state.url)
    
    video_path = "bilibili_loader/cache/video/video.mp4"
    audio_path = "bilibili_loader/cache/audio/audio.m4a"
    
    if bili_api_spider.download_media(video_path, audio_path):
        st.write("资源准备成功，开始整合。")
        try:
            # 合并视频和音频
            output_path = "bilibili_loader/cache/output"
            output_name = bili_api_spider.name
            output_file = merge_video(video_path, audio_path, output_path, output_name)
            if output_file:
                st.success(f"合并完成: {output_name}.mp4")
                with open(output_file, "rb") as f:
                    st.download_button("下载视频", f, file_name=output_file)
                st.session_state.is_downloaded = True
            else:
                st.error("合并失败")
        except Exception as e:
            st.error(f"合并失败: {e}")
    else:
        st.error("资源准备失败")