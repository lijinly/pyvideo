
import os
import random
from pathlib import Path
from .asset_video_ import VideoIndexDB as video_indexer
from .asset_audio_ import AudioIndexDB as audio_indexer

from utils.logs import setup_logger
from .tools import  extract_main_description, load_json,save_json

class plan_2_design_wf:
 
    def __init__(self,config_plan_path:str):
        
        self.logger = setup_logger(name="plan_2_design_wf")
        self.video_db = video_indexer()
        self.audio_db = audio_indexer()
        # self.scene = scene
        
        # 构造策划案的工作空间
        root_dir = Path(config_plan_path).parent
        file_name = Path(config_plan_path).stem
        
        self.plan_space_dir = os.path.join(root_dir,file_name)
        os.makedirs( self.plan_space_dir,exist_ok=True) 
        
        # 加载策划的数据
        self.config_plan_path = config_plan_path
        self.config_plan_data = load_json(config_plan_path) 
                           
    def generate_design_files(self):
         
        if  not "references" in self.config_plan_data:
            self.config_plan_data["references"]=[]
        
     
        for index, design in enumerate( self.config_plan_data["designs"]):
          
            # update by lijinly at 2025-9-15 begin
            # 背景音乐
            # design["background_music_path"] = self._search_background_music(design["background_music"])
            # 音频
            # design["voice_path"] = design["voice"]
            # 背景音乐
            bgm_path = self._search_background_music(design["background_music"])            
            
            # clips
            clips_new,whole_duration = self._search_clips(design["clips"])
            # design["clips"] =  clips_new
            # update by lijinly at 2025-9-15 end
            
             # 构造design_config的集合            
            design_content = {  
                        "project":{ 
                            "duration":whole_duration,
                            "description":design["description"],
                            "width": 540,
                            "height": 960,
                            "frame_rate": 30,
                            "cover_path":"create:"+design["description"],
                            "background_music":design["background_music"],
                            "background_music_path": bgm_path,# design["background_music_path"],#bgm的地址                          
                            "voice_path":design["voice"],
                            "voice":design["voice"]
                        },
                        "video_clips": clips_new
                    }
            design_path = os.path.join(self.plan_space_dir,f"config_design_{index}.json")
            
            save_json(design_content,design_path)
            
            self.config_plan_data["references"].append(design_path)
       
        save_json(self.config_plan_data,self.config_plan_path)        
            
    def _search_clips(self,clips:list):
        
         # 处理视频片段    
        clips_assets=[]
        included_sub_clip_ids=[]
      
        current_whole_duration =0
        for clip in clips:
            
            clip_visual_method_name = clip["visual"].split(":")[0]  
           

            if clip_visual_method_name in ("avatar", "create", "load"):
                
                
                lst = [{"type":clip["type"]
                        ,"start_time":current_whole_duration
                        ,"duration":clip["duration"]
                        ,"description":clip["description"]
                        ,"visual":clip["visual"]
                        ,"voice":clip["voice"]
                        ,"visual_path":clip["visual"]
                        ,"voice_path":clip["voice"]
                        ,"structure":clip["structure"]}]
                
                current_whole_duration +=clip["duration"]               
                current_whole_duration = round(current_whole_duration,3)
               
                
            elif clip_visual_method_name == "search":
                
                query_text = extract_main_description(clip["description"])
                
                sub_clip_asset = self.video_db.search(  query = query_text  )
               
                sub_clip_asset = [item for item in sub_clip_asset if item["video_id"] not in included_sub_clip_ids ] 
                
                sub_actual_clips =[]
                should_duration = clip["duration"]
                actual_duration = 0
                for item in sub_clip_asset:
                    actual_duration +=item["clip_duration"]
                    sub_actual_clips.append(item)
                    if actual_duration >= should_duration:
                        break
                
                if actual_duration > should_duration :
                    balance_duration = round( actual_duration - should_duration,3)
                    sub_actual_clips[-1]["clip_duration"]   -=  balance_duration  
                    sub_actual_clips[-1]["clip_start"]   +=    round( random.uniform(0, balance_duration),3)
             
                lst = []
                
                sub_actual_clips = [item for item in sub_actual_clips if item["clip_duration"] >=1]
                
                cur_clip_duration = clip["duration"]
                sub_actual_clips_duration = sum([item["clip_duration"] for item in sub_actual_clips])
                
                # 修复除零错误：检查sub_actual_clips_duration是否为0
                if sub_actual_clips_duration == 0:
                    # 如果没有找到合适的片段，创建一个占位片段
                    lst = [{
                        "type": clip["type"],
                        "start_time": current_whole_duration,
                        "duration": cur_clip_duration,
                        "description": clip["description"],
                        "visual": clip["visual"],
                        "voice": clip["voice"],
                        "visual_path": "create:" + query_text,
                        "voice_path": clip["voice"],
                        "structure": clip["structure"]
                    }]
                    current_whole_duration += cur_clip_duration
                    current_whole_duration = round(current_whole_duration, 3)
                else:
                    sub_actual_clip_ratio = cur_clip_duration/ sub_actual_clips_duration
                    
                    for item in sub_actual_clips:
                        lst.append({"type":clip["type"]
                            ,"start_time":current_whole_duration
                            ,"duration":round( item["clip_duration"] *sub_actual_clip_ratio,3)
                            ,"description":clip["description"]
                            ,"visual":clip["visual"]
                            ,"voice":clip["voice"]
                            ,"visual_path":"load:"+item["video_path"]+"$"+str(round(item["clip_start"],3)) +"$"+str(round(item["clip_duration"],3))
                            ,"voice_path":clip["voice"]
                            ,"structure":clip["structure"]} )
                        
                        current_whole_duration +=round( item["clip_duration"] *sub_actual_clip_ratio,3) 
                        current_whole_duration = round(current_whole_duration,3)            
                     
                      
                    
                    included_sub_clip_ids.extend([item["video_id"] for item in sub_actual_clips])
             
            
            clips_assets.extend(lst)        
       
        
        return clips_assets  ,current_whole_duration
                        
    def _search_background_music(self,bgm_method_full:str):
          # 处理背景音乐 
        
        bgm_method_name = bgm_method_full.split(":")[0]
        bgm_method_parm = "".join(bgm_method_full.split(":")[1:] )
       
        bgm_method_new = bgm_method_full
        if bgm_method_name in ["search"]:
           
            bgm_metas = self.audio_db.search(bgm_method_parm)
            
            if bgm_metas:
                bgm = random.choice(bgm_metas)
                bgm_method_new = "load:"+bgm["audio_path"]
           
        elif bgm_method_name in ["avatar",  "load","create"]:
             bgm_method_new = bgm_method_name +":"+ bgm_method_parm          
        return bgm_method_new
       

# if __name__ == "__main__": 
   
    
    # config_plan_path = ".work_space/default/marketing/检索素材库生成视频_04.json"
    
    # marketing = marketing_selling_scene()
    # generator = plan_2_design_wf(config_plan_path=config_plan_path,scene= marketing)  
    
    # # 生成文案
    # generator.generate_copywrite()
    
    # # 生成基础设计
    # generator.generate_stroyboards()
    
    # generator.generate_designs_full()
    
    # from domains.work_flow_design2compose import IntegrateGenerator
    
    # plan_config = load_json(config_plan_path)
    
    # paths = plan_config["references"]

    # root_path= config_plan_path.split(".")[0]
    
    # for path in paths:
          
    #     design_config_path = path
       
    #     generator = IntegrateGenerator(root_path= root_path, design_config_path= design_config_path)
        
    #     # generator.generate_video_cover()
    #     generator.generate_video_voice()  
    #     generator.generate_video_bgm() 
            
    #     generator.generate_voice_clips()
    #     generator.generate_video_clips()    


    #     generator.adjust_video_duration()    
    #     generator.compose_video_assets()
        
    #     print(f"IntegrateGenerator 执行完毕：{path}")  
    
    # print("执行完毕")
   
    
        
        