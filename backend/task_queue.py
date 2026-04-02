"""下载任务队列管理（单线程 worker）"""

import uuid
import queue
import threading
import logging
import os
from datetime import timedelta

from models import db, DownloadTask, BangumiQuota, now_bjt
from downloader import download_video, download_bangumi
from config import Config

logger = logging.getLogger(__name__)

# 全局任务队列
task_queue = queue.Queue()
# 当前队列中的任务ID列表（用于追踪位置）
queue_tasks = []
queue_lock = threading.Lock()


def get_queue_status():
    """获取当前队列状态"""
    with queue_lock:
        return {
            'queue_length': len(queue_tasks),
            'tasks': [{'task_id': tid, 'position': i + 1} for i, tid in enumerate(queue_tasks)]
        }


def submit_task(task_id, app, socketio):
    """将任务放入队列"""
    with queue_lock:
        queue_tasks.append(task_id)
        position = len(queue_tasks)

    # 更新数据库状态
    with app.app_context():
        task = DownloadTask.query.get(task_id)
        if task:
            task.status = 'queued'
            task.queue_position = position
            db.session.commit()

    # 放入队列
    task_queue.put((task_id, app, socketio))

    # 广播队列状态
    socketio.emit('queue_update', get_queue_status())

    logger.info(f'任务 {task_id} 已入队，位置: {position}')
    return position


def _remove_from_queue(task_id):
    """从队列追踪列表中移除任务"""
    with queue_lock:
        if task_id in queue_tasks:
            queue_tasks.remove(task_id)


def _process_task(task_id, app, socketio):
    """处理单个下载任务"""
    with app.app_context():
        task = DownloadTask.query.get(task_id)
        if not task:
            logger.error(f'任务 {task_id} 不存在')
            return

        user_id = task.user_id
        room = f'user_{user_id}'

        # 更新状态为下载中
        task.status = 'downloading'
        task.progress = 0
        db.session.commit()

        # 从队列追踪列表移除
        _remove_from_queue(task_id)
        socketio.emit('queue_update', get_queue_status())

        # 进度回调
        def progress_callback(progress, message):
            task.progress = progress
            if progress >= 90:
                task.status = 'merging'
            db.session.commit()
            socketio.emit('task_progress', {
                'task_id': task_id,
                'progress': progress,
                'status': task.status,
                'message': message
            }, room=room)

        try:
            if task.task_type == 'video':
                title, file_path, file_size = download_video(
                    task.target_id,
                    Config.DOWNLOAD_DIR,
                    Config.DOWNLOAD_QUALITY,
                    Config.BILI_SESSDATA,
                    Config.BILI_JCT,
                    progress_callback
                )
            else:
                title, file_path, file_size = download_bangumi(
                    task.target_id,
                    Config.DOWNLOAD_DIR,
                    Config.DOWNLOAD_QUALITY,
                    Config.BILI_SESSDATA,
                    Config.BILI_JCT,
                    progress_callback
                )

            # 下载成功
            task.title = title
            task.status = 'completed'
            task.progress = 100
            task.file_path = file_path
            task.file_size = file_size
            task.expires_at = now_bjt() + timedelta(minutes=Config.FILE_EXPIRE_MINUTES)
            db.session.commit()

            socketio.emit('task_completed', {
                'task_id': task_id,
                'title': title,
                'expires_at': task.expires_at.isoformat(),
                'file_size': file_size
            }, room=room)

            logger.info(f'任务 {task_id} 下载完成: {title}')

        except Exception as e:
            # 下载失败
            task.status = 'failed'
            task.error_message = str(e)[:500]

            # 番剧失败时返还配额并重置冷却
            if task.task_type == 'bangumi':
                today = now_bjt().date()
                quota = BangumiQuota.query.filter_by(user_id=user_id, date=today).first()
                if quota and quota.count > 0:
                    quota.count -= 1
                    quota.last_download_at = None
                    logger.info(f'番剧任务 {task_id} 失败，已返还配额，当前剩余: {quota.count}')

            db.session.commit()

            socketio.emit('task_failed', {
                'task_id': task_id,
                'error_message': str(e)[:500]
            }, room=room)

            logger.error(f'任务 {task_id} 下载失败: {e}')


def start_worker():
    """启动 worker 线程"""
    def worker():
        logger.info('下载 Worker 线程已启动')
        while True:
            task_id, app, socketio = task_queue.get()
            try:
                _process_task(task_id, app, socketio)
            except Exception as e:
                logger.error(f'Worker 处理任务异常: {e}')
            finally:
                task_queue.task_done()

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    return t
