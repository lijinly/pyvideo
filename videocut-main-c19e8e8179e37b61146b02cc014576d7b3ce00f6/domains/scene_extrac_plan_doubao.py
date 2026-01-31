import base64
import json
from volcenginesdkarkruntime import Ark
import re
from config import Config


class FenjingAnalyzer:
    def __init__(self,model:str="doubao-1-5-thinking-vision-pro-250428"):
        self.client = Ark(
                        base_url="https://ark.cn-beijing.volces.com/api/v3",
                        api_key = Config.ARK_API_KEY # 从环境变量读取API密钥
                    )
        self.model = model
        pass
    def _extract_voice_text(self,text:str)->str:
        pattern = r"‘(.*?)’"  # 匹配单引号内的内容（注意中文单引号）
        match = re.search(pattern, text)

        if match:
            extracted_text = match.group(1)
            return extracted_text
        else:
            return ""
    
    def _merge_clip_by_caption(self,config)->dict:
        
        targetShots = []
        groups =[]
        currentobj={"台词":""}
        
        for shot in config["shots"]:
            if shot["台词"] == currentobj["台词"]:
                currentobj["主体描述"] +="\n" + shot["主体描述"]
                currentobj["end_time"] = shot["end_time"]
            else:
                groups.append(currentobj)
                currentobj=shot 
            
        targetShots = [ item for item in groups if item["台词"] != ""  ] 
        
        for shot in targetShots:
            shot["台词"] = self._extract_voice_text(shot["台词"])
        
        config["shots"] = targetShots
        
        return config
            
 
    def analyze_fenjing(self,video_path: str):
        """解构对标视频，获取分镜头组合"""
        # 构造9维度拆解Prompt（核心指令）
        analysis_prompt = """        
        **请逐镜头拆解视频分镜结构，每个镜头需包含以下9个维度：
        1. [主体描述]: 核心对象的动作/表情/位置
        2. [光影色调]: 光线方向/强度 + 主色调/配色方案
        3. [镜头语言]: 景别(特写/中景/全景) + 运镜方式(推/拉/摇) + 构图
        4. [动态效果]: 物体/镜头运动 + 后期特效
        5. [环境背景]: 场景物理空间 + 道具布置
        6. [风格]: 视觉艺术流派
        7. [技术参数]: 分辨率/帧率/编码格式
        8. [台词]: 人物对白/画外音
        
        **基于上面的分析结果，请提取视频画面的宽度、高度，帧率、视频长度、视频的整体描述
        **输出为JSON格式：{"project":{"description":"视频的整体描述","width": 540,"height": 960,"frame_rate": 30,
        "duration": 60, "background_music_path": "背景音乐的名字.mp3"},"shots": [{"shot_id":1, "start_time":0.0, "end_time":2.5, ...维度字段...}]}
        """
  
        fileurl = f"data:video/mp4;base64,{base64.b64encode(open(video_path, 'rb').read()).decode('utf-8') }"
      
        messages=[{ "role": "user", 
                        "content": [                   
                            {"type":"video_url","video_url": {"url": fileurl }},
                            { "type": "text","text": analysis_prompt} ] } ]
       
        response = self.client.chat.completions.create(           
            model=self.model, # "doubao-1-5-thinking-vision-pro-250428",
            messages= messages
              )

        print(response.choices[0].message.content)
        
        obj = json.loads(response.choices[0].message.content)
        
        self._save_config(obj=obj,file_path=readme_path.split(".")[0]+"_draft.json")
        
        obj = self._merge_clip_by_caption(obj)
        
        readme_path = video_path.split(".")[0]+"_analysis.json"
        
        # with open(readme_path, 'w',encoding="utf-8") as f:           
        #     json.dump(obj, f,ensure_ascii=False, indent=2)
        self._save_config(file_path=readme_path,obj=obj)
            
        
    def _load_config(self, file_path:str)->object:        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)  
        
    def _save_config(self,obj,file_path:str) :
        with open(file_path, 'w',encoding="utf-8") as f:           
            json.dump(obj, f,ensure_ascii=False, indent=2)        
        
if __name__ == "__main__":
    
    videopath = "extract_videos/douyin_7513772615874399526.mp4"
    video_url = "https://www.douyin.com/aweme/v1/play/?video_id=v0300fg10000d134h0vog65genao90o0"
 
 
    # config_path = "extract_videos/douyin_7513772615874399526_analysis.json"
    desc = FenjingAnalyzer()  
    desc.analyze_fenjing(videopath) 
    # obj = desc._load_config(config_path)   
    # obj= desc._merge_clip_by_caption(obj)
    # desc._save_config(obj=obj,file_path=config_path.split(".")[0]+"_merged.json")
      
    
    
    