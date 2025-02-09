import streamlit as st
import uuid
import os
import time
import math
from bilibili_loader.core.bili_api_spider import BiliApiSpider
from bilibili_loader.app.state import StateManager as state
from bilibili_loader.utils.video_utils import merge_video
from bilibili_loader.utils.file_utils import remove_file, get_random_file, load_json


def process_download():
    """处理视频下载和合并"""
    progress_bar = st.progress(0)  # 创建一个进度条
    
    st.write("正在解析，请稍候...")
    
    # 生成唯一 ID
    unique_id = uuid.uuid4().hex  

    # 获取 URL，确保不为空
    url = st.session_state.get("url", "")
    if not url:
        st.error("请输入有效的视频网址")
        return

    # 初始化爬虫对象
    headers = load_json(get_random_file("src/bilibili_loader/config/headers"))
    bili_api_spider = BiliApiSpider(headers=headers,url=url)

    # 资源存储路径
    video_path = f"cache/video/video_{unique_id}.mp4"
    audio_path = f"cache/audio/audio_{unique_id}.m4a"

    progress_bar.progress(25)  # 更新进度条
    
    # 下载视频和音频
    # 开始时间
    start_time = time.time()
    download_state, error = bili_api_spider.download_media(video_path, audio_path)
    time_gap = time.time() - start_time
    
    while not download_state and not error and state.is_parsing() and time_gap < 300:
        download_state, error = bili_api_spider.download_media(video_path, audio_path)
        time_gap = time.time() - start_time
        if time_gap < 180:
            progress_bar.progress(25 + math.ceil(time_gap / 4))   # 更新进度条
        
    if download_state:
        st.write("资源准备成功，开始整合。")
        progress_bar.progress(70)  # 更新进度条
        try:
            output_path = "cache/output"
            output_name = bili_api_spider.name or "bilibili_video"  # 避免 output_name 为空
            output_file = merge_video(video_path, audio_path, output_path, output_name)

            if output_file and os.path.exists(output_file):
                state.set_downloaded(True)
                state.set_parsing(False)
                state.set_name(output_name)
                
                st.rerun()  # 重新运行 Streamlit 应用以更新下载按钮
            else:
                st.error("融合失败，两股力量发生了排斥！")
        except Exception:
            st.error(f"融合失败，受到未知力量干扰！")
    elif not download_state and not error:
        st.error("道中偶遇耐抓视频，拼尽全力无法战胜。")
    else:
        st.error(f"下载失败: {error}")
        
    # 删除视频和音频文件
    remove_file(video_path)
    remove_file(audio_path)