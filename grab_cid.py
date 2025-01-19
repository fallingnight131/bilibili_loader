import requests
import re

bvid = "BV1YprQY5Euo"

# 视频页面 URL
url = "https://www.bilibili.com/video/{}".format(bvid)

# 设置请求头，模拟浏览器
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
}

# 发送 GET 请求
response = requests.get(url, headers=headers)

if response.status_code == 200:
    html_content = response.text

    # 匹配包含 aid、bvid 和 cid 的字段
    matches = re.findall(r'"aid":(\d+),"bvid":"(BV[0-9A-Za-z]+)","cid":(\d+)', html_content)

    # 查找指定 bvid 的 aid 和 cid
    for aid, bvid, cid in matches:
        if bvid == bvid:
            print(f"匹配到指定 bvid: {bvid}")
            print(f"对应的 aid: {aid}")
            print(f"对应的 cid: {cid}")
            break
    else:
        print(f"未找到指定的 bvid: {bvid}")
else:
    print(f"请求失败，状态码：{response.status_code}")