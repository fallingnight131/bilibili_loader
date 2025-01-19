import requests

url = "https://api.bilibili.com/x/player/playurl"
params = {
    "fnver": 0,
    "fnval": 4048,
    "bvid": "BV1vT411P7B3",
    "cid": 854895314
}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
}

response = requests.get(url, params=params, headers=headers)
data = response.json()

# 提取所有的URL
video_base_urls = []
video_backup_urls = []
audio_base_urls = []
audio_backup_urls = []

# 遍历所有的dash项
for video_data in data['data']['dash']['video']:
    if 'baseUrl' in video_data:
        video_base_urls.append(video_data['baseUrl'])
    if 'base_url' in video_data:
        video_base_urls.append(video_data['base_url'])
    if 'backupUrl' in video_data:
        video_backup_urls.append(video_data['backupUrl'][0])
    if 'backup_url' in video_data:
        video_backup_urls.append(video_data['backup_url'][0])

# 输出所有提取的URL
print("Video Base URLs:")
for url in video_base_urls:
    print(url)
    print("-----------------------------------------------------------------")
    
print("Video Backup URLs:")
for url in video_backup_urls:
    print(url)
    print("-----------------------------------------------------------------")
    