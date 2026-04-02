from datetime import datetime, timezone, timedelta
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 北京时间
BJT = timezone(timedelta(hours=8))


def now_bjt():
    """获取当前北京时间"""
    return datetime.now(BJT)


class User(db.Model):
    """用户表"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=now_bjt)

    tasks = db.relationship('DownloadTask', backref='user', lazy='dynamic')
    quotas = db.relationship('BangumiQuota', backref='user', lazy='dynamic')


class DownloadTask(db.Model):
    """下载任务表"""
    __tablename__ = 'download_tasks'

    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_type = db.Column(db.String(10), nullable=False)  # "video" 或 "bangumi"
    target_id = db.Column(db.String(50), nullable=False)  # BV号 或 ep_id
    title = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')
    progress = db.Column(db.Integer, default=0)
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    queue_position = db.Column(db.Integer)
    error_message = db.Column(db.String(500))
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=now_bjt)


class BangumiQuota(db.Model):
    """番剧下载配额表"""
    __tablename__ = 'bangumi_quota'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    count = db.Column(db.Integer, default=0)
    last_download_at = db.Column(db.DateTime)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', name='uq_user_date'),
    )
