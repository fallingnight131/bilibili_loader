import requests
import os
import re
import time

# ====================== 【只需修改这里】 ======================
# 单集链接示例：https://www.bilibili.com/bangumi/play/ep259707
EP_ID    = 259707          # ep 后面的数字
QUALITY  = 80              # 清晰度：64=720P, 80=1080P, 112=1080P+, 116=1080P60
SAVE_DIR = "./bangumi"     # 视频保存文件夹

SESSDATA = "0ac91153%2C1789890590%2C17b0d%2A31CjCfUTLAxjvbDamfcMZh3cR3X6n4S9qOOLUXXvvdOTahaKEVkl7GLEXnxslS16SsajISVjRzUHlHaTRQakVKTnNUZWRuaVUybTVHZFNONmgwNXU2VTJXa0FhYUNMWnJ1NmhHbmt2ZmVJUHZpb2dJenNZX3RKNm0zYXZsTW01cXUwa0o2NVhIWkZ3IIEC"  # 浏览器复制的 SESSDATA
BILI_JCT = "2ca58e8fa5e4392f9bc5276930fc0b0f"    # 浏览器复制的 bili_jc
# ==============================================================

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9",
    "cache-control": "no-cache",
    "origin": "https://www.bilibili.com",
    "pragma": "no-cache",
    "referer": "https://www.bilibili.com/",
    "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Cookie": f"SESSDATA={SESSDATA}; bili_jct={BILI_JCT}"
}


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', '', name).strip()


def get_episode_play_url(ep_id: int, quality: int) -> str:
    """通过 ep_id 获取番剧单集直链 MP4 URL"""
    url = "https://api.bilibili.com/pgc/player/web/playurl"
    params = {
        "ep_id":    ep_id,
        "qn":       quality,
        "fnval":    0,        # 关闭 DASH，直接拿合并好的 MP4
        "platform": "html5",
    }
    res = requests.get(url, headers=HEADERS, params=params, timeout=10).json()

    if res.get("code") != 0:
        raise RuntimeError(
            f"获取播放地址失败：{res.get('message')}（code={res.get('code')}）\n"
            "提示：大会员内容需要有效的 SESSDATA。"
        )

    durl = res.get("result", {}).get("durl", [])
    if not durl:
        raise RuntimeError("播放地址为空，请检查 SESSDATA 是否有效或该集是否有权限观看。")

    return durl[0]["url"]


def download_file(url: str, save_path: str):
    """流式下载，显示进度和速度"""
    resp = requests.get(url, headers=HEADERS, stream=True, timeout=120)
    resp.raise_for_status()

    total = int(resp.headers.get("content-length", 0))
    downloaded = 0
    start = time.time()

    with open(save_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):  # 1 MB/chunk
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded / total * 100
                    speed = downloaded / (time.time() - start + 1e-6) / 1024 / 1024
                    print(
                        f"\r  进度：{pct:5.1f}%  速度：{speed:.1f} MB/s  "
                        f"({downloaded // 1024 // 1024}/{total // 1024 // 1024} MB)",
                        end="", flush=True
                    )
    print()  # 换行


def main():
    os.makedirs(SAVE_DIR, exist_ok=True)

    print(f"▶ 单集模式：ep_id={EP_ID}")
    print("正在获取播放地址...")

    try:
        video_url = get_episode_play_url(EP_ID, QUALITY)
    except RuntimeError as e:
        print(f"❌ {e}")
        return

    filename = f"ep_{EP_ID}.mp4"
    save_path = os.path.join(SAVE_DIR, filename)

    if os.path.exists(save_path):
        print(f"⏭  文件已存在，跳过：{save_path}")
        return

    print(f"⬇  开始下载：{filename}")
    try:
        download_file(video_url, save_path)
        print(f"✅ 下载完成：{save_path}")
    except Exception as e:
        print(f"❌ 下载失败：{e}")
        if os.path.exists(save_path):
            os.remove(save_path)  # 清理不完整文件


if __name__ == "__main__":
    main()