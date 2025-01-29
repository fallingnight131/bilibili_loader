import streamlit as st
import requests
import os
import sys
from moviepy.editor import VideoFileClip, AudioFileClip

# 添加顶级包目录到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bilibili_loader.core.bili_web_scraper import BiliWebScraper


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


def download_file(url, filename):
    """下载文件的通用函数。"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"下载失败: {e}")
    return False

# **解析和下载逻辑**
if st.session_state.is_parsing and not st.session_state.is_downloaded and st.session_state.url:
    st.write("正在解析，请稍候...")

    # 初始化 BiliIdSpider 实例
    bili_web_scraper = BiliWebScraper(url = url)
    
    # 获取 aid 和 cid
    aid, bvid, cid, error = bili_web_scraper.find_api_inf()
    name = bili_web_scraper.find_video_name()
    
    if aid and cid:
        
        # 请求视频和音频下载地址
        params = {"fnver": "0", "fnval": "4048", "fourk": "1", "aid": aid, "bvid": bvid, "cid": cid}
        response = requests.get("https://api.bilibili.com/x/player/playurl", params=params, headers=headers)

        if response.status_code == 200:
            data = response.json()
            video_base_urls = [video.get('baseUrl', video.get('base_url')) for video in data['data']['dash']['video']]
            audio_base_urls = [audio.get('baseUrl', audio.get('base_url')) for audio in data['data']['dash']['audio']]

            # 下载视频和音频
            video_file = "video.mp4"
            audio_file = "audio.m4a"
            video_downloaded = False
            audio_downloaded = False

            st.write("正在下载视频...")
            for video_url in video_base_urls:
                if download_file(video_url, video_file):
                    video_downloaded = True
                    st.success("视频文件下载成功。")
                    break
            if not video_downloaded:
                st.error("视频文件下载失败。")

            st.write("正在下载音频...")
            for audio_url in audio_base_urls:
                if download_file(audio_url, audio_file):
                    audio_downloaded = True
                    st.success("音频文件下载成功。")
                    break
            if not audio_downloaded:
                st.error("音频文件下载失败。")

            # 合并音频和视频
            if video_downloaded and audio_downloaded:
                output_file = "output.mp4"
                st.write("正在合并音频和视频...")
                try:
                    video = VideoFileClip(video_file)
                    audio = AudioFileClip(audio_file)
                    video = video.set_audio(audio)
                    video.write_videofile(output_file, codec="libx264", audio_codec="aac")
                    st.success(f"合并完成: {output_file}")
                    with open(output_file, "rb") as f:
                        st.download_button("下载视频", f, file_name=output_file)
                    st.session_state.is_downloaded = True
                except Exception as e:
                    st.error(f"合并失败: {e}")
                finally:
                    video.close()
                    audio.close()
            else:
                st.error("视频或音频下载失败，无法合并。")

            # 清理临时文件
            if os.path.exists(video_file):
                os.remove(video_file)
            if os.path.exists(audio_file):
                os.remove(audio_file)
        else:
            st.error("获取视频或音频地址失败。")
            
    else:
        st.error(error)

