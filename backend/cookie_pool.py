"""Cookie 池管理模块

每个 cookie 绑定一个独立的任务队列和 worker 线程，保证同账号单线程。
cookie 间的任务通过 round-robin / 随机方式分配。
"""

import queue
import random
import threading
import logging
import time
import os
from datetime import timedelta

from models import db, CookieEntry, DownloadTask, BangumiQuota, now_bjt
from downloader import download_video, download_bangumi, validate_bili_cookie, DownloadCancelled
from config import Config

logger = logging.getLogger(__name__)

# cookie_id -> { 'sessdata', 'bili_jct', 'queue', 'thread', 'last_task_time', 'user_agent' }
_workers: dict[int, dict] = {}
_workers_lock = threading.Lock()

# 全局任务队列追踪（用于广播队列状态）
_queue_tasks: list[str] = []
_queue_lock = threading.Lock()

# 已取消的任务 ID 集合
_cancelled_tasks: set[str] = set()
_cancelled_lock = threading.Lock()

# 提供过合法 cookie 的特权用户 ID 集合（无限番剧下载）
_privileged_users: set[int] = set()
_privileged_lock = threading.Lock()

# 每个 cookie 两次任务之间的最小间隔（秒）
PER_COOKIE_INTERVAL = 2

# app & socketio 引用
_app = None
_socketio = None

# User-Agent 模板列表
_UA_TEMPLATES = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{ver}.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{ver}.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{ver}.0.0.0 Safari/537.36 Edg/{ver}.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{ver}.0.0.0 Safari/537.36",
]


def _generate_user_agent(cookie_id):
    """为每个 cookie 生成唯一的 User-Agent"""
    template = _UA_TEMPLATES[cookie_id % len(_UA_TEMPLATES)]
    chrome_ver = 120 + (cookie_id * 7) % 17  # 120-136
    return template.format(ver=chrome_ver)


def init_cookie_pool(app, socketio):
    """应用启动时调用：从数据库加载已有 cookie 并为每个启动 worker"""
    global _app, _socketio
    _app = app
    _socketio = socketio

    with app.app_context():
        entries = CookieEntry.query.all()
        for entry in entries:
            _ensure_worker(entry.id, entry.sessdata, entry.bili_jct)
            # 初始化特权用户集合（user_id=0 是系统添加，不授予特权）
            if entry.added_by_user_id and entry.added_by_user_id > 0:
                with _privileged_lock:
                    _privileged_users.add(entry.added_by_user_id)
        logger.info(f'Cookie 池已加载 {len(entries)} 个 cookie，特权用户: {_privileged_users}')

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
        ua = _generate_user_agent(cookie_id)
        info = {
            'sessdata': sessdata,
            'bili_jct': bili_jct,
            'queue': q,
            'last_task_time': 0.0,
            'user_agent': ua,
        }
        t = threading.Thread(target=_cookie_worker, args=(cookie_id, info), daemon=True)
        info['thread'] = t
        _workers[cookie_id] = info
        t.start()
        logger.info(f'Cookie worker 已启动: cookie_id={cookie_id}, UA={ua[:60]}...')


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
        # cookie 已存在，但仍授予用户特权
        with _privileged_lock:
            _privileged_users.add(user_id)
        return False, '该 cookie 已存在于 cookie 池中'

    entry = CookieEntry(sessdata=sessdata, bili_jct=bili_jct, added_by_user_id=user_id)
    db.session.add(entry)
    db.session.commit()

    _ensure_worker(entry.id, sessdata, bili_jct)
    with _privileged_lock:
        _privileged_users.add(user_id)
    logger.info(f'用户 {user_id} 添加 cookie 到池, id={entry.id}, 池大小={pool_size()}')
    return True, 'cookie 已加入池'


def remove_cookie(cookie_id):
    """从池中移除 cookie，并检查是否需要撤销对应用户的特权"""
    entry = CookieEntry.query.get(cookie_id)
    removed_user_id = entry.added_by_user_id if entry else None
    if entry:
        db.session.delete(entry)
        db.session.commit()
    with _workers_lock:
        worker = _workers.pop(cookie_id, None)
        if worker:
            logger.info(f'已移除 cookie worker: cookie_id={cookie_id}')

    # 检查该用户是否还有其他 cookie 在池中，若无则撤销特权
    if removed_user_id and removed_user_id > 0:
        remaining = CookieEntry.query.filter_by(added_by_user_id=removed_user_id).count()
        if remaining == 0:
            with _privileged_lock:
                _privileged_users.discard(removed_user_id)
            logger.info(f'用户 {removed_user_id} 的所有 cookie 已失效，已撤销特权')


