import streamlit as st
from bilibili_loader.core.bili_api_spider import BiliApiSpider
from bilibili_loader.utils.video_utils import merge_video
from bilibili_loader.app.state import StateManager as state
import os

def process_download():
    """处理视频下载和合并"""
    st.write("正在解析，请稍候...")

    # 获取 URL，确保不为空
    url = st.session_state.get("url", "")
    if not url:
        st.error("请输入有效的视频网址")
        return

    # 初始化爬虫对象
    bili_api_spider = BiliApiSpider(url=url)

    # 资源存储路径
    video_path = "bilibili_loader/cache/video/video.mp4"
    audio_path = "bilibili_loader/cache/audio/audio.m4a"

    # 下载视频和音频
    while not bili_api_spider.download_media(video_path, audio_path) and state.is_parsing():
        pass
    
    st.write("资源准备成功，开始整合。")

    try:
        output_path = "bilibili_loader/cache/output"
        output_name = bili_api_spider.name or "bilibili_video"  # 避免 output_name 为空
        output_file = merge_video(video_path, audio_path, output_path, output_name)

        if output_file and os.path.exists(output_file):
            st.session_state.is_downloaded = True
            st.session_state.is_parsing = False
            state.set_name(output_name)
            
            st.rerun()  # 重新运行 Streamlit 应用以更新下载按钮
            
        else:
            st.error("合并失败，文件未生成")
    except Exception as e:
        st.error(f"合并失败: {e}")
