import requests
import os
from moviepy.editor import VideoFileClip, AudioFileClip
import re

# 视频页面 URL
url = input("请输入 Bilibili 视频的网址:\n ")

def extract_bv(url):
    """
    从给定的 URL 中提取 Bilibili 的 BV 号。

    参数:
        url (str): 包含 BV 号的 URL。

    返回:
        str: 提取到的 BV 号，如果未找到则返回 None。
    """
    # 定义匹配 BV 号的正则表达式
    bv_pattern = r"BV[0-9A-Za-z]+"
    
    # 使用正则表达式在 URL 中查找
    match = re.search(bv_pattern, url)
    
    if match:
        return match.group(0)  # 返回匹配到的 BV 号
    else:
        return None  # 如果没有匹配到 BV 号，则返回 None
    
bvid = extract_bv(url)



def find_api_inf(url, bvid, headers):
    # 获取api信息
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        html_content = response.text

        # 匹配包含 aid、bvid 和 cid 的字段
        matches = re.findall(r'"aid":(\d+),"bvid":"(BV[0-9A-Za-z]+)","cid":(\d+)', html_content)

        # 查找指定 bvid 的 aid 和 cid
        for aid, matched_bvid, cid in matches:
            if matched_bvid == bvid:
                return aid, cid
        else:
            print(f"未找到指定的 bvid: {bvid}")
    else:
        print(f"请求失败，状态码：{response.status_code}")

# 设置请求头，模拟浏览器
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
}

aid, cid = find_api_inf(url, bvid, headers)

params = {
"fnver": "0",
"fnval": "4048",
"fourk": "1",
"aid": aid,
"bvid": bvid,
"cid": cid,
}

# 请求 B站 API
response = requests.get("https://api.bilibili.com/x/player/playurl", params=params, headers=headers)

data = response.json()

# 提取视频和音频 URL
video_base_urls = []
audio_base_urls = []

# 提取视频 URL
for video_data in data['data']['dash']['video']:
    if 'baseUrl' in video_data:
        video_base_urls.append(video_data['baseUrl'])
    if 'base_url' in video_data:
        video_base_urls.append(video_data['base_url'])

# 提取音频 URL
for audio_data in data['data']['dash']['audio']:
    if 'baseUrl' in audio_data:
        audio_base_urls.append(audio_data['baseUrl'])
    if 'base_url' in audio_data:
        audio_base_urls.append(audio_data['base_url'])

# 定义下载函数
def download_file(url, filename):
    try:
        print(f"正在下载: {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"下载完成: {filename}")
        return True
    except Exception as e:
        print(f"下载失败: {url}, 错误: {e}")
        return False

# 下载视频和音频
video_file = "video.mp4"
audio_file = "audio.m4a"

video_downloaded = False
audio_downloaded = False

for video_url in video_base_urls:
    if download_file(video_url, video_file):
        video_downloaded = True
        break

for audio_url in audio_base_urls:
    if download_file(audio_url, audio_file):
        audio_downloaded = True
        break

# 合并音频和视频
if video_downloaded and audio_downloaded:
    output_file = "output.mp4"
    print("正在合并音频和视频...")
    try:
        # 加载视频和音频文件
        video = VideoFileClip(video_file)
        audio = AudioFileClip(audio_file)

        # 将音频添加到视频
        video = video.set_audio(audio)

        # 导出合并后的视频
        video.write_videofile(output_file, codec="libx264", audio_codec="aac")
        print(f"合并完成: {output_file}")
    except Exception as e:
        print(f"合并失败: {e}")
    finally:
        # 清理 MoviePy 的缓存文件
        video.close()
        audio.close()
else:
    print("视频或音频下载失败，无法合并。")

# 清理临时文件
if os.path.exists(video_file):
    os.remove(video_file)
if os.path.exists(audio_file):
    os.remove(audio_file)

