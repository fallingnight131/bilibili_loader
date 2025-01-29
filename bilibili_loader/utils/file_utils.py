import json

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