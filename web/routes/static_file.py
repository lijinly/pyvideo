from flask import Blueprint, send_from_directory, abort
from flask_jwt_extended import jwt_required
from pathlib import Path

# 创建蓝图
static_bp = Blueprint('static', __name__)

# 添加静态文件访问路由，只开放.asset_space/uploads文件夹
@static_bp.route('/uploads/<path:filename>')
@jwt_required()
def get_uploads_files(filename):
    # 使用绝对路径而不是相对路径
    base_path = Path(__file__).parent.parent.parent / '.asset_space' / 'uploads'
    file_path = base_path / filename
    
    # 检查文件是否存在
    if not file_path.exists():
        abort(404)
    return send_from_directory(str(base_path), filename)

# 添加静态文件访问路由，只开放.work_space中以compose_video命名的mp4文件
@static_bp.route('/videos/<path:filename>')
@jwt_required()
def get_compose_video_files(filename):
    # 检查文件名是否以compose_video开头且以.mp4结尾
    # 获取实际的文件名（路径中的最后一部分）
    actual_filename = Path(filename).name
    if not (actual_filename.startswith('compose_video') and actual_filename.endswith('.mp4')):
        abort(404)
    
    # 使用绝对路径而不是相对路径
    base_path = Path(__file__).parent.parent.parent / '.work_space'
    file_path = base_path / filename
    
    # 检查文件是否存在
    if not file_path.exists():
        abort(404)
        
    return send_from_directory(str(base_path), filename)