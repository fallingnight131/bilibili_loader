import requests
import os
import subprocess
import re
import time
import hashlib
from urllib.parse import urlencode

# ====================== 【只需修改这里】 ======================
EP_ID    = 259707          # 示例：https://www.bilibili.com/bangumi/play/ep259707
QUALITY  = 80              # 清晰度：80=1080P, 112=1080P+, 116=1080P60, 120=4K
SAVE_DIR = "downloads"    # 保存目录

SESSDATA = ""
BILI_JCT = ""
# ==============================================================

# WBI 混淆表 (官方固定映射)
MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52
]

HEADERS = {
    "referer": "https://www.bilibili.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Cookie": f"SESSDATA={SESSDATA}; bili_jct={BILI_JCT}"
}

# --- WBI 签名核心算法 ---

def get_mixin_key(orig):
    """生成混淆后的 Mixin Key"""
    return ''.join([orig[i] for i in MIXIN_KEY_ENC_TAB])[:32]

def enc_wbi(params: dict, img_key: str, sub_key: str):
    """为请求参数字典计算并添加 wts 和 w_rid"""
    mixin_key = get_mixin_key(img_key + sub_key)
    params['wts'] = int(time.time())
    # ASCII 升序排序
    params = dict(sorted(params.items()))
    # URL 编码并过滤
    query = urlencode(params)
    # 计算 MD5 签名
    w_rid = hashlib.md5((query + mixin_key).encode()).hexdigest()
    params['w_rid'] = w_rid
    return params

def get_wbi_keys():
    """从 nav 接口动态获取 img_key 和 sub_key"""
    url = "https://api.bilibili.com/x/web-interface/nav"
    res = requests.get(url, headers=HEADERS, timeout=10).json()
    if res['code'] != 0:
        raise RuntimeError(f"获取 WBI Keys 失败 (nav): {res['message']}")
    
    wbi_img = res['data']['wbi_img']
    img_key = wbi_img['img_url'].split('/')[-1].split('.')[0]
    sub_key = wbi_img['sub_url'].split('/')[-1].split('.')[0]
    return img_key, sub_key

# --- 番剧解析与下载逻辑 ---

def get_bangumi_dash_urls(ep_id, quality, img_key, sub_key):
    """获取番剧 DASH 模式下的音视频流地址 (带 WBI 签名)"""
    # 番剧专用 API 路径
    url = "https://api.bilibili.com/pgc/player/web/playurl"
    raw_params = {
        "ep_id": ep_id,
        "qn": quality,
        "fnval": 16,  # 开启 DASH
        "fourk": 1,
        "platform": "pc"
    }
    # 注入 WBI 签名
    signed_params = enc_wbi(raw_params, img_key, sub_key)
    
    res = requests.get(url, headers=HEADERS, params=signed_params, timeout=10).json()
    
    if res.get('code') != 0:
        raise RuntimeError(f"API请求失败: {res.get('message')}")

    dash = res["result"]["dash"]
    video_url = dash["video"][0]["baseUrl"]
    audio_url = dash["audio"][0]["baseUrl"]
    
    return video_url, audio_url

def download_segment(url, filename, desc):
    """带进度的流式下载"""
    print(f"正在下载 {desc}...")
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
    print(f"\n{desc} 下载完成")

def merge_bangumi(v_path, a_path, out_path):
    """使用 FFmpeg 无损合并音视频"""
    print("🎬 正在合并文件...")
    cmd = [
        'ffmpeg', '-y',
        '-i', v_path,
        '-i', a_path,
        '-c', 'copy',
        out_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    print(f"✅ 处理成功: {out_path}")

def main():
    if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)
    
    try:
        # 1. 获取 WBI 动态密钥
        print("正在同步 WBI 动态密钥...")
        img_key, sub_key = get_wbi_keys()
        
        # 2. 获取 DASH 链接 (带签名)
        print(f"正在获取 ep{EP_ID} 的播放地址...")
        v_url, a_url = get_bangumi_dash_urls(EP_ID, QUALITY, img_key, sub_key)
        
        v_temp = os.path.join(SAVE_DIR, f"ep{EP_ID}_video.m4s")
        a_temp = os.path.join(SAVE_DIR, f"ep{EP_ID}_audio.m4s")
        final_mp4 = os.path.join(SAVE_DIR, f"bangumi_ep{EP_ID}_final.mp4")

        # 3. 执行下载
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