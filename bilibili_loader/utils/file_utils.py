import json
import requests
import streamlit as st

def load_json(filename="headers.json"):
        """加载 headers.json"""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            st.error(f"❌ 未找到 {filename} 文件，请检查路径是否正确")
            return {}
        except json.JSONDecodeError:
            st.error(f"❌ {filename} 文件格式错误，请检查是否为合法 JSON 格式")
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
        st.error(f"❌ 下载失败: {e}")
    return False