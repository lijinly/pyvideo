

# 创建蓝图
import os
from pathlib import Path
import tempfile
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from domains.tools import generate_file_hash
from utils.logs import setup_logger
from domains.avatar_video import avatar_video


avatar_bp = Blueprint('avatar', __name__)

# 配置日志记录
logger = setup_logger(name=__name__)

       
@avatar_bp.route('/generate_avatar_model', methods=['POST'])
@jwt_required()
def generate_avatar_model( input_video_path:str )->dict:
    '''
    基于基础模型+输入视频，为某人定制数字人模型
    从Request中获取video_path
    '''
     # 检查请求中是否包含文件部分
    if 'video' not in request.files:
        return jsonify({'error': 'No video file part in the request'}), 400
    
    file = request.files['video']
    
    # 如果用户没有选择文件，浏览器可能提交一个空字段
    if file.filename == '':
        return jsonify({'error': 'No video file selected'}), 400
    
    # 验证文件类型
    if not file or not allowed_file(file.filename):
         return jsonify({'error': 'Invalid file type. Allowed types: ' + ', '.join(ALLOWED_EXTENSIONS)}), 400
     
        # 安全地获取原始文件名
        # filename = secure_filename(file.filename)
        
        # 创建临时文件
    with tempfile.NamedTemporaryFile(  suffix= Path( file.filename).suffix,   delete=True   ) as temp_video:
        file.save(temp_video.name)
        
        userid = get_jwt_identity()      
        avatar_video().fine_tuning_avatar(input_video_path= temp_video.name,user_id=userid )


    return jsonify({
        'message': 'Video successfully uploaded and saved as temporary file',
        
        'original_filename': file.filename
    }), 200
            
    
   
@avatar_bp.route('/load_avatar_metas', methods=['POST'])
@jwt_required()    
def load_avatar_metas(avatar_id):
    '''
    加载数字人模型元数据
    '''
    userid = get_jwt_identity()
    return  avatar_video().load_avatar_metas(avatar_id= avatar_id,user_id=userid)

# 配置允许的视频文件扩展名
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'flv'}

def allowed_file(filename):
    """检查文件扩展名是否合法"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS