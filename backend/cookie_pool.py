"""Cookie 池管理模块

每个 cookie 绑定一个独立的任务队列和 worker 线程，保证同账号单线程。
cookie 间的任务通过 round-robin / 随机方式分配。
"""

import queue
import random
import threading
import logging
import time
from datetime import timedelta

from models import db, CookieEntry, DownloadTask, BangumiQuota, now_bjt
from downloader import download_video, download_bangumi, validate_bili_cookie
from config import Config

logger = logging.getLogger(__name__)

# cookie_id -> { 'sessdata', 'bili_jct', 'queue', 'thread', 'last_task_time' }
_workers: dict[int, dict] = {}
_workers_lock = threading.Lock()

# 全局任务队列追踪（用于广播队列状态）
_queue_tasks: list[str] = []
_queue_lock = threading.Lock()

# 每个 cookie 两次任务之间的最小间隔（秒）
PER_COOKIE_INTERVAL = 2

# app & socketio 引用
_app = None
_socketio = None


def init_cookie_pool(app, socketio):
    """应用启动时调用：从数据库加载已有 cookie 并为每个启动 worker"""
    global _app, _socketio
    _app = app
    _socketio = socketio

    with app.app_context():
        entries = CookieEntry.query.all()
        for entry in entries:
            _ensure_worker(entry.id, entry.sessdata, entry.bili_jct)
        logger.info(f'Cookie 池已加载 {len(entries)} 个 cookie')

    # 如果池为空但 .env 有初始 cookie，自动加入池
    if not entries and Config.BILI_SESSDATA and Config.BILI_JCT:
        with app.app_context():
            _add_initial_cookie(Config.BILI_SESSDATA, Config.BILI_JCT)


def _add_initial_cookie(sessdata, bili_jct):
    """将 .env 中的初始 cookie 加入池（user_id=0 表示系统添加）"""
    entry = CookieEntry(sessdata=sessdata, bili_jct=bili_jct, added_by_user_id=0)
    db.session.add(entry)
    db.session.commit()
    _ensure_worker(entry.id, entry.sessdata, entry.bili_jct)
    logger.info(f'已将 .env 初始 cookie 加入池, id={entry.id}')


def _ensure_worker(cookie_id, sessdata, bili_jct):
    """为指定 cookie 创建 worker（如果还没有）"""
    with _workers_lock:
        if cookie_id in _workers:
            return
        q = queue.Queue()
        info = {
            'sessdata': sessdata,
            'bili_jct': bili_jct,
            'queue': q,
            'last_task_time': 0.0,
        }
        t = threading.Thread(target=_cookie_worker, args=(cookie_id, info), daemon=True)
        info['thread'] = t
        _workers[cookie_id] = info
        t.start()
        logger.info(f'Cookie worker 已启动: cookie_id={cookie_id}')


def _cookie_worker(cookie_id, info):
    """单个 cookie 的 worker 循环：从自身队列取任务，两次任务间保持间隔"""
    q: queue.Queue = info['queue']
    while True:
        task_id = q.get()
        try:
            # 限速：距上次任务至少 PER_COOKIE_INTERVAL 秒
            elapsed = time.time() - info['last_task_time']
            if elapsed < PER_COOKIE_INTERVAL:
                time.sleep(PER_COOKIE_INTERVAL - elapsed)

            _process_task(task_id, cookie_id, info['sessdata'], info['bili_jct'])
            info['last_task_time'] = time.time()
        except Exception as e:
            logger.error(f'Cookie worker {cookie_id} 处理任务 {task_id} 异常: {e}')
        finally:
            q.task_done()


# --------------- 公开接口 ---------------

def pool_size():
    """当前池中 cookie 数量"""
    with _workers_lock:
        return len(_workers)


def add_cookie(sessdata, bili_jct, user_id):
    """向池中添加 cookie（调用前已完成校验）。返回 (added: bool, msg: str)"""
    # 检查 bili_jct 是否已存在
    existing = CookieEntry.query.filter_by(bili_jct=bili_jct).first()
    if existing:
        return False, '该 cookie 已存在于 cookie 池中'

    entry = CookieEntry(sessdata=sessdata, bili_jct=bili_jct, added_by_user_id=user_id)
    db.session.add(entry)
    db.session.commit()

    _ensure_worker(entry.id, sessdata, bili_jct)
    logger.info(f'用户 {user_id} 添加 cookie 到池, id={entry.id}, 池大小={pool_size()}')
    return True, 'cookie 已加入池'


def remove_cookie(cookie_id):
    """从池中移除 cookie"""
    entry = CookieEntry.query.get(cookie_id)
    if entry:
        db.session.delete(entry)
        db.session.commit()
    with _workers_lock:
        worker = _workers.pop(cookie_id, None)
        if worker:
            logger.info(f'已移除 cookie worker: cookie_id={cookie_id}')


def get_all_cookies():
    """返回池中所有 cookie 的 (cookie_id, sessdata, bili_jct) 列表"""
    with _workers_lock:
        return [(cid, w['sessdata'], w['bili_jct']) for cid, w in _workers.items()]


def _pick_random_cookie():
    """随机挑选一个 cookie，返回 (cookie_id, sessdata, bili_jct) 或 None"""
    with _workers_lock:
        if not _workers:
            return None
        cid = random.choice(list(_workers.keys()))
        w = _workers[cid]
        return cid, w['sessdata'], w['bili_jct']


def _pick_all_cookies_shuffled():
    """返回打乱顺序的所有 cookie 列表"""
    with _workers_lock:
        items = [(cid, w['sessdata'], w['bili_jct']) for cid, w in _workers.items()]
    random.shuffle(items)
    return items


# --------------- 任务分发 ---------------

