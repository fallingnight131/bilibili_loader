import requests
from bilibili_loader.core.bili_web_scraper import BiliWebScraper
from bilibili_loader.utils.file_utils import load_json, download_web_file


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
        try:
            if self.params["aid"] and self.params["cid"]:
                response = requests.get(self.api_url, params=self.params, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    video_base_urls = [video.get('baseUrl', video.get('base_url')) for video in data['data']['dash']['video']]
                    audio_base_urls = [audio.get('baseUrl', audio.get('base_url')) for audio in data['data']['dash']['audio']]
                    return video_base_urls, audio_base_urls, None
                else:
                    return None, None, f"这个视频被强大的能量包裹，暂且无法被观测哦~ 请稍作休息后再尝试吧。"
            else:
                return None, None, "您输入的咒语貌似包含了不属于这个世界的力量，大地与天空并没有给予回应。"
            
        except KeyError:
            return None, None, f"这个视频被跨越时间的能量包裹，需要旧时代的利刃才能破开。"
        
        except Exception:
            return None, None, f"糟糕，被未知力场影响了。"

    def download_media(self, video_path = "cache/video/video.mp4", 
                             audio_path = "cache/audio/audio.m4a"):
        """下载视频或音频文件。"""
        video_base_urls, audio_base_urls , error = self.get_baseurl_list()
        
        if not error:
            if not self.video_downloaded:
                for video_url in video_base_urls:
                    if download_web_file(video_url, video_path):
                        self.video_downloaded = True
                        break
                
            if not self.audio_downloaded:
                for audio_url in audio_base_urls:
                    if download_web_file(audio_url, audio_path):
                        self.audio_downloaded = True
                        break
                
            if self.video_downloaded and self.audio_downloaded:
                return True, None
            
            else:
                return False, None
            
        else:
            return None, error