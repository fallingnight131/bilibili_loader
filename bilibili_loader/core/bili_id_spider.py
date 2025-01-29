import re
import requests
from bilibili_loader.utils.file_utils import load_json

class BiliIdSpider:
    def __init__(self, headers=load_json("bilibili_loader/config/headers/1.json")):
        self.aid = None
        self.bvid = None
        self.cid = None
        self.headers = headers

    def extract_bv(self, url):
        """从给定的 URL 中提取 Bilibili 的 BV 号。"""
        bv_pattern = r"BV[0-9A-Za-z]+"
        match = re.search(bv_pattern, url)
        self.bvid = match.group(0) if match else None
        return self.bvid

    def find_api_inf(self, url):
        """从 Bilibili页面中提取 aid 和 cid 信息。"""
        try:
            self.extract_bv(url)
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                html_content = response.text
                matches = re.findall(r'"aid":(\d+),"bvid":"(BV[0-9A-Za-z]+)","cid":(\d+)', html_content)
                for aid, matched_bvid, cid in matches:
                    if matched_bvid == self.bvid:
                        self.aid = aid
                        self.cid = cid
                        return self.aid, self.bvid, self.cid, None
                return None, None, None, f"未找到匹配的 BV 号: {self.bvid}"
            else:
                return None, None, None, f"请求失败，状态码：{response.status_code}"
        except Exception as e:
            return None, None, None, f"请求失败: {e}"
        
