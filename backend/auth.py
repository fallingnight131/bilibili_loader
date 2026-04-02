import logging
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    if not data:
        return jsonify(code=1, message='请求体不能为空'), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')

    # 参数校验
    if not username or not password:
        return jsonify(code=1, message='用户名和密码不能为空'), 400
    if len(username) < 3 or len(username) > 20:
        return jsonify(code=1, message='用户名长度需在3-20字符之间'), 400
    if len(password) < 6 or len(password) > 20:
        return jsonify(code=1, message='密码长度需在6-20字符之间'), 400

    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify(code=1, message='用户名已存在'), 400

    # 创建用户
    user = User(
        username=username,
        password_hash=generate_password_hash(password)
    )
    db.session.add(user)
    db.session.commit()

    logger.info(f'用户注册成功: {username}')
    return jsonify(code=0, message='注册成功')


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    if not data:
        return jsonify(code=1, message='请求体不能为空'), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify(code=1, message='用户名和密码不能为空'), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify(code=1, message='用户名或密码错误'), 400

    # 生成 JWT token
    access_token = create_access_token(identity=str(user.id))
    logger.info(f'用户登录成功: {username}')
    return jsonify(code=0, message='登录成功', data={'access_token': access_token})


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """获取当前用户信息"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify(code=1, message='用户不存在'), 404

    return jsonify(code=0, message='success', data={
        'id': user.id,
        'username': user.username,
        'created_at': user.created_at.isoformat() if user.created_at else None
    })
