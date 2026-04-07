import os

from dotenv import load_dotenv


# 自动加载 backend 目录下的 .env 文件
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


class Config:
    """应用配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///bilibili_downloader.db'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24小时

    # B站账号配置（从环境变量读取）
    BILI_SESSDATA = os.environ.get('BILI_SESSDATA', '')
    BILI_JCT = os.environ.get('BILI_JCT', '')

    # 下载配置
    DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), 'downloads')
    DOWNLOAD_QUALITY = 80  # 默认 1080P
    FILE_EXPIRE_MINUTES = 10  # 文件保留时间

    # 番剧限制
    BANGUMI_DAILY_LIMIT = 5

    # OSS 配置（可选，不填则走服务器直传）
    OSS_ACCESS_KEY_ID = os.environ.get('OSS_ACCESS_KEY_ID', '')
    OSS_ACCESS_KEY_SECRET = os.environ.get('OSS_ACCESS_KEY_SECRET', '')
    OSS_ENDPOINT = os.environ.get('OSS_ENDPOINT', '')  # 如 oss-cn-hangzhou.aliyuncs.com
    OSS_BUCKET_NAME = os.environ.get('OSS_BUCKET_NAME', '')
    OSS_CDN_DOMAIN = os.environ.get('OSS_CDN_DOMAIN', '')  # 如 cdn.example.com，不填则用 OSS 直链

    @classmethod
    def oss_enabled(cls):
        return all([cls.OSS_ACCESS_KEY_ID, cls.OSS_ACCESS_KEY_SECRET,
                    cls.OSS_ENDPOINT, cls.OSS_BUCKET_NAME])
