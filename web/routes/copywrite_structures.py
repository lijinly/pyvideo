import uuid
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from domains.copywrite_structures import cpy_store
from web.models import ErrorCode, make_response
from utils.logs import setup_logger

# 创建蓝图
copywrite_bp = Blueprint('copywrite', __name__)

# 初始化cpy_store实例
copywrite_store = cpy_store()

# 配置日志记录
logger = setup_logger(name=__name__)

@copywrite_bp.route('/load', methods=['GET'])
@jwt_required()
def get_copywrites():
    """
    获取用户的文案结构列表
    """
    # 获取当前用户ID
    user_id = get_jwt_identity()
    
    # 调用cpy_store类中的load_copywrites方法
    results = copywrite_store.load_copywrites(user_id)
    
    return jsonify(make_response(ErrorCode.SUCCESS, {
        'data': results,
        'count': len(results)
    })), 200


@copywrite_bp.route('/save', methods=['POST'])
@jwt_required()
def save_copywrite():
    """
    保存或更新文案结构
    """
    # 获取当前用户ID
    user_id = get_jwt_identity()
    
    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, '请求数据不能为空')), 400
    
    if not isinstance(data, dict):
        return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, 'body必须是一个对象')), 400
        
    # 检查body中的必需字段
    if 'rhythm' not in data or not isinstance(data['rhythm'], str):
        return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, 'body.Rhythm是必需的字符串字段')), 400
        
    if 'style_tone' not in data or not isinstance(data['style_tone'], str):
        return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, 'body.style_tone是必需的字符串字段')), 400
        
    if 'structure' not in data or not isinstance(data['structure'], list):
        return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, 'body.structure是必需的数组字段')), 400
        
    # 校验structure数组中的每个元素
    for i, item in enumerate(data['structure']):
        if not isinstance(item, dict):
            return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, f'body.structure[{i}]必须是一个对象')), 400
            
        if 'description' not in item or not isinstance(item['description'], str):
            return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, f'body.structure[{i}].description是必需的字符串字段')), 400
            
        if 'keyword' not in item or not isinstance(item['keyword'], str):
            return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, f'body.structure[{i}].keyword是必需的字符串字段')), 400
        
        if 'seconds' not in item or not isinstance(item['seconds'], str):
            return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, f'body.structure[{i}].seconds是必需的字符串字段')), 400
    
    
    # 调用cpy_store类中的save_copywrite方法
    doc_id = copywrite_store.save_copywrite(user_id, data)
    
    return jsonify(make_response(ErrorCode.SUCCESS, {"doc_id": doc_id})), 201


@copywrite_bp.route('/delete/<doc_id>', methods=['DELETE'])
@jwt_required()
def delete_copywrite(doc_id):
    """
    删除指定的文案结构
    """
    # 验证doc_id格式
    try:
        uuid.UUID(doc_id)
    except ValueError:
        return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, '无效的文档ID格式')), 400
        
    # 调用cpy_store类中的delete_copywrite方法
    copywrite_store.delete_copywrite(doc_id)
    
    return jsonify(make_response(ErrorCode.SUCCESS)), 200