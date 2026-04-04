"""定时清理过期文件 & 定期校验 Cookie 池的调度器"""

import os
import logging
import threading
import time
import random

from models import db, DownloadTask, now_bjt
from cookie_pool import validate_all_cookies

logger = logging.getLogger(__name__)


def _next_cookie_check_interval():
    """返回下一次 cookie 校验间隔（秒），约 3 天 ± 随机偏移"""
    base = 3 * 24 * 3600  # 3 天
    jitter = random.randint(-6 * 3600, 6 * 3600)  # ±6 小时
    return base + jitter


def start_scheduler(app, socketio):
    """启动后台守护线程"""

    def cleanup_loop():
        logger.info('文件清理调度器已启动')
        while True:
            time.sleep(30)
            try:
                with app.app_context():
                    now = now_bjt().replace(tzinfo=None)
                    expired_tasks = DownloadTask.query.filter(
                        DownloadTask.status == 'completed',
                        DownloadTask.expires_at < now
                    ).all()

                    for task in expired_tasks:
                        if task.file_path and os.path.exists(task.file_path):
                            try:
                                os.remove(task.file_path)
                                logger.info(f'已清理过期文件: {task.file_path}')
                            except OSError as e:
                                logger.error(f'删除文件失败: {task.file_path}, 错误: {e}')

                        task.status = 'expired'
                        db.session.commit()

                        room = f'user_{task.user_id}'
                        socketio.emit('task_progress', {
                            'task_id': task.id,
                            'progress': task.progress,
                            'status': 'expired',
                            'message': '文件已过期'
                        }, room=room)

                    if expired_tasks:
                        logger.info(f'本次清理了 {len(expired_tasks)} 个过期任务')

            except Exception as e:
                logger.error(f'清理调度器异常: {e}')

    def cookie_check_loop():
        logger.info('Cookie 校验调度器已启动')
        while True:
            interval = _next_cookie_check_interval()
            logger.info(f'下次 cookie 校验将在 {interval / 3600:.1f} 小时后')
            time.sleep(interval)
            try:
                with app.app_context():
                    removed = validate_all_cookies()
                    logger.info(f'Cookie 定期校验完成，移除 {removed} 个无效 cookie')
            except Exception as e:
                logger.error(f'Cookie 校验调度器异常: {e}')

    t1 = threading.Thread(target=cleanup_loop, daemon=True)
    t1.start()

    t2 = threading.Thread(target=cookie_check_loop, daemon=True)
    t2.start()

    return t1, t2
