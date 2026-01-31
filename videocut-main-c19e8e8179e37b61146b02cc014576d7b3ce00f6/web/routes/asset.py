import time
import uuid
import random
import os
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify
from utils.logs import setup_logger
from web.extensions import sql_db
from web.models.users import UserFile
from domains.asset_index import AssetIndex
from web.models import ErrorCode, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity

# 创建蓝图（指定蓝图名称和模块）
asset_bp = Blueprint('asset', __name__)

# 配置日志记录
logger = setup_logger(name=__name__)


def generate_filename(original_filename):
    """生成符合日期-随机数格式的文件名"""
    # 获取文件扩展名
    ext = Path(original_filename).suffix

    # 获取当前日期和时间，精确到秒
    current_datetime = datetime.now().strftime("%Y%m%d%H%M%S")

    # 生成随机数
    random_number = str(random.randint(100, 999))

    # 组合生成新文件名
    new_filename = f"{current_datetime}-{random_number}{ext}"
    return new_filename


def create_temp_dirs(userid, batch_number):
    """创建目录结构"""
    temp_dir = Path(".asset_space") / "uploads" / str(userid) / batch_number    
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def get_files_in_folder(userid, batch_number):
    """获取指定文件夹中的所有文件信息"""
    folder_path = Path(".asset_space") / "uploads" / str(userid) / batch_number    
    files_info = []
    
    if folder_path.exists() and folder_path.is_dir():
        for file_path in folder_path.iterdir():
            if file_path.is_file():
                # 过滤掉.txt和.json文件
                if file_path.suffix.lower() in ['.txt', '.json']:
                    continue
                    
                stat = file_path.stat()
                files_info.append({
                    'filename': file_path.name,
                    'size': stat.st_size,
                    'modified_time': stat.st_mtime,
                    'access_path': f"/static/uploads/{userid}/{batch_number}/{file_path.name}"
                })
    
    # 按文件名字典序排序
    files_info.sort(key=lambda x: x['filename'])
    return files_info


def get_user_folders(userid):
    """获取用户的所有文件夹信息"""
    # 查询用户的所有文件夹记录
    folders = UserFile.query.filter_by(userid=userid).all()
    folders_info = []
    
    for folder in folders:
        folder_info = {
            'folder_id': folder.batch_number,
            'folder_name': folder.folder_name,
            'file_count': folder.file_count,
            'upload_time': folder.upload_time
        }
        folders_info.append(folder_info)
    
    return folders_info


@asset_bp.route('/folder', methods=['POST'])
@jwt_required()
def create_folder():
    """创建新文件夹接口"""
    # 获取当前用户ID
    userid = get_jwt_identity()
    
    # 获取请求数据
    data = request.get_json()
    folder_name = data.get('folder_name')
    
    if not folder_name:
        return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, '文件夹名称不能为空')), 400
    
    # 生成文件夹ID
    folder_id = f"{userid}-{str(uuid.uuid4().hex[:8])}"
    
    # 创建文件夹目录
    folder_path = create_temp_dirs(userid, folder_id)
    
    # 保存文件夹信息到数据库
    new_folder = UserFile()
    new_folder.file_path = str(folder_path)
    new_folder.userid = userid
    new_folder.file_count = 0
    new_folder.batch_number = folder_id
    new_folder.folder_name = folder_name
    new_folder.upload_time = time.time()
    sql_db.session.add(new_folder)
    sql_db.session.commit()
    
    # 返回文件夹ID
    response_data = {
        'folder_id': folder_id,
        'folder_name': folder_name,
        'access_path': f"/static/uploads/{userid}/{folder_id}"
    }
    
    return jsonify(make_response(ErrorCode.SUCCESS, response_data)), 201


@asset_bp.route('/folders', methods=['GET'])
@jwt_required()
def get_folders_with_files():
    """获取用户下的所有文件夹及文件数据接口"""
    # 获取当前用户ID
    userid = get_jwt_identity()
    
    # 获取用户的所有文件夹
    folders = UserFile.query.filter_by(userid=userid).all()
    result = []
    
    for folder in folders:
        # 获取文件夹中的文件信息
        files_info = get_files_in_folder(userid, folder.batch_number)
        
        folder_data = {
            'folder_id': folder.batch_number,
            'folder_name': folder.folder_name,
            'file_count': folder.file_count,
            'upload_time': folder.upload_time,
            'files': files_info
        }
        result.append(folder_data)
    
    return jsonify(make_response(ErrorCode.SUCCESS, result)), 200


# 由于已经从web.utils导入了get_current_user_id，所以可以删除本地定义的函数


