import requests
import os

# ====================== 【只需修改这里】 ======================
BVID = "BV1mRcrzSEYK"  # 改成你要爬的视频 BV 号
QUALITY = 116          # 清晰度：64=720P, 80=1080P, 112=1080P+, 116=1080P60, 120=4K
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
    "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Cookie": f"SESSDATA={SESSDATA}; bili_jct={BILI_JCT}"
}

def get_cid(bvid):
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    res = requests.get(url, headers=HEADERS, timeout=10).json()
    return res["data"]["cid"], res["data"]["title"]

def get_best_video_url(bvid, cid):
    # 直接获取 最高清 合并好的 MP4 地址
    url = "https://api.bilibili.com/x/player/playurl"
    params = {
        "bvid": bvid,
        "cid": cid,
        "qn": 80,      # 1080P
        "fnval": 0,    # 关闭DASH，直接拿合并好的视频
        "platform": "html5"
    }
    res = requests.get(url, headers=HEADERS, params=params, timeout=10).json()
    return res["data"]["durl"][0]["url"]

def download_video(url, save_name):
    print(f"开始下载高清视频：{save_name}")
    with open(save_name, "wb") as f:
        resp = requests.get(url, headers=HEADERS, stream=True, timeout=60)
        for chunk in resp.iter_content(1024*1024):
            f.write(chunk)
    print(f"✅ 下载完成！文件：{save_name}")

if __name__ == "__main__":
    print("正在获取视频信息...")
    cid, title = get_cid(BVID)
    print(f"视频标题：{title}")

    print("正在获取最高清下载地址...")
    video_url = get_best_video_url(BVID, cid)

    # 直接下载 高清MP4（自带声音，不用合并，不用ffmpeg）
    output_name = f"{title}.mp4".replace("/", "").replace("\\", "").replace(" ", "")
    download_video(video_url, output_name)