import json
import os
import requests
import random

def load_json(filename="headers.json"):
        """加载 headers.json"""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ 文件 {filename} 未找到，使用默认 headers")
            return {}
        except json.JSONDecodeError:
            print(f"⚠️ 解析 {filename} 失败，请检查 JSON 格式")
            return {}
        
def download_web_file(url, file_path):
    """下载文件的通用函数。"""
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"下载失败: {e}")
    return False

def remove_file(file_path):
    """删除文件"""
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def get_random_file(folder_path):
    """从指定文件夹中随机获取一个文件的路径"""
    if not os.path.isdir(folder_path):
        raise ValueError(f"路径 '{folder_path}' 不是一个有效的文件夹")

    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    if not files:
        raise FileNotFoundError(f"文件夹 '{folder_path}' 中没有文件")
    
    return os.path.join(folder_path, random.choice(files))