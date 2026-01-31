# coding=utf-8

import json
from pathlib import Path
import re
import dashscope
from dashscope.audio.tts import SpeechSynthesizer as v0SpeechSynthesizer

from .tools import  process_phone_numbers, save_json, save_text,split_with_quotes
from .config import Config


class VoiceGenerator:
    """
    使用qwen.cosy，根据台词合成语音
    """
      
    def __init__(self,model:str = "sambert-zhimao-v1",voice:str ="longanran" ):
        """
        使用qwen.cosy，根据台词合成语音
        """
        # 若没有将API Key配置到环境变量中，需将your-api-key替换为自己的API Key
        dashscope.api_key = Config.dashscope_api_key
         # 模型
        self.model = model
        # 音色
        self.voice = voice
        
    def generate_voice(self,voice_text: str,voice_file_path:str) -> object:
        """
        合成音频文件并保存到voice_output_path
        """ 
        # 删除所有空白字符
        voice_text =  re.sub(r'^\s+|\s+$', '', voice_text) 
        
        # needing,_ = needs_say_as_tag(voice_text)
        
        optimized_text = process_phone_numbers( voice_text)        
                   
        rrst = v0SpeechSynthesizer.call(model=self.model
                                        ,text=optimized_text
                                        ,word_timestamp_enabled=True)
        texts = rrst.get_timestamps()        
        audio = rrst.get_audio_data()
        
         # 保存时间戳     
        timestamp_path = Path(voice_file_path).with_suffix(".json")  # voice_file_path.split(".")[0]+".json"
        save_json(texts,timestamp_path)
        
        # 处理字幕
        raw_voice_texts =  split_with_quotes(voice_text)  
        raw_voice_texts_path = Path(voice_file_path).with_suffix(".txt") # voice_file_path.split(".")[0]+".txt"
        save_text( "\n".join(raw_voice_texts),raw_voice_texts_path)    
        
        subtiles = [] 
        for i, seg in enumerate(texts): 
            
            if len(texts) == len(raw_voice_texts):  
                subtiletext = raw_voice_texts[i]
            else:                              
                subtiletext = "".join([ word["text"] for word in  seg["words"]])                       
            
            subtiles.append({"start":seg["begin_time"],"end":seg["end_time"],"text":subtiletext})
        
        # 保存改良后的字幕
        subtile_path = Path( voice_file_path).with_suffix(".srt") #.split(".")[0]+".srt"    
       
        with open(subtile_path, "w",encoding="utf-8") as f:
            objs = []
            for i, seg in enumerate(subtiles):                 
                subtiletext = seg["text"] 
                start_time = round(seg['start'] / 1000, 3)
                end_time = round(seg['end'] / 1000, 3)
                objs.append(((start_time,round(end_time-start_time,3)),subtiletext))
            json.dump(objs, f,ensure_ascii=False, indent=2)  
       
        
        # 将音频保存至本地
        with open(voice_file_path, 'wb') as f:
            f.write(audio)
        
      
        
        return audio
      
            
if __name__ == "__main__":
    
    content = """
    速速拨打400-400-56578，不想挤高铁？来试试大方租车呀！APP一键下单，覆盖全国90%机场和高铁站，24小时救援服务全程护航～速抢200元无门槛券！
    """
    
    generator = VoiceGenerator()
    
    audio = generator.generate_voice(content,"render_videos/create_voice_sambert.wav")
    
    