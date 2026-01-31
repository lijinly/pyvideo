import json
import os
from pathlib import Path
from typing import Dict


class ExtractConvertor:
    def __init__(self,source_path:str,target_path:str):
        self.source_path = source_path
        self.target_path = target_path
        self.source_file_name =  Path(source_path).stem #  os.path.basename(source_path).split(".")[0]
        pass
    
    def _load_source(self) -> Dict:
        """加载JSON配置文件"""
        with open(self.source_path, 'r', encoding='utf-8') as f:
            return json.load(f)
        
    def _save_target(self,data)->None:
          # 保存创建的配置文件
        with open( self.target_path, 'w',encoding="utf-8") as f:
            json.dump( data, f,ensure_ascii=False, indent=2)   
        pass    
    def convert(self):
        
        """
        video_clips": [
        {
        "type": "clip",
        "start_time": 0,
        "duration": 5,
        "visual_description": "炎热街头，一位油皮女生用纸巾擦拭额头汗水后露出斑驳底妆，表情略显焦虑。",
        "voice_caption": "Kak！底妆斑驳了？Ya Allah，这可不行！",
        "visual_path": "Scene1_OilySkinProblem.mp4",
        "voice_path": "VoiceClip1_SpotlightProblem.mp3",
        "comments": "开篇制造用户共鸣：油皮和户外底妆挑战是东南亚用户的普遍痛点。"
        }]
        """
        """
         [{
            "shot_id": 1,
            "start_time": 0.0,
            "end_time": 2.5,
            "主体描述": "女性手持面膜进行敷面膜动作，表情自然",
            "光影色调": "暖光，光线柔和，主色调暖黄色",
            "镜头语言": "中景，固定镜头，居中构图",
            "动态效果": "手部敷面膜动作，无后期特效",
            "环境背景": "室内场景，布置有花瓶（插有粉色花朵）、台灯",
            "风格": "日常美妆风格",
            "技术参数": "分辨率1080p，帧率30fps，编码H.264",
            "长度": 2.5,
            "台词": "20岁用叫预防"
        }]
        
        """
        extract_data = self._load_source()
        
        
        
        # 转换clips
        video_clips = []
        index = 0
        for shot in extract_data["shots"]:
            
            index +=1
            # 处理台词
            voice_caption = shot["台词"]
            # 处理持续时间
            duration =max(0, shot["end_time"] - shot["start_time"])
            
            # 处理视觉描述
            visual_descs =[]            
            for k,v in shot.items():
                if k in ["主体描述","光影色调","镜头语言","动态效果","环境背景","风格","技术参数"]:
                    visual_descs.append(f"**{k}**：{v}") 
                     
            visual_desc = "\n".join( visual_descs )  
            
            suffix = "_"+shot["主体描述"][:2] if len(shot["主体描述"])>2 else ""
            
            
            video_clip = {                
                    "type": "clip",
                    "start_time": shot["start_time"],
                    "duration": duration,
                    "visual_description": visual_desc,
                    "voice_caption": shot["台词"],
                    "visual_path": f"video_clip_{index}{suffix}.mp4",
                    "voice_path": f"vioce_clip_{index}{suffix}.mp3" ,
                    "create_method":"create" # "create|search 默认create"               
            } 
            video_clips.append(video_clip)
            
        
        
        # 转换project
        """
         "project": {
            "name": "GlowBeauty_Indonesia_Promo.mp4",
            "description": "以痛点展示开场，通过多场景对比突出产品优势，最终号召行动的60秒带货短视频。",
            "width": 540,
            "height": 960,
            "frame_rate": 30,
            "duration": 60,
            "background_music_path": "TikTokHot_BGM_TropicalRain.mp3"
        },
        """
       
        project = { 
            "name": self.source_file_name,
            "description": "",
            "width": 540,
            "height": 960,
            "frame_rate": 30,
            "duration": 60,
            "background_music_path": ""}
        
        sourceProject = extract_data["project"]
        
        project = {**project,**sourceProject}
        
        # 合成目标格式
        design_data ={"project":project,
                      "video_clips":video_clips}
        
        # 
        self._save_target(design_data)
        # 
        print(f"extract->design convert finished:{self.source_file_name}")
        
if __name__ == "__main__":
    
    source = "extract_videos/douyin_7513772615874399526_analysis_merged.json"
    target = "content_design/douyin_7513772615874399526_extract.json"
    
    convertor = ExtractConvertor(source_path=source,target_path=target)
    convertor.convert()
         
                
                 