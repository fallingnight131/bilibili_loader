import os
from moviepy.editor import VideoFileClip, AudioFileClip

def merge_video(video_path = "bilibili_loader/cache/video/video.mp4", 
                audio_path = "bilibili_loader/cache/audio/audio.m4a", 
                output_path = "bilibili_loader/cache/output",
                output_name = "output"):
    """合并视频和音频文件。"""
    try:
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)
        video = video.set_audio(audio)
        video.write_videofile(f"{output_path}/{output_name}.mp4", codec="libx264", audio_codec="aac")
        return f"{output_path}/{output_name}.mp4"
    except Exception as e:
        print(f"合并失败: {e}")
        return None
    finally:
        video.close()
        audio.close()
        # 清理临时文件
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(audio_path):
            os.remove(audio_path)
    