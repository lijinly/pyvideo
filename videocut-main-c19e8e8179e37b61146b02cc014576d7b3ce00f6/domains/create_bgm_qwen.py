import os
from pathlib import Path
import shutil
import random

class BGMGenerator:
    def __init__(self):
        project_root = Path(__file__).parent.parent
        
        self.dbm_store_path = project_root / ".asset_space" / "audios" / "bgm" #"assets_database\\bgm"
        pass
    
    def generate_bgm(self,target_dir:str)->str:
        source_dir = self.dbm_store_path
        # 创建目标文件夹（如果不存在）
        os.makedirs(target_dir, exist_ok=True)
        
        # 递归收集所有MP3文件路径
        mp3_files = []
        for root, _, files in os.walk(source_dir):
            for file in files:
                if file.lower().endswith(".mp3") or file.lower().endswith(".wma"):
                    mp3_files.append(os.path.join(root, file))
        
        # 检测是否存在MP3文件
        if not mp3_files:
            raise FileNotFoundError(f"未在 {source_dir} 中找到MP3文件")
        
        # 随机选择一个文件
        selected_file = random.choice(mp3_files)
        
        # 复制到目标文件夹
        shutil.copy2(
            selected_file,
            target_dir
            # os.path.join(target_dir, os.path.basename(selected_file))
        )
        return selected_file

    