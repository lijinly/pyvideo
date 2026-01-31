import os
from pathlib import Path
import requests
from http import HTTPStatus
from dashscope import VideoSynthesis
import dashscope

from domains.tools import chat,parse_json
from domains.config import Config

class VideoGenerator:
    def __init__(self,model:str="wanx2.1-i2v-turbo"): 
        dashscope.api_key = Config.dashscope_api_key
        self.model = model  
        
    def _optimize_prompt(self,prompt:str)->dict:
        optimizing_prompt =f"""
        
        您是一位图生视频的专家，我需要让AI用图生视频的方式为我创作电商带货短视频。
        请帮我生成给图生视频模型的提示词，用来生成一个分镜，要求如下：
        - 主体描述：{prompt} 
        - 请设计：[主体描述]、[光影色调]、[镜头语言]、[动态效果]、[环境背景]、[风格]、[参数] 
        - 参考电商带货的视频画面特点
        - 只输出正面提示词及负面提示词，其它信息不输出 
        严格按如下Json格式输出分析结果 ：
        json'''
        {{"positive_prompt":"正面提示词","negtive_prompt":"负面提示词"}}
        '''
        """
        prompt = chat(optimizing_prompt)
       
        
        print(f"optimized prompt:{prompt}")      
        
        prompt = parse_json(prompt)[0]
        
        return prompt
    
    def generate_video(self, prompt:str, image_path:str, video_path:str,duration:float=5)->str:
        """调用异步接口生成视频"""
    
        optimized_prompt = self._optimize_prompt(prompt= prompt)
      
        image_path = f"file://"+image_path
            
        rsp = VideoSynthesis.async_call(
                                model = self.model,# 'wanx2.1-i2v-turbo',
                                prompt=optimized_prompt["positive_prompt"],
                                negative_prompt=optimized_prompt["negtive_prompt"],
                                img_url=image_path,
                                parameters={
                                    "resolution": "720P",  # 支持480P/720P/1080P
                                    "fps": 8,              # 帧率（默认8fps）
                                    "duration": duration           # 视频时长（秒）
                                })
        if rsp.status_code == HTTPStatus.OK:
            print("task_id: %s" % rsp.output.task_id)
        else:
            print('Response Failed, status_code: %s, code: %s, message: %s' %
                (rsp.status_code, rsp.code, rsp.message)) 
                
                
        # wait the task complete, will call fetch interval, and check it's in finished status.
        rsp = VideoSynthesis.wait(rsp)
        print(rsp)
        if rsp.output.task_status !="SUCCEEDED":
                print('Task Failed, task_status: %s' %(rsp.output.task_status))             
            
        video_url = rsp.output.video_url
        
        prompt_full = "orig_prompt:"+ rsp.output["orig_prompt"] +"\n actual_prompt:"+rsp.output["actual_prompt"]
        
        response = requests.get(video_url, stream=True)
        
        if response.status_code == 200:
            with open(video_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"视频已下载至: {os.path.abspath(video_path)}") 
            
            video_prompt_path = Path(video_path).parent / (Path(video_path).stem + "_prompt.txt")
            
            with open(video_prompt_path, "w", encoding="utf-8") as file:
                file.write(prompt_full)           
                        
                

        return None

    

if __name__ == "__main__":    
 
    
    # 参数配置
    image_path ="render_videos/Tropicshade_Coconut_Hair_Care_Cream/Optimize_Intro_Clip_jimeng.jpeg"           # 输入图片路径
    prompt_text = "对比测试：一边是普通粉底液，另一边是Glow Beauty，喷洒水雾后，普通粉底液迅速斑驳，而Glow Beauty保持完美。"
    video_path = "render_videos/Tropicshade_Coconut_Hair_Care_Cream/Optimize_Intro_Clip_qwen.mp4"               # 输出目录
    
    
    # 执行生成
    generator = VideoGenerator()
    video_url = generator.generate_video(prompt=prompt_text, image_path= image_path, 
                                         video_path=video_path,duration=2)
   
      
 
    
    
 
 
  
   