def get_queue_status():
    """获取全局队列状态"""
    with _queue_lock:
        return {
            'queue_length': len(_queue_tasks),
            'tasks': [{'task_id': tid, 'position': i + 1} for i, tid in enumerate(_queue_tasks)]
        }


def submit_task(task_id):
    """将任务分配给一个随机 cookie 的 worker"""
    with _queue_lock:
        _queue_tasks.append(task_id)
        position = len(_queue_tasks)

    with _app.app_context():
        task = DownloadTask.query.get(task_id)
        if task:
            task.status = 'queued'
            task.queue_position = position
            db.session.commit()

    cookie = _pick_random_cookie()
    if not cookie:
        # 池为空，标记失败
        with _app.app_context():
            task = DownloadTask.query.get(task_id)
            if task:
                task.status = 'failed'
                task.error_message = 'Cookie 池为空，无法下载'
                db.session.commit()
        _remove_from_queue(task_id)
        _socketio.emit('queue_update', get_queue_status())
        return position

    cookie_id = cookie[0]
    with _workers_lock:
        if cookie_id in _workers:
            _workers[cookie_id]['queue'].put(task_id)

    _socketio.emit('queue_update', get_queue_status())
    logger.info(f'任务 {task_id} 已入队，位置: {position}，分配给 cookie {cookie_id}')
    return position


def _remove_from_queue(task_id):
    with _queue_lock:
        if task_id in _queue_tasks:
            _queue_tasks.remove(task_id)


# --------------- 任务处理（含 cookie 轮替重试） ---------------

def _process_task(task_id, primary_cookie_id, sessdata, bili_jct):
    """处理下载任务，失败时自动使用其他 cookie 重试"""
    with _app.app_context():
        task = DownloadTask.query.get(task_id)
        if not task:
            logger.error(f'任务 {task_id} 不存在')
            _remove_from_queue(task_id)
            return

        user_id = task.user_id
        room = f'user_{user_id}'

        task.status = 'downloading'
        task.progress = 0
        db.session.commit()

        _remove_from_queue(task_id)
        _socketio.emit('queue_update', get_queue_status())

        def make_progress_callback(t):
            def progress_callback(progress, message):
                t.progress = progress
                if progress >= 90:
                    t.status = 'merging'
                db.session.commit()
                _socketio.emit('task_progress', {
                    'task_id': task_id,
                    'progress': progress,
                    'status': t.status,
                    'message': message
                }, room=room)
            return progress_callback

        # 构建 cookie 尝试顺序：主 cookie 在前，其余随机
        cookies_to_try = [(primary_cookie_id, sessdata, bili_jct)]
        for cid, sd, jct in _pick_all_cookies_shuffled():
            if cid != primary_cookie_id:
                cookies_to_try.append((cid, sd, jct))

        last_error = None
        for cid, sd, jct in cookies_to_try:
            try:
                # 重置进度
                task.progress = 0
                task.status = 'downloading'
                db.session.commit()

                if task.task_type == 'video':
                    title, file_path, file_size = download_video(
                        task.target_id, Config.DOWNLOAD_DIR,
                        Config.DOWNLOAD_QUALITY, sd, jct,
                        make_progress_callback(task)
                    )
                else:
                    title, file_path, file_size = download_bangumi(
                        task.target_id, Config.DOWNLOAD_DIR,
                        Config.DOWNLOAD_QUALITY, sd, jct,
                        make_progress_callback(task)
                    )

                # 下载成功
                task.title = title
                task.status = 'completed'
                task.progress = 100
                task.file_path = file_path
                task.file_size = file_size
                task.expires_at = now_bjt() + timedelta(minutes=Config.FILE_EXPIRE_MINUTES)
                db.session.commit()

                _socketio.emit('task_completed', {
                    'task_id': task_id,
                    'title': title,
                    'expires_at': task.expires_at.isoformat(),
                    'file_size': file_size
                }, room=room)

                logger.info(f'任务 {task_id} 用 cookie {cid} 下载成功: {title}')
                return  # 成功，结束

            except Exception as e:
                last_error = e
                logger.warning(f'任务 {task_id} 用 cookie {cid} 失败: {e}，尝试下一个...')
                continue

        # 所有 cookie 都失败
        task.status = 'failed'
        task.error_message = str(last_error)[:500] if last_error else '所有 cookie 均失败'

        if task.task_type == 'bangumi':
            today = now_bjt().date()
            quota_obj = BangumiQuota.query.filter_by(user_id=user_id, date=today).first()
            if quota_obj and quota_obj.count > 0:
                quota_obj.count -= 1
                logger.info(f'番剧任务 {task_id} 失败，已返还配额')

        db.session.commit()

        _socketio.emit('task_failed', {
            'task_id': task_id,
            'error_message': task.error_message
        }, room=room)

        logger.error(f'任务 {task_id} 所有 cookie 均失败')


# --------------- 定期校验 ---------------

def validate_all_cookies():
    """校验池中所有 cookie，移除不合法的"""
    cookies = get_all_cookies()
    removed = 0
    for cid, sd, jct in cookies:
        try:
            ok, reason = validate_bili_cookie(sd, jct, '293024')
            if not ok:
                logger.warning(f'Cookie {cid} 校验失败: {reason}，即将移除')
                with _app.app_context():
                    remove_cookie(cid)
                removed += 1
            else:
                # 更新 last_validated_at
                with _app.app_context():
                    entry = CookieEntry.query.get(cid)
                    if entry:
                        entry.last_validated_at = now_bjt()
                        db.session.commit()
        except Exception as e:
            logger.error(f'校验 cookie {cid} 时异常: {e}')

    logger.info(f'Cookie 池校验完成: 共 {len(cookies)} 个，移除 {removed} 个，剩余 {pool_size()} 个')
    return removed
