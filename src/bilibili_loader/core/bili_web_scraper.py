import re
import requests
from bilibili_loader.utils.file_utils import load_json

class BiliWebScraper:
    def __init__(self, headers=load_json("src/bilibili_loader/config/headers/1.json"), url=None):
        self.aid = None
        self.bvid = None
        self.cid = None
        self.headers = headers
        self.url = url

    def extract_bv(self):
        """从给定的 URL 中提取 Bilibili 的 BV 号。"""
        bv_pattern = r"BV[0-9A-Za-z]+"
        match = re.search(bv_pattern, self.url)
        self.bvid = match.group(0) if match else None
        return self.bvid

    def find_api_inf(self):
        """从 Bilibili页面中提取 aid 和 cid 信息。"""
        try:
            self.extract_bv()
            response = requests.get(self.url, headers=self.headers)
            if response.status_code == 200:
                html_content = response.text
                matches = re.findall(r'"aid":(\d+),"bvid":"(BV[0-9A-Za-z]+)","cid":(\d+)', html_content)
                for aid, matched_bvid, cid in matches:
                    if matched_bvid == self.bvid:
                        self.aid = aid
                        self.cid = cid
                        return self.aid, self.bvid, self.cid
                return None, None, None
            else:
                return None, None, None
        except Exception:
            return None, None, None
        
    def find_video_name(self):
        """从 Bilibili 页面中提取视频标题。"""
        try:
            if not self.cid:
                self.find_api_inf()
            response = requests.get(self.url, headers=self.headers)
            if response.status_code == 200:
                html_content = response.text
                matches = re.findall(r'"cid":(\d+),"title":"(.*?)"', html_content)
                matches_with_quot = re.findall(r'"cid":(\d+),"title":"\\"([^"]+)\\""', html_content)    # 匹配标题中包含引号的情况
                matches.extend(matches_with_quot)
                for matched_cid, name in matches:
                    if matched_cid == self.cid and name != "\\":
                        return name
                return 'Output' #未找到匹配的 CID 号
            else:
                return 'Output' #请求失败
        except Exception:
            return 'Output' #请求失败
