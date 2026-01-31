
import os 
from datetime import datetime
from pathlib import Path

from domains.avatar_video import avatar_video
from domains.create_video_qwen import VideoGenerator as VideoGenerator
from domains.create_image_volce import ImageGenerator as ImageGenerator
from domains.convert_design_compose import FormatConvertor 
from domains.compose_pr_movpy import VideoComposer as  VideoComposer
from domains.create_bgm_qwen import BGMGenerator as BgmGenerator
from domains.create_voice_sambert import VoiceGenerator as VoiceGenerator

from domains.tools import concatenate_and_save_videos,  load_json,save_json, save_last_frame,get_audio_duration,get_video_duration_fps
 
class design_2_compose_wf:
    """
    基于设计文件，基于谓词和参数，构造素材，生成compose文件指导视频合成
    """     
    def __init__(self,config_design_path: str):
      
        # 构造工作空间   
        root_dir = Path(config_design_path).parent
        file_name = Path(config_design_path).stem
        
        self.work_space_path = os.path.join(root_dir,file_name)
        os.makedirs(self.work_space_path,exist_ok=True) 
     
       
            
        # 加载JSON文件
        self.design_config_path = config_design_path
        self.design_config_data = load_json(config_design_path) 

     
        # 构造合成视频的配置文件路径及合成视频的路径
        self.compose_config_path =os.path.join(self.work_space_path, "compose_config.json")
        self.compose_video_path = os.path.join(self.work_space_path, "compose_video.mp4")
       
       
       
    def _generate_video_voice(self)->None:
        design_config_data = self.design_config_data
        design_config_path = self.design_config_path
        work_space_path = self.work_space_path
        
        voiceGenerator = VoiceGenerator()   
        
        # 处理全局音频
         
        whole_voice_method =  design_config_data["project"]["voice_path"].split(":")[0]
        whole_voice_parm ="".join( design_config_data["project"]["voice_path"].split(":")[1:])
        
        if whole_voice_method == "create":
            whole_voice_path = os.path.join(work_space_path, "whole_voice.mp3") 
            # 合成音频文件并保存到创作区
          
            voiceGenerator.generate_voice(voice_text= whole_voice_parm,voice_file_path= whole_voice_path)
            
            # 
            # ToDo：
            # 根据生成的全局音频的长度，伸缩视频的总长度，并按比例伸缩各片段的长度
            # 
            
            design_config_data["project"]["voice_path"] = "load:"+whole_voice_path
        
        elif whole_voice_method == "load":
             design_config_data["project"]["voice_path"] = "load:"+whole_voice_parm
        
        # 及时保存
        save_json(design_config_data,design_config_path)
    
    def _generate_video_avatar(self)->None:
        """
        遍历全部clips,若存在数字人需求，则基于完整音频，创建数字人，
        并将数字人作为素材付给clip
        """
        design_config_data = self.design_config_data
          
       
        #  创建数字人素材 
        
        
      
        avatar_clips =[clip for clip in design_config_data['video_clips'] if clip["visual_path"].split(":")[0] == 'avatar']
          
        
        if not avatar_clips :
            return 
       
        avatar_clip = avatar_clips[0]
        
        avatar_params = avatar_clip["visual_path"].split(":")       
        avatar_id = avatar_params[1]
       
        avatar_visual_path =os.path.join( self.work_space_path ,"avatar_visual.mp4")
        whole_voice_parm ="".join( design_config_data["project"]["voice_path"].split(":")[1:])
      
        avatarGenerator = avatar_video()
        avatarGenerator.generate_avatar_video(avatar_id= avatar_id, output_video_path=avatar_visual_path, input_video_path=whole_voice_parm)
       
            
        
        for avatar_clip in avatar_clips:  
            avatar_clip[  "visual_path"] =f"load:{avatar_visual_path}"
                    
        pass

    def _generate_voice_clips(self)->None:
        
        
        design_config_data = self.design_config_data
        design_config_path = self.design_config_path
        work_space_path = self.work_space_path
        
        voiceGenerator = VoiceGenerator()  
           
        # 处理clip中的音频
        
        for index, clip in enumerate( design_config_data['video_clips']):            
           
            part_voice_method = clip["voice_path"].split(":")[0]
            part_voice_parm = clip["voice_path"].split(":")[1]
            
     
            if part_voice_method == "create": 
       
                part_voice_path = os.path.join(work_space_path, f"voice_clip_{index}.mp3") 
                duration = clip["duration"]
                
                # 合成音频文件并保存到创作区
                voiceGenerator.generate_voice(part_voice_parm,part_voice_path,duration=duration)
                clip["voice_path"] = "load:"+part_voice_path
            elif  part_voice_method == "load":
                 clip["voice_path"]  = "load:"+part_voice_parm
            else:
                pass
            # 及时保存
            save_json(design_config_data,design_config_path)
            
    def _adjust_video_duration(self)->None:
        
        original_video_whole_duration = self.design_config_data["project"]["duration"]
        whole_audio_path = self.design_config_data["project"]["voice_path"]  
        whole_audio_path = whole_audio_path.split(":")[1]
        actual_audio_whole_duration = get_audio_duration(whole_audio_path)
        self.design_config_data["project"]["duration"] = actual_audio_whole_duration
      
        ratio = round(actual_audio_whole_duration/original_video_whole_duration,2)
        
        last_end_time = 0
        extra = 0
        for clip in self.design_config_data["video_clips"]:
            clip["start_time"] = last_end_time
            full_duration = clip["duration"] * ratio + extra
            clip["duration"] =  ((full_duration * 1000) // 1 / 1000) 
            extra = full_duration -  clip["duration"]
            last_end_time += clip["duration"]
       
        extra = actual_audio_whole_duration -  last_end_time 
        if extra >0:
            last_clip_duration = round( self.design_config_data["video_clips"][-1]["duration"] + extra,2)
            self.design_config_data["video_clips"][-1]["duration"] = last_clip_duration
        
        save_json(self.design_config_data,self.design_config_path) 
               
    def _generate_video_cover(self)->None:
         #生成视频首帧
     
        if not "cover_path" in self.design_config_data["project"]:
            return
        if not self.design_config_data["project"]["cover_path"].strip():
            return
          
     
        cover_method =  self.design_config_data["project"]["cover_path"].split(":")[0]
        if cover_method != "create":
             # load、skip 都不必处理
            return 
        
        imageGenerator = ImageGenerator()     
        video_whole_description = self.design_config_data["project"]["description"]
        prompt = f"""
        参考以下是视频的文案信息，帮我生成短视频的封面图，文案信息如下：{video_whole_description}
        """
        video_cover_path = self.compose_video_path.split(".")[0]+"_cover.jpg"
        imageGenerator.generate_image(prompt,video_cover_path)
        self.design_config_data["project"]["cover_path"] = "load:"+ video_cover_path
    
                    
    def _generate_video_clips(self)->None:        
        
     
        design_config_data = self.design_config_data
        design_config_path = self.design_config_path
        work_space_path = self.work_space_path
        
        # 遍历visual_*，生成图片和视频
        imageGenerator = ImageGenerator()
        videoGenerator =  VideoGenerator()
        
              
        for clip_index, clip in enumerate( design_config_data['video_clips']):
                     
            clip_visual_mehtod = clip["visual_path"].split(":")[0]           
            
            if  clip_visual_mehtod != "create":
                """
                当前中有可能是 create、load，Load 无需处理
                """
                continue
            
          
                
            clip_aready_parts=[] 
            clip_part_durations = []
            clip_left_duration = clip["duration"]    
            
            while(clip_left_duration > 0):               
                clip_part_curation = min (5,clip_left_duration)               
                clip_part_durations.append(clip_part_curation)
                clip_left_duration = min (0,clip_left_duration-5)
            
            for part_index ,clip_part_curation in enumerate(clip_part_durations):
                
                last_part_frame = None
                if part_index ==0:
                    last_part_frame = os.path.join(work_space_path,f"visual_clip_{clip_index}_image_{part_index}.jpeg")
                    imageGenerator.generate_image(clip["description"],last_part_frame)
                else:
                    last_part_frame = clip_aready_parts[-1]
                    save_last_frame(part_video_path,last_part_frame)
                
                              
                part_video_path = os.path.join(work_space_path, f"visual_clip_{clip_index}_video_{part_index}.mp4")
                videoGenerator.generate_video(prompt= clip["description"],
                                            image_path= last_part_frame,
                                            video_path = part_video_path,
                                            duration= clip_part_curation)
                clip_aready_parts.append(part_video_path)
                
                    
            part_video_path = os.path.join(work_space_path, f"visual_clip_{clip_index}_video.mp4")  
            concatenate_and_save_videos(clip_aready_parts,clip["duration"],part_video_path)   
            
            clip["visual_path"] = "load:"+part_video_path
            
            save_json(design_config_data,design_config_path)
    
         
            
                
    
    def _generate_video_bgm(self)->None: 
        
        design_config_data = self.design_config_data
        design_config_path = self.design_config_path
        work_space_path = self.work_space_path  
        
        if not "background_music_path" in self.design_config_data["project"]:
            return
        if not self.design_config_data["project"]["background_music_path"].strip():
            return
        
        back_ground_music_path = design_config_data["project"]["background_music_path"]
        bgm_method = back_ground_music_path.split(":")[0]
        bgm_parms = back_ground_music_path.split(":")[1]
        
        if not bgm_method in [ "create"]:            
            # skip 无需处理，load原样返回,search 前面已处理
            return  
                  
        generate = BgmGenerator()
        bgm_path = generate.generate_bgm(work_space_path)
        
        design_config_data["project"]["background_music_path"] = "load:"+bgm_path
        
        save_json(design_config_data,design_config_path) 
        
     
    
    def _compose_video_assets(self)->None:
        
         # 创建compose file
        convertor = FormatConvertor(self.design_config_path,self.compose_config_path,self.work_space_path)
        convertor.convert()
      
        composer = VideoComposer(self.compose_config_path)       
        composer.generate(self.compose_video_path)   
    
    def generate_video(self)->None:  
        '''
        生成视频
        '''
        self._generate_video_voice()  
        self._generate_video_bgm() 
        self._generate_video_avatar()
        self._generate_voice_clips()
        self._generate_video_clips()    
        self._adjust_video_duration()    
        self._compose_video_assets()       
          
            
if __name__ == "__main__":    
   
    design_config_path = "检索素材库生成视频_04\config_design_3.json"
   
    generator = design_2_compose_wf(config_design_path= design_config_path)
    
    # generator.generate_video_cover()
    generator._generate_video_voice()  
    generator._generate_video_bgm() 
    generator._generate_video_avatar()
     
    generator._generate_voice_clips()
    generator._generate_video_clips()    
  
    
    generator._adjust_video_duration()    
    generator._compose_video_assets()
    
    print(f"IntegrateGenerator 执行完毕 at {datetime.now()}")
