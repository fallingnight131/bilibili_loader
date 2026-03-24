import requests
import os
import subprocess
import re
import time

# ====================== 【只需修改这里】 ======================
EP_ID    = 259707          # 示例：https://www.bilibili.com/bangumi/play/ep259707
QUALITY  = 80              # 清晰度：80=1080P, 112=1080P+, 116=1080P60, 120=4K
SAVE_DIR = "bangumi_downloads"

SESSDATA = "0ac91153%2C1789890590%2C17b0d%2A31CjCfUTLAxjvbDamfcMZh3cR3X6n4S9qOOLUXXvvdOTahaKEVkl7GLEXnxslS16SsajISVjRzUHlHaTRQakVKTnNUZWRuaVUybTVHZFNONmgwNXU2VTJXa0FhYUNMWnJ1NmhHbmt2ZmVJUHZpb2dJenNZX3RKNm0zYXZsTW01cXUwa0o2NVhIWkZ3IIEC"
BILI_JCT = "2ca58e8fa5e4392f9bc5276930fc0b0f"
# ==============================================================

HEADERS = {
    "referer": "https://www.bilibili.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Cookie": f"SESSDATA={SESSDATA}; bili_jct={BILI_JCT}"
}

def get_bangumi_dash_urls(ep_id, quality):
    """获取番剧 DASH 模式下的音视频流地址"""
    # 注意：番剧使用 pgc 接口
    url = "https://api.bilibili.com/pgc/player/web/playurl"
    params = {
        "ep_id": ep_id,
        "qn": quality,
        "fnval": 16,  # 开启 DASH
        "fourk": 1,
        "platform": "pc"
    }
    res = requests.get(url, headers=HEADERS, params=params, timeout=10).json()
    
    if res.get('code') != 0:
        raise RuntimeError(f"API请求失败: {res.get('message')}")

    dash = res["result"]["dash"]
    # 提取视频流（默认取第一个，即当前 QN 下的最佳流）
    video_url = dash["video"][0]["baseUrl"]
    # 提取音频流
    audio_url = dash["audio"][0]["baseUrl"]
    
    return video_url, audio_url

def download_segment(url, filename, desc):
    """带进度的流式下载"""
    print(f"开始下载{desc}...")
    with requests.get(url, headers=HEADERS, stream=True, timeout=60) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        done = 0
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
                    done += len(chunk)
                    if total_size:
                        print(f"\r  进度: {done/total_size*100:.1f}%", end="")
    print(f"\n{desc}下载完成")

def merge_bangumi(v_path, a_path, out_path):
    """使用 FFmpeg 合并音视频"""
    print("正在合并文件...")
    cmd = [
        'ffmpeg', '-y',
        '-i', v_path,
        '-i', a_path,
        '-c', 'copy', # 直接拷贝编码，速度极快且无损
        out_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    print(f"✅ 处理成功: {out_path}")

def main():
    if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)
    
    try:
        # 1. 获取 DASH 链接
        v_url, a_url = get_bangumi_dash_urls(EP_ID, QUALITY)
        
        # 2. 定义临时文件名和最终文件名
        v_temp = os.path.join(SAVE_DIR, f"ep{EP_ID}_video.m4s")
        a_temp = os.path.join(SAVE_DIR, f"ep{EP_ID}_audio.m4s")
        final_mp4 = os.path.join(SAVE_DIR, f"bangumi_ep{EP_ID}_final.mp4")

        # 3. 下载
        download_segment(v_url, v_temp, "视频流")
        download_segment(a_url, a_temp, "音频流")

        # 4. 合并并清理
        merge_bangumi(v_temp, a_temp, final_mp4)
        
        if os.path.exists(v_temp): os.remove(v_temp)
        if os.path.exists(a_temp): os.remove(a_temp)
        
    except Exception as e:
        print(f"❌ 运行出错: {e}")

if __name__ == "__main__":
    main()