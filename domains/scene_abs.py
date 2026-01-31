from abc import ABC, abstractmethod 
import os 
from pathlib import Path
import time

from utils.logs import setup_logger 
from .tools import build_user_space_dir, chat, load_json, parse_json,save_json


class abs_scene(ABC):
    """
    负责生成策划文件，并保存到用户的工作空间
    """
 
    def __init__(self,plan_name :str, user_id:str= "default"):
        """
        初始化场景
        """      
        # 基类构造函数中可以初始化通用属性
        user_work_space_dir =  build_user_space_dir(user_id)
        scene_type = self.return_scene_type()
        self.biz_work_space_dir = os.path.join(user_work_space_dir,scene_type)
        os.makedirs(self.biz_work_space_dir,exist_ok=True) 
        self.plan_path = os.path.join(self.biz_work_space_dir,plan_name+".json")
       
        self.logger = setup_logger(name="abs_scene")  
 
    def save_plan(self,plan_data:dict)->str: 
        """
        保存plan文件
        """      
        plan_path = self.plan_path
        save_json(plan_data,plan_path)
       
        self.plan_data = plan_data
        self.plan_path = plan_path
        return self.plan_path
    
    def load_plan(self)->object:
        """
        加载plan文件
        """         
        #  # 确保策划案在用户的工作空间
        # copy_file_if_not_exists(plan_path, self.biz_work_space_dir)   
        
        # plan_name = Path(plan_path).name 
        
        # self.plan_path = os.path.join(self.biz_work_space_dir, plan_name)
        self.plan_data = load_json(self.plan_path)
        return self.plan_data
     
    
    @abstractmethod
    def return_scene_type(self) -> str:
        """
        返回场景的类型
        """  
             
    
    @abstractmethod
    def make_prompt(self) -> str:
        """
        构造提示词
        """
        self.load_plan()
        
    def get_plan_path(self)->str:
        return self.plan_path
         
    # def _generate_prompt(self):
    #     """
    #     生成背景提示词
    #     """
    #     return self.scene.make_prompt()
        
    def generate_copywrites(self):
        """
        根据背景信息，创作文案
        """              
        prompt =self.make_prompt()
        
        batch_size = self.plan_data["plan"]["batch_size"]
        
        prompt +=f"结合以上信息，帮我生成{batch_size}条爆款文案\n"
        
        copywrite_structure = self.plan_data["plan"]["copywrite_structure"]
        
        structure_text = "+".join([item["description"] for item in copywrite_structure["structure"]])
        rhythm = copywrite_structure["Rhythm"]
        style_tone = copywrite_structure["style_tone"]
        
        prompt += f"生成文案时要严格套用这个文案结构：{structure_text}\n"
        prompt += f"节奏：{rhythm}\n"
        prompt += f"语言：{style_tone}\n"
        
        prompt += f"""        
        请严格按以下json格式输出，禁止输出其他内容：
        Json '''[{{"copywrite_text":"具有{style_tone}语言风格的文案内容",
        "copywrite_structure":"{structure_text}"}}]'''
        """
        
        result = chat(prompt)
        
        copywrites = parse_json(result)[0]
        
        for item in copywrites:
            item["choosen"] = True
        
        if not "copy_writes:" in self.plan_data:
            self.plan_data ["copy_writes"] = copywrites      
        else :           
            self.plan_data ["copy_writes"].extend(copywrites)
            
        save_json(self.plan_data,self.plan_path) 
        
        self.logger.info(copywrites)
                   
    def generate_stroyboards(self):
        """
        结合文案和文案结构，创做视频的分镜设计
        """
        
        config = self.plan_data 
        
        background_prompt = self.make_prompt()
        
        base_designs = []
        copy_writes_choosen = [item for item in config["copy_writes"] if item["choosen"] == True]
        
        copywrite_structure = self.plan_data["plan"]["copywrite_structure"]
        rhythm = copywrite_structure["Rhythm"]
        
        for copywrite in copy_writes_choosen:
            
            copywrite_text = copywrite["copywrite_text"]
            copywrite_structure = copywrite["copywrite_structure"]
            
            # 构造 video_clips
            append_prompt = f"""
            请结合视频文案：{copywrite_text},以及文案结构：{copywrite_structure}，帮我生成视频的分镜组合：           
            1.视频的节奏为：{rhythm}
            2.每个分镜，必须对应以上提供的文案结构中的一个部分，并用这个部分的文字给分镜做标注
            3.分镜设计要包含这些内容：[主体描述]、[光影色调]、[镜头语言]、[动态效果]、[环境背景]、[风格]、[参数]、[结构标注] 
            4.每个分镜的长度需不大于5秒
            5.请严格按如下json结构输出,严禁输出其它内容：
            Json '''[{{   "主体描述":"人物佩戴珍珠发箍，穿黑色带米色蕾丝装饰衣物，执行撕下脸部面膜的动作",
                          "光影色调":"暖光，光线柔和，主色调为暖黄色搭配黑、米色",
                          "镜头语言":"中景，固定镜头，采用居中构图",
                          "动态效果":"人物手部完成撕面膜动作，无复杂后期特效",
                          "环境背景":"室内场景，背景布置有台灯、插着粉色花朵的花瓶"
                          "风格":"美妆教程风格，呈现日常温馨感",
                          "技术参数":"分辨率540x960，帧率30，编码格式H.264",
                          "时长"：2,
                          "结构标注":"兴趣圈层共鸣"}}]'''
            """
            prompt = background_prompt + append_prompt
            
            shots_text = chat(prompt)
            
            shots = parse_json(shots_text)[0]
             
            clips = [] 
            
            for shot in shots:   
                visual_descs =[]    
                for k,v in shot.items():
                    if k in ["主体描述","光影色调","镜头语言","动态效果","环境背景","风格","技术参数"]:
                        visual_descs.append(f"{k} ：{v}") 
                visual_desc = "--".join(visual_descs)
                
                      
                
                for item    in self.plan_data["plan"]["copywrite_structure"]["structure"] :
                    
                    idnex =  shot["结构标注"].find( item["description"])
                    
                    if idnex != -1:
                        method=item["method"]
                        clips.append({
                            "type": "video",  
                            "description": visual_desc,           
                            "duration": shot["时长"],
                            "visual": method,#+"$"+shot["主体描述"],
                            "voice": "skip:project" , 
                            "structure":  shot["结构标注"]               
                            })
                        break 
                   
            
            voice =   "create:"+  copywrite_text
            background_music =  "search:"+  copywrite_text
            description = copywrite_text
                
                
            base_designs.append({
                "structure":copywrite_structure,
                "voice":voice,
                "description":description,
                "background_music" : background_music,
                "clips":clips                
            })            
            
            # 暂停一秒，防过于频繁调用
            time.sleep(0.5)
            
        if not "designs" in self.plan_data:
            
            self.plan_data["designs"] = []
        
        self.plan_data["designs"].extend(base_designs) 
        
        save_json(self.plan_data,self.plan_path) 
      