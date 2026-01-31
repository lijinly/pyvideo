from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    jwt_required, create_access_token, create_refresh_token,
    get_jwt_identity, get_jwt
)
from werkzeug.security import check_password_hash
import logging

from web.models.users import User
from utils.kv_db import kv_db_lmdb
from web.models import ErrorCode, make_response
from utils.logs import setup_logger

# 创建蓝图（指定蓝图名称和模块）
auth_bp = Blueprint('auth', __name__) 

# 配置日志记录
logger = setup_logger(name=__name__)

# 登录接口
@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    # 验证用户
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify(make_response(ErrorCode.INVALID_CREDENTIALS)), 401

    # 生成令牌，使用用户ID作为身份标识
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    return jsonify(make_response(ErrorCode.SUCCESS, {
        "access_token": access_token,
        "refresh_token": refresh_token
    })), 200


# 刷新 access token
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    # 根据用户ID查找用户
    user = User.query.get(current_user_id)
    if not user:
        return jsonify(make_response(ErrorCode.USER_NOT_FOUND)), 404
    new_access_token = create_access_token(identity=current_user_id)
    return jsonify(make_response(ErrorCode.SUCCESS, {
        "access_token": new_access_token
    })), 200


# 登出（使 access token 失效）
@auth_bp.route('/logout', methods=['DELETE'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']  # 获取令牌唯一标识 
    
    with kv_db_lmdb() as db:
        db.put(f"{jti}".encode(), f"{jti}".encode(), serialize=False)
        
    return jsonify(make_response(ErrorCode.SUCCESS, None, "access token 已失效")), 200


# 获取当前登录用户信息
@auth_bp.route('/get_current_user', methods=['GET'])
@jwt_required()
def get_current_user(): 
    # 获取当前用户ID
    current_user_id = get_jwt_identity()
    # 根据用户ID查找用户
    user = User.query.get(current_user_id)
    if not user:
        return jsonify(make_response(ErrorCode.USER_NOT_FOUND)), 404
        
    # 返回用户信息（不包含密码等敏感信息）
    user_info = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }
    return jsonify(make_response(ErrorCode.SUCCESS, user_info)), 200