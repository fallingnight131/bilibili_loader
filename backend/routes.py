"""下载相关 API 蓝图"""

import uuid
import logging
import os
import time
from datetime import timedelta

from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, DownloadTask, BangumiQuota, CookieSettingCooldown, now_bjt
from downloader import parse_bvid, parse_ep_id, validate_bili_cookie
from task_queue import submit_task, get_queue_status
from config import Config

# 短效下载 token 存储：{token: (task_id, user_id, expire_timestamp)}
_download_tokens: dict = {}

# 提供凭据的特权用户 ID（无限番剧下载）
_privileged_user_id: int | None = None

logger = logging.getLogger(__name__)
download_bp = Blueprint('download', __name__, url_prefix='/api/download')

# socketio 实例将在 app.py 中注入
_socketio = None

COOKIE_SETTING_COOLDOWN_SECONDS = 120


def init_routes(socketio):
    """注入 socketio 实例"""
    global _socketio
    _socketio = socketio


@download_bp.route('/video', methods=['POST'])
@jwt_required()
def submit_video_download():
    """提交视频下载任务"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data or not data.get('input'):
        return jsonify(code=1, message='请输入 BV 号或视频链接'), 400

    try:
        bvid = parse_bvid(data['input'])
    except ValueError as e:
        return jsonify(code=1, message=str(e)), 400

    # 创建任务
    task_id = str(uuid.uuid4())
    task = DownloadTask(
        id=task_id,
        user_id=user_id,
        task_type='video',
        target_id=bvid,
        status='pending'
    )
    db.session.add(task)
    db.session.commit()

    # 提交到队列
    position = submit_task(task_id, current_app._get_current_object(), _socketio)

    logger.info(f'用户 {user_id} 提交视频下载任务: {bvid}, task_id={task_id}')
    return jsonify(code=0, message='任务已提交', data={
        'task_id': task_id,
        'queue_position': position
    })


@download_bp.route('/bangumi', methods=['POST'])
@jwt_required()
def submit_bangumi_download():
    """提交番剧下载任务"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data or not data.get('input'):
        return jsonify(code=1, message='请输入 EP 号或番剧链接'), 400

    try:
        ep_id = parse_ep_id(data['input'])
    except ValueError as e:
        return jsonify(code=1, message=str(e)), 400

    # 检查番剧配额
    today = now_bjt().date()
    quota = BangumiQuota.query.filter_by(user_id=user_id, date=today).first()

    if not quota:
        quota = BangumiQuota(user_id=user_id, date=today, count=0)
        db.session.add(quota)
        db.session.commit()

    # 特权用户仅跳过每日次数限制，不跳过冷却
    is_privileged = (_privileged_user_id is not None and user_id == _privileged_user_id)

    # 检查每日上限
    if not is_privileged and quota.count >= Config.BANGUMI_DAILY_LIMIT:
        return jsonify(code=2, message='今日番剧下载次数已用完，请明天再试'), 429

    # 检查冷却时间（特权用户同样受冷却限制）
    if quota.last_download_at:
        elapsed = (now_bjt().replace(tzinfo=None) - quota.last_download_at).total_seconds()
        if elapsed < Config.BANGUMI_COOLDOWN_SECONDS:
            remaining = int(Config.BANGUMI_COOLDOWN_SECONDS - elapsed)
            return jsonify(code=3, message=f'冷却中，请等待 {remaining} 秒', data={
                'cooldown_remaining_seconds': remaining
            }), 429

    # 更新配额
    quota.count += 1
    quota.last_download_at = now_bjt()
    db.session.commit()

    # 创建任务
    task_id = str(uuid.uuid4())
    task = DownloadTask(
        id=task_id,
        user_id=user_id,
        task_type='bangumi',
        target_id=ep_id,
        status='pending'
    )
    db.session.add(task)
    db.session.commit()

    # 提交到队列
    position = submit_task(task_id, current_app._get_current_object(), _socketio)

    logger.info(f'用户 {user_id} 提交番剧下载任务: ep{ep_id}, task_id={task_id}')
    return jsonify(code=0, message='任务已提交', data={
        'task_id': task_id,
        'queue_position': position
    })


