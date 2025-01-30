import streamlit as st
from bilibili_loader.core.bili_api_spider import BiliApiSpider
from bilibili_loader.utils.video_utils import merge_video
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
    while not bili_api_spider.download_media(video_path, audio_path):
        pass
    
    st.write("资源准备成功，开始整合。")

    try:
        output_path = "bilibili_loader/cache/output"
        output_name = bili_api_spider.name or "bilibili_video"  # 避免 output_name 为空
        output_file = merge_video(video_path, audio_path, output_path, output_name)

        if output_file and os.path.exists(output_file):
            st.success(f"合并完成: {output_name}.mp4")

            # 提供下载按钮
            with open(output_file, "rb") as f:
                st.download_button("下载视频", f, file_name=f"{output_name}.mp4", mime="video/mp4")

            # 更新状态
            st.session_state.is_downloaded = True
        else:
            st.error("融合失败，两股力量发生了排斥。")
    except Exception as e:
        st.error(f"融合失败，两股力量发生了排斥。")
