
import os
import platform
from dotenv import load_dotenv
from pathlib import Path
import torch  


load_dotenv()  # 加载 .env 文件

class Config:
    # 系统平台 windows linux
    SYSTEM = platform.system()
    # GPU
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
   
    print(f"torch 设备: {DEVICE}，torch版本：{torch.__version__}")
    
  
    # torch.hub.set_dir(Config.cache_dir) 
    # 基于当前文件所在目录的父目录（项目根目录）构建路径
    # 这样无论脚本在哪里执行，路径都能正确定位
    project_root = Path(__file__).parent.parent  # 根据实际文件位置调整层级
    asset_space_dir = os.path.join(project_root, ".asset_space")
    cache_dir =os.path.join( asset_space_dir, ".cache"  ) 
    
    font_windows_path = os.path.join(cache_dir,"NotoSerifCJK-Bold.ttc" )
    font_linux_path = r"/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
    nltk_cache_dir = os.path.join(cache_dir, "nltk")
    jieba_cache_dir = os.path.join(cache_dir, "jieba")
    
    dbs_dir = os.path.join( asset_space_dir , ".dbs"  )  
    asset_root_dir= project_root                                          # 素材库根目录
    video_chroma_dir =  os.path.join(dbs_dir, "chroma_video"    )      # 视频素材的数据库路径
    audio_chroma_dir = os.path.join(dbs_dir, "chroma_audio") # 音频素材的数据库路径

    
    os.makedirs(cache_dir,exist_ok=True)
    os.makedirs(video_chroma_dir,exist_ok=True)
    os.makedirs(audio_chroma_dir,exist_ok=True)
    os.makedirs(nltk_cache_dir,exist_ok=True)
    os.makedirs(jieba_cache_dir,exist_ok=True)
        
    apihz_uid = os.getenv("apihz_uid")  
    apihz_key = os.getenv("apihz_key") 

    dashscope_api_key = os.getenv("dashscope_api_key")
    ARK_API_KEY = os.getenv("ARK_API_KEY")
    
    frame_interval = 30                                         # 抽帧间隔（帧数）
    blip_generate_model = "Salesforce/blip-image-captioning-base"        # 多语言轻量模型（中英文支持）
    blip_retrieval_model ="Salesforce/blip-itm-base-coco"
    question_model="Salesforce/blip-vqa-base"
    clap_model = "laion/clap-htsat-unfused"
    
    stop_words ={
                # 中文停用词（高频虚词、代词、语气词等）
                "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", 
                "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好",
                "自己", "这", "吗", "呢", "啊", "呀", "哦", "唉", "哎哟", "哼", "吧", "哈", "亲", 
                "商品", "下单", "包邮", "爆款", "热卖", "正品", "他", "我们", "他们", "这个", "那些", 
                "哪里", "非常", "已经", "再", "还", "虽然", "即使", "因此", "有", "叫", "使", "让",                
                # 英文停用词（冠词、介词、代词、助动词等）
                "a", "an", "the", "in", "on", "at", "with", "by", "for", "about", 
                "is", "am", "are", "was", "were", "be", "been", "being", "have", "has", 
                "had", "do", "does", "did", "can", "could", "will", "would", "shall", 
                "should", "must", "may", "might", "I", "you", "he", "she", "it", "we",
                "they", "me", "him", "her", "us", "them", "my", "your", "his", "its", "our", "their",
                "and", "but", "or", "so", "because", "if", "then", "very", "too", "more", 
                "most", "not", "no", "yes", "this", "that", "these", "those", "here", 
                "there", "when", "where", "how", "why", "which", "who", "whom", "what"
                }
    
    product_categories = {"美妆": ["口红", "粉底", "眼影"], "3C": ["手机", "耳机", "充电器"]}


    # 配置日志，便于定位错误