@download_bp.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    """获取当前用户的所有任务列表"""
    user_id = int(get_jwt_identity())
    tasks = DownloadTask.query.filter_by(user_id=user_id).order_by(
        DownloadTask.created_at.desc()
    ).limit(5).all()

    task_list = []
    for t in tasks:
        task_list.append({
            'id': t.id,
            'task_type': t.task_type,
            'target_id': t.target_id,
            'title': t.title,
            'status': t.status,
            'progress': t.progress,
            'file_size': t.file_size,
            'queue_position': t.queue_position,
            'error_message': t.error_message,
            'expires_at': t.expires_at.isoformat() if t.expires_at else None,
            'created_at': t.created_at.isoformat() if t.created_at else None
        })

    return jsonify(code=0, message='success', data=task_list)


@download_bp.route('/tasks/<task_id>', methods=['GET'])
@jwt_required()
def get_task_detail(task_id):
    """获取单个任务详情"""
    user_id = int(get_jwt_identity())
    task = DownloadTask.query.get(task_id)

    if not task or task.user_id != user_id:
        return jsonify(code=1, message='任务不存在'), 404

    return jsonify(code=0, message='success', data={
        'id': task.id,
        'task_type': task.task_type,
        'target_id': task.target_id,
        'title': task.title,
        'status': task.status,
        'progress': task.progress,
        'file_size': task.file_size,
        'queue_position': task.queue_position,
        'error_message': task.error_message,
        'expires_at': task.expires_at.isoformat() if task.expires_at else None,
        'created_at': task.created_at.isoformat() if task.created_at else None
    })


@download_bp.route('/file/<task_id>', methods=['GET'])
@jwt_required()
def download_file(task_id):
    """下载文件"""
    user_id = int(get_jwt_identity())
    task = DownloadTask.query.get(task_id)

    if not task or task.user_id != user_id:
        return jsonify(code=1, message='任务不存在'), 404

    if task.status != 'completed':
        return jsonify(code=1, message='任务尚未完成'), 400

    # 检查是否过期
    if task.expires_at and now_bjt().replace(tzinfo=None) > task.expires_at:
        task.status = 'expired'
        db.session.commit()
        return jsonify(code=1, message='文件已过期'), 410

    if not task.file_path or not os.path.exists(task.file_path):
        return jsonify(code=1, message='文件不存在'), 404

    # 防止路径遍历：确保文件在 DOWNLOAD_DIR 中
    real_path = os.path.realpath(task.file_path)
    real_download_dir = os.path.realpath(Config.DOWNLOAD_DIR)
    if not real_path.startswith(real_download_dir):
        return jsonify(code=1, message='非法文件路径'), 403

    filename = os.path.basename(task.file_path)
    return send_file(real_path, as_attachment=True, download_name=filename)


@download_bp.route('/file-token/<task_id>', methods=['POST'])
@jwt_required()
def create_download_token(task_id):
    """为指定任务生成一个 60 秒有效的下载 token"""
    user_id = int(get_jwt_identity())
    task = DownloadTask.query.get(task_id)

    if not task or task.user_id != user_id:
        return jsonify(code=1, message='任务不存在'), 404
    if task.status != 'completed':
        return jsonify(code=1, message='任务尚未完成'), 400

    # 清理过期 token
    now = time.time()
    expired = [t for t, v in _download_tokens.items() if v[2] < now]
    for t in expired:
        _download_tokens.pop(t, None)

    token = uuid.uuid4().hex
    _download_tokens[token] = (task_id, user_id, now + 60)
    return jsonify(code=0, data={'token': token})


