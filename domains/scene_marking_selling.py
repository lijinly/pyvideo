 
from .scene_abs import abs_scene  

class marketing_selling_scene(abs_scene):
        
    def __init__(self,plan_name :str, user_id:str= "default"):
        # 调用父类的构造函数，确保基类属性被正确初始化
        super().__init__(plan_name,user_id)      
    
    def return_scene_type(self) -> None:
        return "marketing"     
   
    def make_prompt(self) -> str:
        """
        构造视频创作背景的提示词，支持 品牌营销和带货两个场景
        """
        super().make_prompt() 
        
        prompt = "你是一位爆款短视频策划专家，非常擅长撰写爆款文案以及策划分镜\n"
        
        # 创作意图       
        product_info = ""
       
        config_plan = self.plan_data["plan"] 
        
        if  "product_name" in config_plan and config_plan ["product_name"].strip():
            product_name = config_plan ["product_name"].strip()
            product_info += f"**产品名字**：{product_name}\n"
        
        if  "product_selling_points" in config_plan and len(config_plan["product_selling_points"]) >0:
            
            sell_points = [item.strip() for item in  config_plan["product_selling_points"]]
            sell_points =" -- ".join( sell_points)
            product_info += f"**产品卖点**：{sell_points}\n"
                
        
          # 品牌信息 
        brand_info = ""
           
        if "brand_name" in self.plan_data["plan"] and self.plan_data["plan"]["brand_name"].strip(): 
            brand_name = self.plan_data["plan"]["brand_name"].strip()
            brand_info += f"**品牌名字**:{brand_name}\n" 
        if "brand_story" in self.plan_data["plan"] and self.plan_data["plan"]["brand_story"].strip(): 
            brand_story = self.plan_data["plan"]["brand_story"].strip()
            brand_info += f"**品牌故事**:{brand_story}\n" 
       
        
        if product_info.strip():
            prompt += "我要创作带货短视频。\n"
            prompt += f"需要参考的产品信息：{product_info}\n " 
            prompt += f"需要参考的品牌信息：{brand_info}\n " 
        else:
            prompt += "我要市场推广短视频。\n"
            prompt += f"需要参考的品牌信息：{brand_info}\n " 
  
        
        if "target_channel" in self.plan_data["plan"] and self.plan_data["plan"]["target_channel"].strip():
            target_channel = self.plan_data["plan"]["target_channel"]
            target_channel = f"我想在{target_channel}渠道上投放视频\n"
            prompt += target_channel  
            
        # 视频想达到的目的
        if "core_objective" in self.plan_data["plan"] and self.plan_data["plan"]["core_objective"].strip(): 
            core_objective = self.plan_data["plan"]["core_objective"].strip()
            prompt += f"我想通过这个短视频达到的目的：{core_objective} \n"
        
        # 目标用户的特征（用户画像）
        if "User_portrait" in self.plan_data["plan"] and len(self.plan_data["plan"]["User_portrait"]) >0: 
            sell_portraits = [item.strip() for item in  config_plan["User_portrait"]]
            sell_portraits =" -- ".join( sell_portraits)
            sell_portraits = f"这个视频的目标用户的画像：{sell_portraits}\n"
            prompt += sell_portraits
        
        # 目标用户的地域（目标市场）
        if "target_market" in self.plan_data["plan"] and self.plan_data["plan"]["target_market"].strip(): 
            target_market = self.plan_data["plan"]["target_market"].strip()
            target_market =  f"这个视频的目标市场： {target_market}，需要根据目标市场，分析地区文化表达、宗教禁忌、法规约束\n"   
            prompt += target_market
        
        # 配套的市场活动
        if "market_campaign" in self.plan_data["plan"] and self.plan_data["plan"]["market_campaign"].strip(): 
            market_campaign = self.plan_data["plan"]["market_campaign"].strip()
            market_campaign = f"配套的市场推广活动：{market_campaign}\n"
            prompt += market_campaign       
       
           
        self.background_prompt = prompt
            
        return prompt