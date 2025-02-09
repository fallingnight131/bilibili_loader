import os
from moviepy.editor import VideoFileClip, AudioFileClip
from bilibili_loader.utils.file_utils import remove_file

def merge_video(video_path="cache/video/video.mp4", 
                audio_path="cache/audio/audio.m4a", 
                output_path="cache/output",
                output_name="output"):
    """合并视频和音频文件。"""
    try:
        # 确保输出目录存在
        os.makedirs(output_path, exist_ok=True)
        
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)
        video = video.set_audio(audio)
        output_file = f"{output_path}/{output_name}.mp4"
        video.write_videofile(output_file, codec="libx264", audio_codec="aac")
        return output_file
    except Exception as e:
        print(f"合并失败: {e}")
        return None
    finally:
        video.close()
        audio.close()
        # 清理临时文件
        remove_file(video_path)
        remove_file(audio_path)
    