"""Flask 应用入口"""

import eventlet
eventlet.monkey_patch()

import os
import logging
from datetime import timedelta

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from models import db
from auth import auth_bp
from routes import download_bp, init_routes
from websocket import socketio
from task_queue import start_worker
from scheduler import start_scheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """创建 Flask 应用"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # JWT 过期时间
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)

    # 初始化扩展
    db.init_app(app)
    CORS(app, supports_credentials=True)
    JWTManager(app)
    socketio.init_app(app)

    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(download_bp)

    # 注入 socketio 到 routes
    init_routes(socketio)

    # 创建数据库表和下载目录
    with app.app_context():
        db.create_all()
        os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)

    # 启动 worker 线程
    start_worker()

    # 启动文件清理调度器
    start_scheduler(app, socketio)

    logger.info('应用启动完成')
    return app


if __name__ == '__main__':
    app = create_app()
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
