import os
from pathlib import Path
import shutil

from tinydb import Query

from domains.tools import generate_file_hash
from utils.doc_db import doc_db_tiny
from .avatar_gfpgan_ import enhance_video
from .avatar_wav2lip_ import synic_video
import tempfile
from .config import Config

class avatar_video:
    def __init__(self,debug_mode=True):
        self.debug_mode = debug_mode
       
        pass        
        
    def generate_avatar_video(self, input_audio_path,avatar_id, output_video_path):
        '''
        输入视频、音频和数字人Id，生成数字人视频
        '''
     
        output_suffix = Path(output_video_path).suffix
        output_stem = Path(output_video_path).stem
        output_dir = Path(output_video_path).parent
  
        with tempfile.NamedTemporaryFile(suffix=output_suffix,prefix=output_stem, delete=True) as tmp_video:
            
            if self.debug_mode:
                model_path:str='.asset_space/avatars/default/Wav2Lip-SD-GAN.pth'
                video_path:str='.asset_space/avatars/default/jiaojiao01.mp4'
            else:
                model_path ,video_path = self._load_avatar_model(avatar_id)
       
            synic_video(face_path= video_path, 
                        audio_path= input_audio_path,
                        out_file= tmp_video.name,
                        avatar_path= model_path,
                        resize_factor=2)
            
            enhance_video(input_video_path= tmp_video.name,
                            output_video_path= output_video_path) 
            
            if self.debug_mode:
                shutil.copy2(tmp_video.name, output_dir)

    def fine_tuning_avatar(self, input_video_path:str,user_id:str ='default' )->dict:
        '''
        基于基础模型+输入视频，为某人定制数字人模型
        返回数字人的模型地址
        '''
        model_dir = os.path.join(Config.project_root,".asset_space","avatars",user_id)
        os.makedirs(model_dir, exist_ok=True)
        avatar_id = generate_file_hash(input_video_path)
        video_path = os.path.join(model_dir, f"{avatar_id}.mp4")
        shutil.copyfile(input_video_path, video_path)
       
        model_name = f"{avatar_id}.pth"
        cover_name = f"{avatar_id}.jpg"
        video_name = f"{avatar_id}.mp4"
        
        if self.debug_mode:
             model_name = f"jiaojiao01.pth"
        else:
            # 实际的模型训练逻辑
            # 待实现
            pass
           
        # ToDo：
        # Step 1: 训练模型并存储
        # Step 2：保存元数据金数据库
        # Step 3：返回元数据
        result =  {"avatar_id":avatar_id,
                    "user_id":user_id,
                    "model_path":os.path.join(Config.project_root,".asset_space","avatars",user_id,model_name),
                    "cover_path":os.path.join(Config.project_root,".asset_space","avatars",user_id,cover_name),
                    "video_path":os.path.join(Config.project_root,".asset_space","avatars",user_id,video_name)
                    }
        
        from utils.doc_db import doc_db_tiny
        
        with doc_db_tiny() as db:
            db.insert(result, doc_db_tiny.tables.avatar_metas)
        
        return result
     
    def load_avatar_metas(self,avatar_id:str='jiaojiao01',user_id:str='default'):
        '''
        加载数字人模型元数据
        '''
        # 模拟数据
        # 实际应该从数据库中加载
        with doc_db_tiny() as db:
            meta = Query()
            if avatar_id is None:
                results = db.query(meta.user_id == user_id,table_name=doc_db_tiny.tables.avatar_metas)
            else:
                results = db.query((meta.id == avatar_id) & (meta.user_id == user_id),table_name=doc_db_tiny.tables.avatar_metas)
        return results     
    
    
  
        
    def _load_avatar_model(self,avatar_id:str='jiaojiao01',user_id:str="default"):
        with doc_db_tiny() as db:
            meta = Query()
           
            results = db.search((meta.id == avatar_id) & (meta.user_id == user_id))
            
            if len(results) > 0:
                avatar_model_path = results[0]['avatar_model_path']
                avatar_video_path = results[0]['avatar_video_path']
                avatar_cover_path = results[0]['avatar_cover_path']
            else:
                avatar_model_path = None
                avatar_video_path = None
                avatar_cover_path = None    
        return avatar_model_path,avatar_video_path,avatar_cover_path
    
        
    def _generate_avatar_cover(self, input_video_path ,avatar_cover_path):
         # 获取数字人封面
        from moviepy import VideoFileClip
        import imageio

        # 视频文件路径
        video_path = input_video_path

        # 创建视频文件剪辑对象
        clip = VideoFileClip(video_path)

        # 获取第一帧（位于时间0秒处）
        frame = clip.get_frame(0) # get_frame(t) 可以获取第 t 秒的帧

        # 保存第一帧为图像文件
        output_path = avatar_cover_path
        imageio.imwrite(output_path, frame)
        print(f"First frame saved to {output_path}")

        # 释放资源（可选，但良好的实践）
        clip.close() 
        