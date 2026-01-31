import os
from pathlib import Path
from flask import Flask, jsonify, send_from_directory,abort
from .extensions import  jwt,sql_db
from .config import Config,DevelopmentConfig,ProductionConfig

from web.routes.auth import auth_bp
from web.routes.asset import asset_bp
from web.routes.static_file import static_bp
from web.routes.copywrite_structures import copywrite_bp
from web.routes.marketing import marketing_bp
from web.routes.avatar import avatar_bp
from web.int_user_data import init_data
from sqlalchemy import inspect
from utils.kv_db import kv_db_lmdb
from web.models import ErrorCode, make_response
import logging
from utils.logs import setup_logger
from werkzeug.exceptions import UnsupportedMediaType, HTTPException

# 配置日志记录
logger = setup_logger(name=__name__)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)   
   
        
    # 初始化扩展
    jwt.init_app(app)     
    sql_db.init_app(app)
    
    # 添加已撤销 token 检查回调
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        try:
            with kv_db_lmdb() as db:
                return db.get(f"{jti}".encode(), deserialize=False) is not None
        except Exception as e:
            # 发生异常时，默认认为token无效，增强安全性
            return True
    
    # 统一被撤销token的错误响应格式
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return make_response(ErrorCode.TOKEN_REVOKED), 401
    
    # 统一过期token的错误响应格式
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return make_response(ErrorCode.TOKEN_EXPIRED), 401
    
    # 处理不支持的媒体类型异常（如Content-Type不是application/json）
    @app.errorhandler(UnsupportedMediaType)
    def handle_unsupported_media_type(e):
        # 不记录日志，直接返回错误响应
        return jsonify(make_response(ErrorCode.VALIDATION_ERROR, sub_message="请求的Content-Type必须是'application/json'")), 400
    
    # 处理404错误
    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify(make_response(ErrorCode.ASSET_NOT_FOUND, sub_message="请求的资源未找到")), 404
    
    # 全局异常处理
    @app.errorhandler(Exception)
    def handle_exception(e):
        # 记录异常日志（包含详细信息）
        logger.error(f"未处理的异常: {str(e)}", exc_info=True)
        # 返回统一的错误响应（不包含详细错误信息）
        return jsonify(make_response(ErrorCode.INTERNAL_ERROR)), 500
    
    # 添加favicon.ico路由处理
    @app.route('/favicon.ico')
    def favicon():
        return '', 204

    # 注册API路由
    # 注册蓝图（所有路由会自动带上指定前缀）
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(asset_bp, url_prefix='/asset')
    app.register_blueprint(static_bp, url_prefix='/static')
    app.register_blueprint(copywrite_bp, url_prefix='/copywrite_structures')
    app.register_blueprint(marketing_bp, url_prefix='/marketing')
    app.register_blueprint(avatar_bp, url_prefix='/avatar') 
    # 创建数据库表
    with app.app_context():
        inspector = inspect(sql_db.engine)
        # 检查是否缺少任何表
        existing_tables = inspector.get_table_names()
        required_tables = ['users', 'user_files']
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        # 如果有缺失的表，则创建所有表
        if missing_tables:
            sql_db.create_all()  # 创建所有表
            # 如果users表是新创建的，则初始化用户数据
            if 'users' in missing_tables:
                init_data() 
   
      
     # 首页路由
    @app.route('/')
    def index():
        return "Flask  is running! Visit /api/users to get started."
    
    # 请求结束时移除数据库会话
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        sql_db.session.remove()
    

    
    return app