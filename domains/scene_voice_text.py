

import os
from pathlib import Path
from create_voice_sambert import VoiceGenerator  
from tools import load_json,save_json,parse_json,chat
from scene_abs import abs_scene


class voice_text_scene(abs_scene):
    def __init__(self,  user_id :str="default",voice_text_path:str=""):
       
        super().__init__(user_id)  
        # 
        # 1、
        # 构造工作流的工作空间
        # 提取将要创建的配置文件的名字（带扩展名
        voice_file_name = Path(voice_text_path).name 
        # 
        # 2、
        # 构造输出路径
        self.voice_output_path = os.path.join(self.workspace_path, voice_file_name+".wav")
        self.srt_output_path = os.path.join(self.workspace_path,voice_file_name+".srt")
        self.shots_output_path = os.path.join(self.workspace_path,voice_file_name+"_shots.json")
        self.design_output_path = os.path.join(self.workspace_path,voice_file_name+"_design.json")
        
    def return_scene_type(self):
        return "voicetext"   
    # 
    # 1、
    # 需要能把 台词合成语音，以便获取音频文件、字幕文件；
    # 就得到了视频的场景划分、每个场景的台词、以及视频的总长度
    # 
    def _generate_voice_srt(self,voice_text_path:str,voice_file_path:str,srt_file_path:str)->None:
        voice_text = self.jsonTool.load_json(voice_text_path)
        generator = VoiceGenerator()
        generator.generate_voice(voice_text=voice_text,voice_file_path=voice_file_path,srt_file_path=srt_file_path)
         
    # 
    # 2、
    # 根据视频的分镜的台词、长度，策划分镜
    # 
    # 
    def _generate_shots(self, srt_file_path:str,shots_file_path:str)->object:
    
      
        voice_srt_data = load_json(srt_file_path)       
        
        voice_texts = [seg[1] for seg in voice_srt_data]
        prompt = f"""
                **我要制作一个知识类口播的短视频，我有了一组台词，请参考台词帮我制作分镜组合：
                1.我的台词集合是：{str(voice_texts)}
                2.请参考台词帮我为每行台词设计一个分镜
                3.分镜设计要包含这些内容：[主体描述]、[光影色调]、[镜头语言]、[动态效果]、[环境背景]、[风格]、[参数] 
                4.请严格按如下结构输出：[{{"台词":"第一句台词",
                                        "主体描述"："人物佩戴珍珠发箍，穿黑色带米色蕾丝装饰衣物，执行撕下脸部面膜的动作\n同前人物撕面膜后，颈部残留面膜，自然展示颈部状态",
                                        "光影色调"："暖光，光线柔和，主色调为暖黄色搭配黑、米色",
                                        "镜头语言"："中景，固定镜头，采用居中构图",
                                        "动态效果"："人物手部完成撕面膜动作，无复杂后期特效",
                                        "环境背景"："室内场景，背景布置有台灯、插着粉色花朵的花瓶"
                                        "风格"："美妆教程风格，呈现日常温馨感"
                                        "技术参数"："分辨率540x960，帧率30，编码格式H.264"}}]
                """
        descs= chat(prompt)
        print(descs)
        
        descs = parse_json(descs)
        save_json(descs,shots_file_path)
        
        return descs
    
    # 
    # 3、
    # 根据分镜结构，合成最终的策划文件
    # 
    # 
    def _generate_design(self,srt_file_path:str, shots_file_path:str,design_file_path:str)->None:        

        descs = load_json(shots_file_path)
        shots_data = load_json(srt_file_path)
        # 合成 video_clips节点
        video_clips = []
        index =0 
        whole_duration = 0
        for seg in  shots_data:              
        
            index += 1  
            whole_duration += seg[0][1]
            desc = [desc for desc in descs if desc["台词"] == seg[1]][0]
            
            visual_descs =[]            
            for k,v in desc.items():
                if k in ["主体描述","光影色调","镜头语言","动态效果","环境背景","风格","技术参数"]:
                    visual_descs.append(f"**{k}**：{v}") 
                        
            visual_desc = "\n".join( visual_descs )  
            
            suffix = "_"+seg[1][:2] if len(seg[1])>2 else ""
            
            clip =  {
                "type": "clip",
                "start_time":  seg[0][0],
                "duration": seg[0][1],
                "visual_description":visual_desc,
                "visual_path": f"clip_{index}{suffix}.mp4",
                "voice_caption": seg[1] ,
                "create_method": "create"
                }
            video_clips.append(clip)
        
        # 合成project节点
        project = {
            "name": "glow_beauty_campaign_us.mp4",
            "description": "",
            "width": 540,
            "height": 960,
            "frame_rate": 30,
            "duration": 60,
            "background_music_path": "SoutheastAsia_TrendyBGM_Ramadan.mp3"
        }
     
    
            
        project["duration"] = whole_duration
        project["voice_path"] = self.voice_output_path 
      
        
        # 合成整个配置文件
        design_config = {"project":project,
                    "video_clips":video_clips   }
        
        
        save_json(objdata= design_config,output_path=design_file_path)  
        
    
    def generate(self):
        
        self._generate_voice_srt(voice_text_path=self.voice_text_path,voice_file_path=self.v)
        self._generate_shots(srt_file_path=self.srt_output_path,shots_file_path=self.shots_output_path)
        self._generate_design(shots_file_path=self.shots_output_path,design_file_path=self.design_output_path)
        
        print(f"已创建策划文件：{self.design_output_path}") 
    
     
     
     


if __name__ == "__main__":
    
    root_path = "render_videos"
    voice_text_path = "content_design/品牌部比总经理还操心.txt"
    
    voice2Design = voice_text_scene(root_path=root_path,voice_text_path= voice_text_path)
    voice2Design.generate()
     
    
    