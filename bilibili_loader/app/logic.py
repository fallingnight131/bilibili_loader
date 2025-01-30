import streamlit as st
from bilibili_loader.core.bili_api_spider import BiliApiSpider
from bilibili_loader.utils.video_utils import merge_video

def process_download():
    st.write("正在解析，请稍候...")
    url = st.session_state.url
    bili_api_spider = BiliApiSpider(url=url)

    video_path = "bilibili_loader/cache/video/video.mp4"
    audio_path = "bilibili_loader/cache/audio/audio.m4a"

    if bili_api_spider.download_media(video_path, audio_path):
        st.write("资源准备成功，开始整合。")
        try:
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