def get_all_cookies():
    """返回池中所有 cookie 的 (cookie_id, sessdata, bili_jct) 列表"""
    with _workers_lock:
        return [(cid, w['sessdata'], w['bili_jct']) for cid, w in _workers.items()]


def _pick_random_cookie():
    """随机挑选一个 cookie，返回 (cookie_id, sessdata, bili_jct, user_agent) 或 None"""
    with _workers_lock:
        if not _workers:
            return None
        cid = random.choice(list(_workers.keys()))
        w = _workers[cid]
        return cid, w['sessdata'], w['bili_jct'], w['user_agent']


def _pick_all_cookies_shuffled():
    """返回打乱顺序的所有 cookie 列表"""
    with _workers_lock:
        items = [(cid, w['sessdata'], w['bili_jct'], w['user_agent']) for cid, w in _workers.items()]
    random.shuffle(items)
    return items


def is_privileged(user_id):
    """检查用户是否拥有特权（提供过合法 cookie）"""
    with _privileged_lock:
        return user_id in _privileged_users


def cancel_task(task_id):
    """标记任务为已取消"""
    with _cancelled_lock:
        _cancelled_tasks.add(task_id)
    logger.info(f'任务 {task_id} 已被标记为取消')


def is_task_cancelled(task_id):
    """检查任务是否已被取消"""
    with _cancelled_lock:
        return task_id in _cancelled_tasks


def _clear_cancelled(task_id):
    """清除取消标记"""
    with _cancelled_lock:
        _cancelled_tasks.discard(task_id)


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

        # 检查是否已被取消
        if is_task_cancelled(task_id):
            task.status = 'cancelled'
            task.error_message = '任务已取消'
            db.session.commit()
            _remove_from_queue(task_id)
            _clear_cancelled(task_id)
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

        def cancel_check():
            return is_task_cancelled(task_id)

        # 获取主 cookie 的 user_agent
        with _workers_lock:
            primary_ua = _workers.get(primary_cookie_id, {}).get('user_agent')

        # 构建 cookie 尝试顺序：主 cookie 在前，其余随机
        cookies_to_try = [(primary_cookie_id, sessdata, bili_jct, primary_ua)]
        for cid, sd, jct, ua in _pick_all_cookies_shuffled():
            if cid != primary_cookie_id:
                cookies_to_try.append((cid, sd, jct, ua))

        last_error = None
        for cid, sd, jct, ua in cookies_to_try:
            try:
                # 重置进度
                task.progress = 0
                task.status = 'downloading'
                db.session.commit()

                if task.task_type == 'video':
                    title, file_path, file_size = download_video(
                        task.target_id, Config.DOWNLOAD_DIR,
                        Config.DOWNLOAD_QUALITY, sd, jct,
                        make_progress_callback(task),
                        user_agent=ua, cancel_check=cancel_check
                    )
                else:
                    title, file_path, file_size = download_bangumi(
                        task.target_id, Config.DOWNLOAD_DIR,
                        Config.DOWNLOAD_QUALITY, sd, jct,
                        make_progress_callback(task),
                        user_agent=ua, cancel_check=cancel_check
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

            except DownloadCancelled:
                # 用户取消，清理并退出
                task.status = 'cancelled'
                task.error_message = '已取消下载'
                # 返还番剧配额
                if task.task_type == 'bangumi':
                    today = now_bjt().date()
                    quota_obj = BangumiQuota.query.filter_by(user_id=user_id, date=today).first()
                    if quota_obj and quota_obj.count > 0:
                        quota_obj.count -= 1
                db.session.commit()
                _clear_cancelled(task_id)

                _socketio.emit('task_progress', {
                    'task_id': task_id,
                    'progress': 0,
                    'status': 'cancelled',
                    'message': '已取消下载'
                }, room=room)
                logger.info(f'任务 {task_id} 已被用户取消')
                return

            except Exception as e:
                last_error = e
                logger.warning(f'任务 {task_id} 用 cookie {cid} 失败: {e}，校验该 cookie...')

                # 立即校验失败的 cookie 是否仍然有效
                try:
                    ok, reason = validate_bili_cookie(sd, jct, '293024')
                    if not ok:
                        logger.warning(f'Cookie {cid} 校验失败: {reason}，移除该 cookie')
                        remove_cookie(cid)
                except Exception as ve:
                    logger.error(f'校验 cookie {cid} 时异常: {ve}')

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
