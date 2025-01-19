import requests

url = "https://api.bilibili.com/x/player/playurl"
params = {
    "fnver": "0",
    "fnval": "4048",
    "fourk": "1",
    "avid": "113787021624650",
    "bvid": "BV1YprQY5Euo",
    "cid": "27757446175"
}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
}

response = requests.get(url, params=params, headers=headers)
data = response.json()

# 提取所有的URL
video_base_urls = []
audio_base_urls = []

# 遍历所有的dash项
for video_data in data['data']['dash']['video']:
    if 'baseUrl' in video_data:
        video_base_urls.append(video_data['baseUrl'])
    if 'base_url' in video_data:
        video_base_urls.append(video_data['base_url'])
        
for audio_data in data['data']['dash']['audio']:
    if 'baseUrl' in audio_data:
        audio_base_urls.append(audio_data['baseUrl'])
    if 'base_url' in audio_data:
        audio_base_urls.append(audio_data['base_url'])

# 输出所有提取的URL
print("Video Base URLs:")
for url in video_base_urls:
    print(url)
    print("-----------------------------------------------------------------")
    
print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
     
print("Audio Base URLs:")
for url in audio_base_urls:
    print(url)
    print("-----------------------------------------------------------------")
    