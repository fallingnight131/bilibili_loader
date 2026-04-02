import requests
import os
import subprocess
import re
import time
import hashlib
from urllib.parse import urlencode

# ====================== 【只需修改这里】 ======================
BVID     = "BV1DzCABvEAV"  # 目标视频 BV 号
QUALITY  = 120             # 期望清晰度：120=4K, 116=1080P60, 80=1080P
SAVE_DIR = "downloads"     # 保存目录

# 建议从你的 Flask 配置或数据库中读取以下信息
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

# --- WBI 签名算法部分 ---

def get_mixin_key(orig):
    """根据初始 key 进行重排，生成混淆后的 Mixin Key"""
    return ''.join([orig[i] for i in MIXIN_KEY_ENC_TAB])[:32]

def enc_wbi(params: dict, img_key: str, sub_key: str):
    """为请求参数字典计算并添加 wts (时间戳) 和 w_rid (签名)"""
    mixin_key = get_mixin_key(img_key + sub_key)
    curr_time = int(time.time())
    params['wts'] = curr_time
    
    # 1. 按照 key 的 ASCII 码升序排序
    params = dict(sorted(params.items()))
    
    # 2. 过滤参数值中的非法字符并进行 URL 编码
    # 注意：B站的WBI签名要求对字符进行特定过滤，这里使用 urlencode 处理基础编码
    query = urlencode(params)
    
    # 3. 拼接 Mixin Key 并计算 MD5
    w_rid = hashlib.md5((query + mixin_key).encode()).hexdigest()
    params['w_rid'] = w_rid
    return params

def get_wbi_keys():
    """核心：模拟浏览器先请求 nav 接口，动态提取当天的 img_key 和 sub_key"""
    url = "https://api.bilibili.com/x/web-interface/nav"
    res = requests.get(url, headers=HEADERS, timeout=10).json()
    if res['code'] != 0:
        raise RuntimeError(f"获取 WBI Keys 失败，请检查 Cookie: {res['message']}")
    
    wbi_img = res['data']['wbi_img']
    # 从 URL 中提取密钥字符串
    img_key = wbi_img['img_url'].split('/')[-1].split('.')[0]
    sub_key = wbi_img['sub_url'].split('/')[-1].split('.')[0]
    return img_key, sub_key

# --- 视频解析与下载部分 ---

def sanitize_name(name):
    """过滤文件名非法字符"""
    return re.sub(r'[\\/:*?"<>|]', '', name).strip()

def get_video_info(bvid):
    """获取视频的 CID 和 标题"""
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    res = requests.get(url, headers=HEADERS, timeout=10).json()
    if res['code'] != 0:
        raise RuntimeError(f"获取视频信息失败: {res['message']}")
    return res["data"]["cid"], sanitize_name(res["data"]["title"])

def get_dash_urls(bvid, cid, quality, img_key, sub_key):
    """使用 WBI 签名获取 DASH 模式的音视频流地址"""
    url = "https://api.bilibili.com/x/player/playurl"
    raw_params = {
        "bvid": bvid,
        "cid": cid,
        "qn": quality,
        "fnval": 16,  # 开启 DASH 模式以获取 1080P60/4K
        "fourk": 1
    }
    
    # 对参数进行签名处理
    signed_params = enc_wbi(raw_params, img_key, sub_key)
    
    res = requests.get(url, headers=HEADERS, params=signed_params, timeout=10).json()
    if res['code'] != 0:
        raise RuntimeError(f"获取下载地址失败 (可能是签名过期): {res['message']}")

    dash = res["data"]["dash"]
    # 默认返回视频列表和音频列表的第一个（最高质量）
    return dash["video"][0]["baseUrl"], dash["audio"][0]["baseUrl"]

def download_stream(url, filename, label):
    """优化后的下载函数：支持流式读取与异常捕获"""
    print(f"  正在下载 {label}...")
    max_retries = 5  # 最大重试次数
    
    for i in range(max_retries):
        try:
            # 增加 timeout 防止死等，设置 stream=True
            with requests.get(url, headers=HEADERS, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(filename, 'wb') as f:
                    # 使用较小的 chunk_size，并手动迭代
                    for chunk in r.iter_content(chunk_size=1024 * 512): # 512KB
                        if chunk:
                            f.write(chunk)
                return # 下载成功，退出循环
        except (requests.exceptions.RequestException, Exception) as e:
            print(f"  ⚠️ {label} 第 {i+1} 次尝试失败: {e}")
            time.sleep(2) # 等待后重试
            if i == max_retries - 1:
                raise RuntimeError(f"{label} 下载彻底失败")

def merge_video_audio(video_file, audio_file, output_file):
    """调用 FFmpeg 进行无损合并"""
    print(f"🎬 正在合并音视频...")
    cmd = [
        'ffmpeg', '-y',
        '-i', video_file,
        '-i', audio_file,
        '-c', 'copy',  # 不重编码，仅转换封装格式，极快
        output_file
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def main():
    if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)
    
    try:
        # 1. 第一步：获取 WBI 密钥（模拟真实访问流程）
        print("正在获取 WBI 动态密钥...")
        img_key, sub_key = get_wbi_keys()
        
        # 2. 第二步：获取基础信息
        cid, title = get_video_info(BVID)
        print(f"视频标题: {title}")
        
        # 3. 第三步：签名并获取下载链接
        v_url, a_url = get_dash_urls(BVID, cid, QUALITY, img_key, sub_key)
        
        # 临时文件路径
        v_temp = os.path.join(SAVE_DIR, f"{BVID}_v.m4s")
        a_temp = os.path.join(SAVE_DIR, f"{BVID}_a.m4s")
        final_mp4 = os.path.join(SAVE_DIR, f"{title}.mp4")

        # 4. 下载
        download_stream(v_url, v_temp, "视频流")
        download_stream(a_url, a_temp, "音频流")
        
        # 5. 合并
        merge_video_audio(v_temp, a_temp, final_mp4)

        # 6. 清理
        if os.path.exists(v_temp): os.remove(v_temp)
        if os.path.exists(a_temp): os.remove(a_temp)
        
        print(f"✅ 下载完成！文件保存至: {final_mp4}")
        
    except Exception as e:
        print(f"❌ 脚本执行失败: {e}")

if __name__ == "__main__":
    main()