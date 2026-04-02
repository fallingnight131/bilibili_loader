import os


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
    BANGUMI_COOLDOWN_SECONDS = 120  # 2分钟冷却