@asset_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """上传文件接口"""
    # 检查是否有文件在请求中
    if 'file' not in request.files:
        return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, '没有文件')), 400

    files = request.files.getlist('file')
    
    # 获取表单数据中的folder_id参数
    folder_id = request.form.get('folder_id', None)

    # 获取当前用户ID
    userid = get_jwt_identity()

    # 处理批次号：如果提供了folder_id，则直接使用；否则生成新的批次号
    if folder_id:
        batch_number = folder_id
    else:
        batch_number = f"{userid}-{str(uuid.uuid4().hex[:8])}"

    # 先保存所有文件到磁盘
    saved_files = []
    batch_dir = create_temp_dirs(userid, batch_number)

    for file in files:
        # 检查文件名
        if file.filename == '':
            continue  # 跳过空文件名

        if file:
            # 生成新的文件名
            new_filename = generate_filename(file.filename)

            # 保存文件到目录
            file_path = batch_dir / new_filename
            file.save(str(file_path))

            saved_files.append({
                'original_filename': file.filename,
                'new_filename': new_filename,
                'file_path': str(file_path)
            })

    if not saved_files:
        return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, '没有有效的文件')), 400

    # 为整个批次保存一条记录到数据库
    # 取第一个文件的目录路径作为批次的代表路径
    representative_file_path = str(Path(saved_files[0]['file_path']).parent) if saved_files else ""
    
    # 查询是否是更新现有文件夹
    existing_folder = UserFile.query.filter_by(batch_number=batch_number, userid=userid).first()
    if existing_folder:
        # 更新现有文件夹的文件数量
        existing_folder.file_count += len(saved_files)
        existing_folder.upload_time = time.time()
        new_file = existing_folder
    else:
        # 创建新的文件夹记录
        new_file = UserFile()
        new_file.file_path = representative_file_path
        new_file.userid = userid
        new_file.file_count = len(saved_files)
        new_file.batch_number = batch_number
        new_file.upload_time = time.time()
        sql_db.session.add(new_file)
    
    sql_db.session.commit()

    # 构建所有上传文件的响应信息
    uploaded_files = []
    for saved_file in saved_files:
        # 从文件路径中提取文件名
        file_name = Path(saved_file['file_path']).name
        # 使用用户ID、批次号和文件名构建访问URL路径
        access_path = f"/static/uploads/{userid}/{batch_number}/{file_name}"
        uploaded_files.append({
            'message': '文件上传成功',
            'original_filename': saved_file['original_filename'],
            'file_path': access_path,
            'batch_number': batch_number,
        })

    # 调用AssetIndex对上传的文件进行索引处理
    asset_index = AssetIndex()
    for saved_file in saved_files:
        try:
            asset_index.build_index(os.path.dirname(saved_file['file_path']))
        except Exception as e:
            logger.error(f"Failed to index file {saved_file['file_path']}: {e}")

    return jsonify(make_response(ErrorCode.SUCCESS, uploaded_files)), 201


# @asset_bp.route('/folder/<folder_id>', methods=['DELETE'])
# @jwt_required()
# def delete_folder(folder_id):
#     """删除文件夹接口"""
#     # 获取当前用户ID
#     userid = get_jwt_identity()
    
#     # 查询要删除的文件夹
#     folder = UserFile.query.filter_by(batch_number=folder_id, userid=userid).first()
    
#     if not folder:
#         return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, '文件夹不存在或无权限访问')), 404
    
#     # 构建文件夹路径
#     folder_path = Path(".asset_space") / "uploads" / str(userid) / folder_id
    
#     # 删除文件夹及其所有内容
#     if folder_path.exists() and folder_path.is_dir():
#         import shutil
#         try:
#             shutil.rmtree(folder_path)
#         except Exception as e:
#             logger.error(f"Failed to delete folder {folder_path}: {e}")
#             return jsonify(make_response(ErrorCode.INTERNAL_ERROR, None, '删除文件夹失败')), 500
    
#     # 从数据库中删除文件夹记录
#     sql_db.session.delete(folder)
#     sql_db.session.commit()
    
#     return jsonify(make_response(ErrorCode.SUCCESS, None, '文件夹删除成功')), 200


# @asset_bp.route('/file', methods=['DELETE'])
# @jwt_required()
# def delete_file():
#     """删除文件接口"""
#     # 获取当前用户ID
#     userid = get_jwt_identity()
    
#     # 获取请求数据
#     data = request.get_json()
#     folder_id = data.get('folder_id')
#     filename = data.get('filename')
    
#     if not folder_id:
#         return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, '缺少文件夹ID')), 400
    
#     if not filename:
#         return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, '缺少文件名')), 400
    
#     # 查询文件夹
#     folder = UserFile.query.filter_by(batch_number=folder_id, userid=userid).first()
    
#     if not folder:
#         return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, '文件夹不存在或无权限访问')), 404
    
#     # 构建文件路径
#     file_path = Path(".asset_space") / "uploads" / str(userid) / folder_id / filename
    
#     # 检查文件是否存在
#     if not file_path.exists() or not file_path.is_file():
#         return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, '文件不存在')), 404
    
#     # 删除文件
#     try:
#         file_path.unlink()
#     except Exception as e:
#         logger.error(f"Failed to delete file {file_path}: {e}")
#         return jsonify(make_response(ErrorCode.INTERNAL_ERROR, None, '删除文件失败')), 500
    
#     # 更新数据库中的文件数量
#     if folder.file_count > 0:
#         folder.file_count -= 1
#         folder.upload_time = time.time()
#         sql_db.session.commit()
    
#     return jsonify(make_response(ErrorCode.SUCCESS, None, '文件删除成功')), 200
