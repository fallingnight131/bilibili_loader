import asyncio
from bilibili_api.video import Video

async def fetch_video_info(bvid):
    # 创建 Video 对象
    video = Video(bvid)
    # 获取播放链接信息
    info = await video.get_playurl()
    print(info)

# 主入口
if __name__ == "__main__":
    bvid = "BV1vT411P7B3"
    asyncio.run(fetch_video_info(bvid))
