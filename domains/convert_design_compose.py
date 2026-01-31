import json
import copy
import os
from pathlib import Path
from .tools import load_json
       


class FormatConvertor:
    def __init__(self,design_file_path:str,compose_config_path:str,workspace_path:str):      
        self.compose_config_path = compose_config_path
        self.design_config = load_json(design_file_path)
        self.compose_config = {}
        self.workspace_path = workspace_path
        
   
       
    def convert(self)->object:
        
        # 1、convert project section
        
        self.compose_config["project"] = copy.deepcopy(self.design_config["project"])
          
        # 2、convert clips section
       
        video_track =[]
        voice_track =[]
        text_track =[]
        for item in self.design_config["video_clips"]:
           
            visual_path_parms = item["visual_path"].split(":")[1]
            video_track.append({"type": "clip",
                                # "source_path": os.path.join(self.workspace_path, item["visual_path"]),
                                "source_path":visual_path_parms,
                                "start_time": item["start_time"],
                                "duration": item["duration"],
                                "description": item["visual"]
                                }) 
            
            # 
            # ToDo:
            # 
            # 
            clip_voice_method = item["voice"].split(":")[0]
            clip_voice_parms = item["voice"].split(":")[1]
            
            if clip_voice_method == "skip":
                continue
            
            voice_path_parms = item["voice_path"].split(":")[1]
            
            voice_track.append({
                                "type": "voice",
                                #"source_path":  os.path.join(self.workspace_path,item["voice_path"]  ),
                                "source_path":voice_path_parms,
                                "start_time": item["start_time"],
                                "duration": item["duration"],
                                "description": item["voice"],
                                "volume": 1 }) 
        
            srt_path =os.path.join( Path(voice_path_parms).parent,Path(voice_path_parms).stem+".srt")
          
            text_track.append( {
                                "type":"subtitle",
                                "content":"",
                                "font": "黑体",
                                "font_size": 80,
                                "color": "#FFFF00",
                                "position": {"x": 0.5, "y": 0.9 },
                                "start_time": item["start_time"],
                                "duration": item["duration"],
                                "source_path":  srt_path,
                                })
        
      
        # 添加背景音乐
        background_music_path_parms = self.compose_config["project"]["background_music_path"].split(":")[1]
        voice_track.append({
                                "type": "bgm",
                                "source_path": background_music_path_parms,
                                "start_time":0,
                                "duration": self.compose_config["project"]["duration"],
                                "description": "",
                                "volume": 0.5 }) 
        # 
        # 添加全局语音和字幕
        #
        voice_project_parms = self.compose_config["project"]["voice_path"].split(":")[1]
       
        srt_project_path =os.path.join( Path(voice_project_parms).parent,Path(voice_project_parms).stem+".srt")
        text_track.append( {
                                "type":"subtitle",
                                "content":"",
                                "font": "黑体",
                                "font_size": 80,
                                "color": "#FFFF00",
                                "position": {"x": 0.5, "y": 0.9 },
                                "start_time": 0,
                                "duration": self.compose_config["project"]["duration"],
                                "source_path":  srt_project_path #voice_project_parms.split(".")[0]+".srt" ,
                                })     
        
        voice_track.append({
                                "type": "voice",
                                "source_path": voice_project_parms,
                                "start_time":0,
                                "duration": self.compose_config["project"]["duration"],
                                "description": self.compose_config["project"]["description"],
                                "volume": 1 }) 
        
        # 删除 project 中冗余的 bgm信息
        # my_dict.pop("b")
        if "background_music_path" in self.compose_config["project"]:
            del self.compose_config["project"]["background_music_path"]
            del self.compose_config["project"]["background_music"]
            
        if "voice_path" in self.compose_config["project"]:
            del self.compose_config["project"]["voice_path"]
            del self.compose_config["project"]["voice"]
        
        # 处理视频封面   
        cover_method_full  =   self.compose_config["project"]["cover_path"]        
        self.compose_config["project"]["cover_path"] =  "".join(cover_method_full.split(":")[1:])
        
        
        
        # 添加视频、音频、字幕
        self.compose_config["timeline"]={  "tracks":[]}
        self.compose_config["timeline"]["tracks"].append({"type":"video", "items":video_track})
        self.compose_config["timeline"]["tracks"].append({"type":"text", "items":text_track})
        self.compose_config["timeline"]["tracks"].append({"type":"audio", "items":voice_track})
        
        # 添加导出结点
        self.compose_config["export"]= {
                                "format": "H.264",
                                "preset": "Match Source - High Bitrate"
                                }
        # 保存创建的配置文件
        with open( self.compose_config_path, 'w',encoding="utf-8") as f:
            json.dump( self.compose_config, f,ensure_ascii=False, indent=2)    
        
        # 返回创建后的配置文件的对象
        return self.compose_config
    
     
                                
if __name__ == "__main__":
    
    design_config_path = "content_design\检索素材库生成视频\config_design_1 copy.json"   
    compose_config_path = "content_design\检索素材库生成视频\config_design_1_copy_compose.json"  
    workspace_path = "render_videos/品牌部比总经理还操心"       
    convertor =  FormatConvertor(design_config_path,compose_config_path,workspace_path) 
    jsonobj = convertor.convert()
  
    print("FormatConvertor.convert 执行完毕")