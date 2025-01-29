import requests
from bilibili_loader.core.bili_web_scraper import BiliWebScraper
from bilibili_loader.utils.file_utils import load_json, download_web_file
import streamlit as st

class BiliApiSpider:
    """Bilibili API 爬取视频。"""
    
    def __init__(self, headers=load_json("bilibili_loader/config/headers/1.json"), url=None):
        self.headers = headers
        self.api_url = "https://api.bilibili.com/x/player/playurl"
        self.bili_web_scraper = BiliWebScraper(headers = headers, url = url)
        aid, bvid, cid = self.bili_web_scraper.find_api_inf()
        self.params = {"fnver": "0", "fnval": "4048", "fourk": "1", "aid": aid, "bvid": bvid, "cid": cid}
        self.name = self.bili_web_scraper.find_video_name()
        self.video_downloaded = False
        self.audio_downloaded = False
        
    def get_baseurl_list(self):
        """从 API 返回的数据中提取视频和音频的下载地址。"""
        if self.params["aid"] and self.params["cid"]:
            response = requests.get(self.api_url, params=self.params, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                video_base_urls = [video.get('baseUrl', video.get('base_url')) for video in data['data']['dash']['video']]
                audio_base_urls = [audio.get('baseUrl', audio.get('base_url')) for audio in data['data']['dash']['audio']]
                return video_base_urls, audio_base_urls
            else:
                print(f"请求失败: {response.status_code}")
                return None, None
        else:
            print("api 参数获取错误")
            return None, None

    def download_media(self, video_path = "bilibili_loader/cache/video/video.mp4", 
                             audio_path = "bilibili_loader/cache/audio/audio.m4a"):
        """下载视频或音频文件。"""
        video_base_urls, audio_base_urls = self.get_baseurl_list()
        
        for video_url in video_base_urls:
            if download_web_file(video_url, video_path):
                self.video_downloaded = True
                break
            
        for audio_url in audio_base_urls:
            if download_web_file(audio_url, audio_path):
                self.audio_downloaded = True
                break
            
        if self.video_downloaded and self.audio_downloaded:
            return True
        else:
            return False