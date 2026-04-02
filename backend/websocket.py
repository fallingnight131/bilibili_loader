"""Flask-SocketIO 事件处理（进度推送、排队状态）"""

import logging
from flask_socketio import SocketIO, join_room
from flask_jwt_extended import decode_token

logger = logging.getLogger(__name__)

socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')


@socketio.on('connect')
def handle_connect(auth=None):
    """客户端连接时，通过 JWT 加入用户专属 room"""
    if auth and auth.get('token'):
        try:
            token_data = decode_token(auth['token'])
            user_id = token_data['sub']
            room = f'user_{user_id}'
            join_room(room)
            logger.info(f'用户 {user_id} 的 WebSocket 已连接，加入 room: {room}')
        except Exception as e:
            logger.warning(f'WebSocket 认证失败: {e}')
    else:
        logger.warning('WebSocket 连接缺少认证信息')


@socketio.on('disconnect')
def handle_disconnect():
    logger.info('WebSocket 客户端断开连接')
