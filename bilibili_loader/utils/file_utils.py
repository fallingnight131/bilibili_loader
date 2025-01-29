import json
import requests

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
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"下载失败: {e}")
    return False