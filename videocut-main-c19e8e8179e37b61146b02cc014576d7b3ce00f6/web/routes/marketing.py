import os
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from domains.scene_marking_selling import marketing_selling_scene
from domains.work_flow_plan2design import plan_2_design_wf
# from domains.work_flow_design2compose import design_2_compose_wf
from datetime import datetime
from web.models import ErrorCode, make_response
from utils.logs import setup_logger
from domains.tools import load_json, save_json
from pathlib import Path

# 创建蓝图
marketing_bp = Blueprint('marketing', __name__)

# 配置日志记录
logger = setup_logger(name=__name__)

@marketing_bp.route('/generate_videos', methods=['POST'])
@jwt_required()
def generate_videos():
    """
    根据审核通过的文案创作视频
    """
    # 获取当前用户ID
    user_identity = get_jwt_identity()
    user_id = user_identity if user_identity else "0"
    
    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, '请求数据不能为空')), 400

    plan_name = data['plan_name']
    # 创建营销场景实例
    marking_scene = marketing_selling_scene(plan_name, user_id)
    # marking_scene.generate_copywrites()

    

    # 加载plan_data以确保在后续方法中可以使用
    plan_config=marking_scene.load_plan()
    if plan_config is None:
        return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, '未找到计划文件')), 404
    config_plan_path = marking_scene.get_plan_path()
    
    # 如果请求中包含copy_writes，则保存到plan_config中
    if 'copy_writes' in data and isinstance(data['copy_writes'], list):
        plan_config['copy_writes'] = data['copy_writes']
        save_json(plan_config, config_plan_path)
        marking_scene.plan_data = plan_config
    
    # #创建分镜设计
    marking_scene.generate_stroyboards()

    from domains.work_flow_design2compose import design_2_compose_wf

    # 创建文案生成器
    generator = plan_2_design_wf(config_plan_path=config_plan_path)       
    # 生成完整设计
    generator.generate_design_files()
    
    # 重新加载plan_config以获取更新后的references
    plan_config = marking_scene.load_plan()
    
    # 构造策划方案路径    
    design_paths = plan_config.get("references", [])
    
    for design_path in design_paths:        
        
        composer = design_2_compose_wf(config_design_path=design_path)
       
        # update lijinly at 2025-09-15 Begin
        # 生成视频各组成部分
        composer.generate_video()
        # composer._generate_video_voice()  
        # composer._generate_video_bgm() 
        # composer._generate_video_avatar()
        # composer._generate_voice_clips()
        # composer._generate_video_clips()    
        # composer._adjust_video_duration()    
        # composer._compose_video_assets()    
        # update lijinly at 2025-09-15 end   
    
    # 重构返回的文件路径，使其可以用于访问视频文件
    video_paths = []
    for design_path in design_paths:
        # 提取路径中的各个部分
        path_obj = Path(design_path)
        
        # update lijinly at 2025-09-15 Begin
        # 获取倒数第二级和最后一级目录名
        # parent_dir = path_obj.parent.name  # 倒数第二级目录名，如"20250906092310739"
        # grandparent_dir = path_obj.parent.parent.name  # 倒数第三级目录名，如"marketing"
        # great_grandparent_dir = path_obj.parent.parent.parent.name  # 倒数第四级目录名，如"2"
        
        # 构建访问路径
        access_path = os.path.join('static','videos', path_obj.parent, path_obj.stem,"compose_video.mp4")
        # access_path = f"/static/videos/{great_grandparent_dir}/{grandparent_dir}/{parent_dir}/config_design_0/compose_video.mp4"
        # update lijinly at 2025-09-15 End
        video_paths.append(access_path)
    
    return jsonify(make_response(ErrorCode.SUCCESS, video_paths)), 200

@marketing_bp.route('/generate_copywrites', methods=['POST'])
@jwt_required()
def generate_copywrites():
    """
    生成营销场景文案
    """
    # 获取当前用户ID
    user_identity = get_jwt_identity()
    user_id = user_identity if user_identity else "0"
    
    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, '请求数据不能为空')), 400
    
    
    
    # 构造策划方案路径
    plan_name = data['plan_name']        
    
    # 创建营销场景实例
    marking_scene = marketing_selling_scene(plan_name, user_id)
    marking_scene.generate_copywrites()

    # 加载plan_data以确保在后续方法中可以使用
    plan_config=marking_scene.load_plan()
    if plan_config is None:
        return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, '未找到计划文件')), 404
    
    copywrites = plan_config["copy_writes"]
    return jsonify(make_response(ErrorCode.SUCCESS, {
        'copy_writes': copywrites
    })), 200



@marketing_bp.route('/save_plan', methods=['POST'])
@jwt_required()
def save_scene_plan():
    """
    保存场景策划方案
    """
    # 获取当前用户ID
    user_identity = get_jwt_identity()
    user_id = user_identity if user_identity else "default"
    
    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, '请求数据不能为空')), 400            
    
    if 'plan' not in data or not isinstance(data['plan'], dict):
        return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, '缺少必需的plan字段或格式不正确')), 400
    
    # 验证plan字段中的必需子字段
    plan = data['plan']
    required_fields = [
        'core_objective', 'user_portrait', 'target_market', 
        'target_channel', 'product_name', 'product_selling_points',
        'brand_name', 'brand_story', 'market_campaign'
    ]
    
    for field in required_fields:
        if field not in plan:
            return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, f'缺少必需的plan.{field}字段')), 400
          
   
    if not isinstance(plan['product_selling_points'], list):
        return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, 'plan.product_selling_points必须为列表格式')), 400
        
   
    if 'batch_size' in plan and not isinstance(plan['batch_size'], int):
        return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, 'plan.batch_size必须为整数')), 400
    
    # 在plan_name后面添加时间戳
    plan_name = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]    
    # 创建营销场景实例
    scene = marketing_selling_scene(plan_name, user_id) 
    
    # 保存策划方案
    plan_data = data
    plan_path = scene.save_plan(plan_data)
    
    return jsonify(make_response(ErrorCode.SUCCESS, {
        'plan_path': plan_path,
        'plan_name': plan_name
    })), 200

@marketing_bp.route('/load_plan', methods=['POST'])
@jwt_required()
def load_scene_plan():
    """
    加载场景策划方案
    """
    # 获取当前用户ID
    user_identity = get_jwt_identity()
    user_id = user_identity if user_identity else "default"
    
    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, '请求数据不能为空')), 400
        
    # # 检查必需字段
    # if 'plan_name' not in data or not data['plan_name'].strip():
    #     return jsonify(make_response(ErrorCode.VALIDATION_ERROR, None, '缺少必需的plan_name字段')), 400
    
    plan_name = data['plan_name']
    marking_scene = marketing_selling_scene(plan_name, user_id)
    # marking_scene.generate_copywrites()

    config_plan_path= marking_scene.get_plan_path()    
    plan_config = load_json(config_plan_path)
    
    return jsonify(make_response(ErrorCode.SUCCESS, plan_config)), 200