"""B站视频/番剧下载核心逻辑"""

import os
import re
import time
import hashlib
import logging
import subprocess
import requests
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

# WBI 混淆表（官方固定映射）
MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52
]


def _build_headers(sessdata, bili_jct):
    """构建请求头"""
    return {
        "referer": "https://www.bilibili.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "Cookie": f"SESSDATA={sessdata}; bili_jct={bili_jct}"
    }


def _get_mixin_key(orig):
    """生成混淆后的 Mixin Key"""
    return ''.join([orig[i] for i in MIXIN_KEY_ENC_TAB])[:32]


def _enc_wbi(params: dict, img_key: str, sub_key: str):
    """为请求参数字典计算并添加 wts 和 w_rid"""
    mixin_key = _get_mixin_key(img_key + sub_key)
    params['wts'] = int(time.time())
    params = dict(sorted(params.items()))
    query = urlencode(params)
    w_rid = hashlib.md5((query + mixin_key).encode()).hexdigest()
    params['w_rid'] = w_rid
    return params


def get_wbi_keys(headers):
    """从 nav 接口动态获取 img_key 和 sub_key"""
    url = "https://api.bilibili.com/x/web-interface/nav"
    res = requests.get(url, headers=headers, timeout=10).json()
    if res['code'] != 0:
        raise RuntimeError(f"获取 WBI Keys 失败: {res['message']}")
    wbi_img = res['data']['wbi_img']
    img_key = wbi_img['img_url'].split('/')[-1].split('.')[0]
    sub_key = wbi_img['sub_url'].split('/')[-1].split('.')[0]
    return img_key, sub_key


def sanitize_filename(name):
    """过滤文件名非法字符"""
    return re.sub(r'[\\/:*?"<>|]', '', name).strip()


def parse_bvid(input_str):
    """从用户输入中提取 BV 号"""
    input_str = input_str.strip()
    # 匹配 BV 号（12位字母数字）
    match = re.search(r'(BV[a-zA-Z0-9]{10})', input_str)
    if match:
        return match.group(1)
    raise ValueError('无法解析 BV 号，请输入正确的 BV 号或视频链接')


def parse_ep_id(input_str):
    """从用户输入中提取 ep_id（纯数字）"""
    input_str = input_str.strip()
    # 匹配 epXXXXX 格式
    match = re.search(r'ep(\d+)', input_str)
    if match:
        return match.group(1)
    # 纯数字
    if input_str.isdigit():
        return input_str
    raise ValueError('无法解析 EP 号，请输入正确的 EP 号或番剧链接')


def get_video_info(bvid, headers):
    """获取视频 CID 和标题"""
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    res = requests.get(url, headers=headers, timeout=10).json()
    if res['code'] != 0:
        raise RuntimeError(f"获取视频信息失败: {res['message']}")
    return res["data"]["cid"], sanitize_filename(res["data"]["title"])


def get_video_dash_urls(bvid, cid, quality, img_key, sub_key, headers):
    """获取普通视频 DASH 音视频流地址"""
    url = "https://api.bilibili.com/x/player/playurl"
    raw_params = {
        "bvid": bvid, "cid": cid, "qn": quality,
        "fnval": 16, "fourk": 1
    }
    signed_params = _enc_wbi(raw_params, img_key, sub_key)
    res = requests.get(url, headers=headers, params=signed_params, timeout=10).json()
    if res['code'] != 0:
        raise RuntimeError(f"获取下载地址失败: {res['message']}")
    dash = res["data"]["dash"]
    return dash["video"][0]["baseUrl"], dash["audio"][0]["baseUrl"]


def get_bangumi_info(ep_id, headers):
    """获取番剧标题（通过 ep_id）"""
    url = f"https://api.bilibili.com/pgc/view/web/season?ep_id={ep_id}"
    res = requests.get(url, headers=headers, timeout=10).json()
    if res.get('code') != 0:
        raise RuntimeError(f"获取番剧信息失败: {res.get('message')}")
    # 从分集列表中查找对应 ep 的标题
    result = res.get('result', {})
    season_title = result.get('season_title', f'番剧ep{ep_id}')
    episodes = result.get('episodes', [])
    for ep in episodes:
        if str(ep.get('id')) == str(ep_id):
            ep_title = ep.get('share_copy', ep.get('long_title', ''))
            if ep_title:
                return sanitize_filename(f"{season_title} - {ep_title}")
    return sanitize_filename(season_title)


def get_bangumi_dash_urls(ep_id, quality, img_key, sub_key, headers):
    """获取番剧 DASH 音视频流地址"""
    url = "https://api.bilibili.com/pgc/player/web/playurl"
    raw_params = {
        "ep_id": ep_id, "qn": quality,
        "fnval": 16, "fourk": 1, "platform": "pc"
    }
    signed_params = _enc_wbi(raw_params, img_key, sub_key)
    res = requests.get(url, headers=headers, params=signed_params, timeout=10).json()
    if res.get('code') != 0:
        raise RuntimeError(f"API请求失败: {res.get('message')}")
    dash = res["result"]["dash"]
    return dash["video"][0]["baseUrl"], dash["audio"][0]["baseUrl"]


