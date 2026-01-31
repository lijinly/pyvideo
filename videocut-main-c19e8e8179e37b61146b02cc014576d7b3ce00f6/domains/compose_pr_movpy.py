import json
import os
from pathlib import Path 
from moviepy import vfx, ImageClip, VideoFileClip,AudioFileClip,TextClip,CompositeVideoClip,CompositeAudioClip,ColorClip,concatenate_videoclips

from domains.config import Config
from .tools import get_valid_frames_duration, load_json
from ffmpeg._ffmpeg import input,output

from moviepy.audio.fx import MultiplyVolume,AudioLoop

class VideoComposer:
    """基于JSON配置和MoviePy库的短视频生成器"""
    
    def __init__(self, config_path):
        """初始化生成器并加载配置"""
        self.config = load_json(config_path) 
        self.assets = {}  # 存储加载的素材   
    

    
    def _load_video_clip(self, source_path, start_time, duration):
        """加载视频片段并处理时间"""        
        width = self.config["project"]["width"]
        height = self.config["project"]["height"]
        fps = self.config["project"]["frame_rate"]
        
        sub_clip_start =  0
        sub_clip_duration =  duration
  
        path_parts = source_path.split("$")  
        source_path = path_parts[0] 
        if len(path_parts) > 1:  # 修改条件判断，确保path_parts[1]存在
           sub_clip_start =float( path_parts[1])
        if len(path_parts) > 2:  # 修改条件判断，确保path_parts[2]存在
           sub_clip_duration =float(  path_parts[2])
           
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"路径不存在: {source_path}")
   
        
        target_ratio = height/width
        
        if source_path not in self.assets: 
            videoClip = VideoFileClip(filename= source_path)
            current_ratio =  videoClip.h / videoClip.w
            target_ratio = height/width
           
            # 处理缩放比例
            if current_ratio > target_ratio:
           
                videoClip = VideoFileClip(filename= source_path,target_resolution=(None,height))
                          
            elif current_ratio < target_ratio: 
                         
                videoClip = VideoFileClip(filename= source_path,target_resolution=(width,None))      
            
            else :
                videoClip = VideoFileClip(filename= source_path,target_resolution=(width,height))    
                
          
            videoClip = videoClip.with_fps(fps)
            videoClip = videoClip.with_position("center","center")
            self.assets[source_path] = videoClip
  
        videoClip = self.assets[source_path]    
            
        # 确保剪辑的结束时间不超过视频的总时长
        clip_end_time = sub_clip_start + sub_clip_duration
        if clip_end_time > videoClip.duration:
            clip_end_time = videoClip.duration
            sub_clip_duration = clip_end_time - sub_clip_start
            
        sub_clip = videoClip.subclipped(sub_clip_start, clip_end_time)
            
        # 调整时长，长了就截取，短了就放慢
        sub_clip = sub_clip.with_speed_scaled(final_duration=duration) 
        sub_clip = sub_clip.with_start(start_time)
        
        return sub_clip
    
    def _load_image_clip(self, source_path, start_time, duration):
        """加载视频片段并处理时间"""
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"路径不存在: {source_path}")
        
        if source_path not in self.assets:
            imageClip = ImageClip(img=source_path)
            current_ratio =  imageClip.h / imageClip.w
            target_ratio = self.config["project"]["height"]/self.config["project"]["width"]
            if current_ratio > target_ratio:
                new_height = self.config["project"]["height"]            
                imageClip =  imageClip.with_effects([vfx.Resize(height=new_height)]) 
            else:
                new_width = self.config["project"]["width"]          
                imageClip =  imageClip.with_effects([vfx.Resize(width=new_width)])           
               
            self.assets[source_path] = imageClip
        
        
        clip = self.assets[source_path]
        
        
        clip = clip.with_start(start_time) 
        clip = clip.with_duration(duration) 
        
        return clip
   

    def _create_subtitle_clip(self, subtile_path:str, start_time:float, duration:float)->object:
        """
        根据字幕文件，返回一组字幕的textclip
        """  
       
        # 
        video_with = self.config["project"]["width"]
        caption_width = int( video_with *0.9)
        margin_horizontal =int( video_with*0.05) #直接截取整数部分

        # 读取srt文件中的定义
        # subtitles_list = [
        #     ((0, 3), "第一行字幕"),  # 0-3秒显示
        #     ((3, 6), "第二行字幕"),  # 3-6秒显示
        # ]
        subtitles_list = []
        
        with open(subtile_path, 'r', encoding='utf-8') as f:
            subtitles_list = json.load(f)     
        
        #创建textclip子片段集合 
        subtile_clips = []   
        for subtitle in   subtitles_list   :
            
            if Config.SYSTEM  == "Windows"  :          
                # Windows 字体默认路径（固定，无需修改）
                font_path = Config.font_windows_path # "C:/Windows/Fonts/msyh.ttc"
            elif Config.SYSTEM  == "Linux"  : 
                font_path = Config.font_linux_path #r"/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"  
             
            # [[0.0, 3.0 ], " Oh no, your foundation just gave up on you."  ]    
            subtitle_clip = TextClip(font=  font_path,#"c:/windows/font/msyh.ttc",
                                            text= subtitle[1], 
                                            method="caption",
                                            text_align="center",
                                            size=(caption_width,None),
                                            font_size=28,
                                            duration=subtitle[0][1],
                                            margin=(margin_horizontal,None,margin_horizontal,10),
                                            color='white')               
           
            subtile_clips.append(subtitle_clip)
        
        concated_clip = concatenate_videoclips(subtile_clips)
        concated_clip = concated_clip.with_position((0.0, 0.8),relative = True)  
        concated_clip = concated_clip.with_start(start_time)
        
        if concated_clip.duration > duration:
            concated_clip = concated_clip.with_duration(duration)
        
        return concated_clip 
      
   
    
    def _create_text_clip(self, content, font, font_size, color, position, start_time, duration, bg_color=None):
        """创建文字片段"""
        project = self.config["project"]
        # 处理相对位置（百分比）
        x, y = position["x"], position["y"]
        
        if isinstance(x, str) and x.endswith("%"):
            x = int(project["width"] * float(x.strip("%")) / 100)
        if isinstance(y, str) and y.endswith("%"):
            y = int(project["height"] * float(y.strip("%")) / 100)
        
        # 创建文字片段
        font_path = "c:/windows/font/msyh.ttc"
        txt_clip = TextClip(
            font = font_path,
            text = content, 
            font_size = font_size,
            color = color,           
            size = (project["width"], project["height"]),
            method="caption" 
        )
        
        # 设置位置和时间
        txt_clip = txt_clip.with_duration(duration)
        txt_clip = txt_clip.with_start(start_time)
        
        if x<1 and y<1:        
            txt_clip = txt_clip.with_position((x, y), relative=True) 
        else :
            txt_clip = txt_clip.with_position((x, y)) 
        
        # 添加背景（如果需要）
        if bg_color:
            bg_clip = ColorClip(
                size=(txt_clip.w + 20, txt_clip.h + 20),
                color=self._hex_to_rgb(bg_color)
            ).set_opacity(0.6)

            bg_clip = bg_clip.with_opacity(0.6)
            bg_clip = bg_clip.with_position('center')

            txt_clip = CompositeVideoClip([bg_clip, txt_clip])
        
        return txt_clip
    
    def _hex_to_rgb(self, hex_color):
        """将十六进制颜色转换为RGB元组"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _load_audio_clip(self, source_path, start_time, duration, volume=1.0):
        """
        加载语音的音频片段、处理时间和音量
        start_time ,音频在目标视频中的开始位置
        duration,音频在目标视频中要播放的长度
        """
        if source_path not in self.assets:            
            audio_clip = AudioFileClip(source_path) 
            self.assets[source_path] =  audio_clip            
        clip = self.assets[source_path] 
        
        sub_duration = min(clip.duration,duration)
        sub_clip = (clip.with_start(start_time) #设置开播时间
                    .with_duration(sub_duration)#设置播放时长
                    .with_effects([MultiplyVolume(factor=volume)]) #设置音量 
                    )
    
        
        return sub_clip
    
    def _load_bgm_clip(self, source_path, start_time, duration, volume=1.0):
        """
        加载背景音乐的音频片段、处理时间和音量
        start_time ,音频在目标视频中的开始位置
        duration,音频在目标视频中要播放的长度
        """
        
        # 处理路径中带的参数 
        #"path$start$duration"
        #path:音频的路径
        #start:截取的起点
        #duration:截取的长度
  
        path_parts = source_path.split("$")  
        source_path = path_parts[0] 
        sub_clip_start = 0.0
        sub_clip_duration = float('inf')
        if len(path_parts) > 1:
           sub_clip_start =float( path_parts[1])
        if len(path_parts) > 2:
           sub_clip_duration =float(  path_parts[2])
           
        if source_path not in self.assets:            
            audio_clip = AudioFileClip(source_path)           
            self.assets[source_path] =  audio_clip            
        clip = self.assets[source_path] 
        
        sub_duration = min(clip.duration-sub_clip_start,sub_clip_duration,duration)
        sub_clip = (clip.subclipped(sub_clip_start,sub_clip_start+sub_duration)
                    .with_start(start_time) #设置开播时间
                    .with_duration(sub_duration)#设置播放时长
                    .with_effects([MultiplyVolume(factor=volume),AudioLoop(duration=duration)]) #设置音量 
                    )
   
        
        return sub_clip
        
    
    def _create_background_clip(self,output_path:str)->object:
        # 1. 定义图像尺寸和颜色
        width, height = self.config["project"]["width"], self.config["project"]["height"]  # 自定义宽高
        background_color = (128, 128, 128)  #标准灰 RGB白色 (255,255,255)

        # # 2. 创建白色背景图（PIL实现）
        bg_clip = ColorClip( size=(width, height),color= background_color,duration=self.config["project"]["duration"])
        return bg_clip
    
    def generate(self, output_path:str):
        """生成视频"""
        project = self.config["project"]
        timeline = self.config["timeline"]
        
        # 创建输出目录
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 初始化视频和音频轨道        
        video_clips = []        
        audio_clips = []
        text_clips = []       
       
     
                                           
        # 处理视频轨道
        for track in timeline["tracks"]:
            if track["type"] == "video":
                for item in track["items"]:
                    if item["type"] == "clip":                        
                        # 加载视频片段
                        clip = self._load_video_clip(
                            item["source_path"], 
                            item["start_time"], 
                            item["duration"]
                        )
                        if clip:
                            video_clips.append(clip)

                    elif item["type"] == "image":                        
                        # 加载视频片段
                        clip = self._load_image_clip(
                            item["source_path"], 
                            item["start_time"], 
                            item["duration"]
                        )
                        if clip:
                            video_clips.append(clip) 

            elif track["type"] == "text": 
                for item in track["items"]:      
                    if item["type"] == "text":      
                        # 创建文字片段
                        bg_color = item.get("background_color")
                        txt_clip = self._create_text_clip(
                            item["content"],
                            item.get("font","arial"),
                            item["font_size"],
                            item["color"],
                            item["position"],
                            item["start_time"],
                            item["duration"],
                            bg_color
                            )
                        text_clips.append(txt_clip)
                    elif item["type"] == "subtitle": 
                        subtitle_clip = self._create_subtitle_clip(
                            item["source_path"],
                            # item.get("font","arial"),
                            # item["font_size"],
                            # item["color"],
                            # item["position"],
                            item["start_time"] + 0.1,#声音字幕延迟300ms
                            item["duration"]
                            # bg_color
                            )
                        text_clips.append(subtitle_clip) #.append(txt_clip)
                        
            
            elif track["type"] == "audio":
                for item in track["items"]:
                    # 加载音频片段
                    if item["type"]=="voice":
                        audio_clip = self._load_audio_clip(
                            item["source_path"],
                            item["start_time"] + 0.1,#声音字幕延迟300ms
                            item["duration"],
                            item.get("volume", 1.0)
                        )                    
                
                        audio_clips.append(audio_clip)
                        
                    elif item["type"] == "bgm":
                        audio_clip = self._load_bgm_clip(
                            item["source_path"],
                            item["start_time"],
                            item["duration"],
                            item.get("volume",0.3)
                        )                    
                
                        audio_clips.append(audio_clip)
                    else:
                        pass
       
        # 合并视觉clips
        visual_clips =[]
        # 创建背景图片
     
        # bgp_clip = self._create_background_clip(output_path=output_path)
        # visual_clips +=[bgp_clip]
        
        visual_clips.append(concatenate_videoclips( video_clips))
        visual_clips.extend(text_clips)
         
        # 合成视频和音频        
        final_audio = CompositeAudioClip(audio_clips)       
        final_video = CompositeVideoClip(visual_clips) 
     
        #   
        final_video = final_video.with_audio(final_audio).with_duration(project["duration"])
        
      
        # 导出视频
        codec = self.config["export"].get("codec", "libx264")
        fps = project.get("frame_rate", 30)
        
            
        # 确保临时音频文件目录存在  
        output_dir = Path(output_path).parent
        os.makedirs(output_dir,exist_ok=True)
        
        
        print(f"compose video starting: {output_path}")
        final_video.write_videofile(
            output_path,
            codec=codec,
            fps=fps,
            audio_codec="aac",
            threads=4,
            temp_audiofile_path=output_dir
        )
        print(f"compose video ended: {output_path}")
         
        # 处理尾帧闪烁，精确到帧的时长计算
       
        # clip = VideoFileClip(output_path)
        # exact_duration = clip.duration - (1/clip.fps)  # 减去最后一帧       
        # exact_duration = get_valid_frames_duration(output_path)
        # # 添加封面
        
        # file_dir = Path(output_path).parent
        # file_stem = Path(output_path).stem
        
        # final_video_path = os.path.join(file_dir,file_stem+"_final.mp4")  
        
        # input_video = input(output_path)

        # if  ( "cover_path" in self.config["project"]  
        #     and self.config["project"]["cover_path"].strip()
        #     and os.path.exists(self.config["project"]["cover_path"].strip())):
            
        #     input_cover = input( self.config["project"]["cover_path"])            
        #     (output(
        #         input_video, 
        #         input_cover,
        #         final_video_path,
        #         vcodec="copy",          # 复制视频流（不重新编码）
        #         acodec="copy",          # 复制音频流（不重新编码）
        #         t=exact_duration,  
        #         **{"disposition:v:1": "attached_pic"}  # 关键：将第二个视频流设为封面
        #     ).run(overwrite_output=True))
            
        # else:
            
        #     (output(
        #         input_video,
        #         final_video_path,
        #         vcodec="copy",
        #         acodec="copy",
        #         t=exact_duration
        #     ).run(overwrite_output=True))
        
        # print(f"视频收尾完成: {output_path}")
        # 关闭所有素材
        for asset in self.assets.values():
            try:
                asset.close()
            except Exception:
                pass
        
        return output_path

if __name__ == "__main__":
    # 使用示例
    config_path = "content_design/检索素材库生成视频_02/config_design_4 copy/compose_config.json"  # JSON配置文件路径
    output_path = "content_design/检索素材库生成视频_02/config_design_4 copy/compose_video_04.mp4"     # 输出视频路径
    
    generator = VideoComposer(config_path)
    generator.generate(output_path)