@download_bp.route('/file-by-token/<token>', methods=['GET'])
def download_file_by_token(token):
    """使用短效 token 直接下载文件（无需 Authorization 头）"""
    entry = _download_tokens.pop(token, None)
    if not entry:
        return jsonify(code=1, message='token 无效或已过期'), 403

    task_id, user_id, expire = entry
    if time.time() > expire:
        return jsonify(code=1, message='token 已过期'), 403

    task = DownloadTask.query.get(task_id)
    if not task or task.status != 'completed':
        return jsonify(code=1, message='文件不可用'), 404

    if task.expires_at and now_bjt().replace(tzinfo=None) > task.expires_at:
        task.status = 'expired'
        db.session.commit()
        return jsonify(code=1, message='文件已过期'), 410

    if not task.file_path or not os.path.exists(task.file_path):
        return jsonify(code=1, message='文件不存在'), 404

    real_path = os.path.realpath(task.file_path)
    real_download_dir = os.path.realpath(Config.DOWNLOAD_DIR)
    if not real_path.startswith(real_download_dir):
        return jsonify(code=1, message='非法文件路径'), 403

    filename = os.path.basename(task.file_path)
    return send_file(real_path, as_attachment=True, download_name=filename)


@download_bp.route('/queue-status', methods=['GET'])
@jwt_required()
def queue_status():
    """获取当前队列状态"""
    return jsonify(code=0, message='success', data=get_queue_status())


@download_bp.route('/bangumi-quota', methods=['GET'])
@jwt_required()
def bangumi_quota():
    """获取当前用户今日番剧下载剩余次数和冷却时间"""
    user_id = int(get_jwt_identity())
    today = now_bjt().date()
    quota = BangumiQuota.query.filter_by(user_id=user_id, date=today).first()

    remaining = Config.BANGUMI_DAILY_LIMIT
    cooldown_remaining_seconds = 0

    if quota:
        remaining = max(0, Config.BANGUMI_DAILY_LIMIT - quota.count)
        if quota.last_download_at:
            elapsed = (now_bjt().replace(tzinfo=None) - quota.last_download_at).total_seconds()
            if elapsed < Config.BANGUMI_COOLDOWN_SECONDS:
                cooldown_remaining_seconds = int(Config.BANGUMI_COOLDOWN_SECONDS - elapsed)

    is_privileged = (_privileged_user_id is not None and user_id == _privileged_user_id)

    return jsonify(code=0, message='success', data={
        'remaining': -1 if is_privileged else remaining,
        'daily_limit': Config.BANGUMI_DAILY_LIMIT,
        'cooldown_remaining_seconds': cooldown_remaining_seconds,
        'is_privileged': is_privileged
    })


@download_bp.route('/settings/bili-credentials', methods=['POST'])
@jwt_required()
def update_bili_credentials():
    """更新 B站凭据并授予特权"""
    global _privileged_user_id
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify(code=1, message='请求体不能为空'), 400

    sessdata = data.get('sessdata', '').strip()
    jct = data.get('jct', '').strip()

    if not sessdata or not jct:
        return jsonify(code=1, message='SESSDATA 和 JCT 不能为空'), 400

    # 每个账号设置 cookie 冷却 2 分钟
    cooldown = CookieSettingCooldown.query.filter_by(user_id=user_id).first()
    now = now_bjt().replace(tzinfo=None)
    if cooldown and cooldown.last_set_at:
        elapsed = (now - cooldown.last_set_at).total_seconds()
        if elapsed < COOKIE_SETTING_COOLDOWN_SECONDS:
            remaining = int(COOKIE_SETTING_COOLDOWN_SECONDS - elapsed)
            return jsonify(code=4, message=f'设置过于频繁，请在 {remaining} 秒后重试'), 429

    # 先校验新 cookie，失败则不更新全局配置，也不授予特权
    ok, reason = validate_bili_cookie(sessdata, jct, '293024')
    if not ok:
        return jsonify(code=5, message=f'新 cookie 校验失败：{reason}'), 400

    # 更新运行时配置
    Config.BILI_SESSDATA = sessdata
    Config.BILI_JCT = jct

    # 授予该用户无限番剧下载特权
    _privileged_user_id = user_id

    if not cooldown:
        cooldown = CookieSettingCooldown(user_id=user_id, last_set_at=now_bjt())
        db.session.add(cooldown)
    else:
        cooldown.last_set_at = now_bjt()
    db.session.commit()

    logger.info(f'用户 {user_id} 更新了 B站凭据并通过校验，获得无限番剧下载特权')
    return jsonify(code=0, message='新 cookie 校验通过，凭据已更新，您已获得无限番剧下载特权')