def download_stream(url, filename, headers, progress_callback=None):
    """流式下载，支持进度回调与自动重试"""
    max_retries = 5
    for i in range(max_retries):
        try:
            with requests.get(url, headers=headers, stream=True, timeout=30) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                done = 0
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024 * 512):
                        if chunk:
                            f.write(chunk)
                            done += len(chunk)
                            if progress_callback and total_size:
                                progress_callback(done / total_size * 100)
            return
        except (requests.exceptions.RequestException, Exception) as e:
            logger.warning(f'下载第 {i+1} 次失败: {e}')
            time.sleep(2)
            if i == max_retries - 1:
                raise RuntimeError(f'下载彻底失败: {e}')


def merge_av(video_path, audio_path, output_path):
    """FFmpeg 无损合并"""
    cmd = ['ffmpeg', '-y', '-i', video_path, '-i', audio_path, '-c', 'copy', output_path]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=True)


def download_video(bvid, download_dir, quality, sessdata, bili_jct, progress_callback=None):
    """
    完整的视频下载流程
    progress_callback(progress_percent, status_message)
    """
    headers = _build_headers(sessdata, bili_jct)

    # 获取 WBI 密钥
    img_key, sub_key = get_wbi_keys(headers)

    # 获取视频信息
    cid, title = get_video_info(bvid, headers)
    logger.info(f'视频标题: {title}')

    if progress_callback:
        progress_callback(0, f'正在解析: {title}')

    # 获取下载地址
    v_url, a_url = get_video_dash_urls(bvid, cid, quality, img_key, sub_key, headers)

    os.makedirs(download_dir, exist_ok=True)
    v_temp = os.path.join(download_dir, f"{bvid}_v.m4s")
    a_temp = os.path.join(download_dir, f"{bvid}_a.m4s")
    final_mp4 = os.path.join(download_dir, f"{title}.mp4")

    try:
        # 下载视频流 0-45%
        def video_progress(pct):
            if progress_callback:
                progress_callback(int(pct * 0.45), '正在下载视频流')
        download_stream(v_url, v_temp, headers, video_progress)

        # 下载音频流 45-90%
        def audio_progress(pct):
            if progress_callback:
                progress_callback(45 + int(pct * 0.45), '正在下载音频流')
        download_stream(a_url, a_temp, headers, audio_progress)

        # 合并 90-100%
        if progress_callback:
            progress_callback(90, '正在合并音视频')
        merge_av(v_temp, a_temp, final_mp4)

        if progress_callback:
            progress_callback(100, '下载完成')

        file_size = os.path.getsize(final_mp4)
        return title, final_mp4, file_size

    finally:
        # 清理临时文件
        for f in [v_temp, a_temp]:
            if os.path.exists(f):
                os.remove(f)


def download_bangumi(ep_id, download_dir, quality, sessdata, bili_jct, progress_callback=None):
    """
    完整的番剧下载流程
    progress_callback(progress_percent, status_message)
    """
    headers = _build_headers(sessdata, bili_jct)

    # 获取 WBI 密钥
    img_key, sub_key = get_wbi_keys(headers)

    # 获取番剧标题
    title = get_bangumi_info(ep_id, headers)
    logger.info(f'番剧标题: {title}')

    if progress_callback:
        progress_callback(0, f'正在解析: {title}')

    # 获取下载地址
    v_url, a_url = get_bangumi_dash_urls(ep_id, quality, img_key, sub_key, headers)

    os.makedirs(download_dir, exist_ok=True)
    v_temp = os.path.join(download_dir, f"ep{ep_id}_v.m4s")
    a_temp = os.path.join(download_dir, f"ep{ep_id}_a.m4s")
    final_mp4 = os.path.join(download_dir, f"{title}.mp4")

    try:
        # 下载视频流 0-45%
        def video_progress(pct):
            if progress_callback:
                progress_callback(int(pct * 0.45), '正在下载视频流')
        download_stream(v_url, v_temp, headers, video_progress)

        # 下载音频流 45-90%
        def audio_progress(pct):
            if progress_callback:
                progress_callback(45 + int(pct * 0.45), '正在下载音频流')
        download_stream(a_url, a_temp, headers, audio_progress)

        # 合并 90-100%
        if progress_callback:
            progress_callback(90, '正在合并音视频')
        merge_av(v_temp, a_temp, final_mp4)

        if progress_callback:
            progress_callback(100, '下载完成')

        file_size = os.path.getsize(final_mp4)
        return title, final_mp4, file_size

    finally:
        # 清理临时文件
        for f in [v_temp, a_temp]:
            if os.path.exists(f):
                os.remove(f)
