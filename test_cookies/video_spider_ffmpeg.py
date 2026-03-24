import requests
import os
import subprocess
import re

# ====================== 【只需修改这里】 ======================
BVID     = "BV1c7wEzrEBm"  # 目标视频 BV 号
QUALITY  = 120             # 期望清晰度：120=4K, 116=1080P60, 80=1080P
SAVE_DIR = "downloads"     # 保存目录

SESSDATA = "0ac91153%2C1789890590%2C17b0d%2A31CjCfUTLAxjvbDamfcMZh3cR3X6n4S9qOOLUXXvvdOTahaKEVkl7GLEXnxslS16SsajISVjRzUHlHaTRQakVKTnNUZWRuaVUybTVHZFNONmgwNXU2VTJXa0FhYUNMWnJ1NmhHbmt2ZmVJUHZpb2dJenNZX3RKNm0zYXZsTW01cXUwa0o2NVhIWkZ3IIEC"
BILI_JCT = "2ca58e8fa5e4392f9bc5276930fc0b0f"
# ==============================================================

HEADERS = {
    "referer": "https://www.bilibili.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Cookie": f"SESSDATA={SESSDATA}; bili_jct={BILI_JCT}"
}

def sanitize_name(name):
    return re.sub(r'[\\/:*?"<>|]', '', name).strip()

def get_video_info(bvid):
    """获取视频的基本信息：cid 和 标题"""
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    res = requests.get(url, headers=HEADERS, timeout=10).json()
    if res['code'] != 0:
        raise RuntimeError(f"获取视频信息失败: {res['message']}")
    return res["data"]["cid"], sanitize_name(res["data"]["title"])

def get_dash_urls(bvid, cid, quality):
    """获取 DASH 模式下的音视频流地址"""
    url = "https://api.bilibili.com/x/player/playurl"
    params = {
        "bvid": bvid,
        "cid": cid,
        "qn": quality,
        "fnval": 16,  # 16 代表开启 DASH 模式
        "fourk": 1
    }
    res = requests.get(url, headers=HEADERS, params=params, timeout=10).json()
    
    if res['code'] != 0:
        raise RuntimeError("无法获取播放地址，请检查 Cookie 是否有效")

    dash = res["data"]["dash"]
    # 选取对应画质的视频流（取列表第一个通常是最高画质）
    video_url = dash["video"][0]["baseUrl"]
    # 选取音频流
    audio_url = dash["audio"][0]["baseUrl"]
    
    return video_url, audio_url

def download_stream(url, filename):
    """流式下载函数"""
    print(f"  正在下载: {filename}")
    with requests.get(url, headers=HEADERS, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                f.write(chunk)

def merge_video_audio(video_file, audio_file, output_file):
    """使用 FFmpeg 合并音视频"""
    print(f"🎬 正在合并为最终视频...")
    # -y 表示覆盖已存在文件，-c copy 表示不重新编码（极快）
    cmd = [
        'ffmpeg', '-y',
        '-i', video_file,
        '-i', audio_file,
        '-c', 'copy',
        output_file
    ]
    # 屏蔽 ffmpeg 冗长的 log 输出
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    print(f"✅ 合并完成: {output_file}")

def main():
    if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)
    
    try:
        cid, title = get_video_info(BVID)
        print(f"目标视频: {title}")
        
        v_url, a_url = get_dash_urls(BVID, cid, QUALITY)
        
        v_temp = os.path.join(SAVE_DIR, f"{BVID}_v.m4s")
        a_temp = os.path.join(SAVE_DIR, f"{BVID}_a.m4s")
        final_mp4 = os.path.join(SAVE_DIR, f"{title}.mp4")

        # 1. 下载视频流
        download_stream(v_url, v_temp)
        # 2. 下载音频流
        download_stream(a_url, a_temp)
        # 3. 合并
        merge_video_audio(v_temp, a_temp, final_mp4)

        # 4. 清理临时文件
        os.remove(v_temp)
        os.remove(a_temp)
        
    except Exception as e:
        print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    main()