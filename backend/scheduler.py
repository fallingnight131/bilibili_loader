"""定时清理过期文件的调度器"""

import os
import logging
import threading
import time

from models import db, DownloadTask, now_bjt

logger = logging.getLogger(__name__)


def start_scheduler(app, socketio):
    """启动后台守护线程，每30秒扫描并清理过期文件"""

    def cleanup_loop():
        logger.info('文件清理调度器已启动')
        while True:
            time.sleep(30)
            try:
                with app.app_context():
                    # 查找已完成且过期的任务
                    now = now_bjt()
                    expired_tasks = DownloadTask.query.filter(
                        DownloadTask.status == 'completed',
                        DownloadTask.expires_at < now
                    ).all()

                    for task in expired_tasks:
                        # 删除物理文件
                        if task.file_path and os.path.exists(task.file_path):
                            try:
                                os.remove(task.file_path)
                                logger.info(f'已清理过期文件: {task.file_path}')
                            except OSError as e:
                                logger.error(f'删除文件失败: {task.file_path}, 错误: {e}')

                        # 更新状态
                        task.status = 'expired'
                        db.session.commit()

                        # 通知用户
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

    t = threading.Thread(target=cleanup_loop, daemon=True)
    t.start()
    return t
