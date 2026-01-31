import os
from pathlib import Path
from openai import OpenAI
import requests

from .config import Config
from .tools import chat, save_image,save_text

# 请确保您已将 API Key 存储在环境变量 ARK_API_KEY 中
# 初始化Ark客户端，从环境变量中读取您的API Key
class ImageGenerator:
    def __init__(self, modelname:str="doubao-seedream-3-0-t2i-250415",):
        
        self.client = OpenAI(
            # 此为默认路径，您可根据业务所在地域进行配置
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            # 从环境变量中获取您的 API Key。此为默认方式，您可根据需要进行修改
            # api_key=os.environ.get("ARK_API_KEY"),
            api_key = Config.ARK_API_KEY 
            )
        self.model = modelname
        
       
    
    def _optimize_prompt(self,prompt:str)->str:
        optimizing_prompt = f"""        
        您是一位文生图的专家，我要让AI帮我制作电商带货短视频的首帧。
        请帮设计给文生图模型的提示词，要求如下：
        1、参考这段短视频的画面描述：{prompt}
        2、参考这个文生图描述格式：[艺术风格] + [主体描述] + [细节特征] + [环境氛围] + [光影效果] + [构图视角] + [技术参数]
        3、参考电商带货的视频画面特点
        4、针对火山的文生图模型模型优化
        5、仅输出提示词，其它不输出
        """
        optimized_prompt = chat(optimizing_prompt)
        
        print(f"优化图片提示词完成:{optimized_prompt}")  
        
        return optimized_prompt
    
    def generate_image(self,prompt:str,output_image_path:str,size :str="540x960")->None:
        
        optimized_pompt = self._optimize_prompt(prompt=prompt)
         
        response = self.client.images.generate(
            # 指定您创建的方舟推理接入点 ID，此处已帮您修改为您的推理接入点 ID
            model= self.model,
            prompt= optimized_pompt,#"鱼眼镜头，一只猫咪的头部，画面呈现出猫咪的五官因为拍摄方式扭曲的效果。",
            size=size,
            response_format= "url" ,
            quality= "high",
            output_format= "jpeg",
            extra_body={"watermark": False}                   
        ) 
        
        img = requests.get(response.data[0].url).content
        
        # 保存图片
        # with open(output_image_path, 'wb+') as f:
        #     f.write(img)
        save_image(img,output_image_path)
            
            
        image_prompt_path =Path( output_image_path).with_suffix(".txt") # .split(".")[0]+".txt"
            
        save_text(optimized_pompt,image_prompt_path) 
               
        print(f"图片已生成：{output_image_path}")
        
       
        
    
        

if __name__ == "__main__":
   
    prompt = """
    对比测试：一边是普通粉底液，另一边是Glow Beauty，喷洒水雾后，普通粉底液迅速斑驳，而Glow Beauty保持完美。
    """
 
    file_path = "render_videos/Tropicshade_Coconut_Hair_Care_Cream/Optimize_Intro_Clip_jimeng.jpeg"
    generator = ImageGenerator()
    generator.generate_image(prompt,file_path)
 