import os
from pathlib import Path
import random

from .tools import append_text, load_text,detect_media_type
from .asset_audio_ import AudioIndexDB
from .asset_video_ import VideoIndexDB
from utils.logs import setup_logger


class AssetIndex:
    """
    统一管理素材的存储和索引
    """
    def __init__(self):
        self.audio_index = AudioIndexDB()
        self.video_index = VideoIndexDB()
        self.logger = setup_logger(name="AssetIndex")
        pass
    
    def build_index(self, asset_dir: str):
            """构建音频特征索引数据库"""
            
            root_path = os.path.join(".asset_space","uploads")
            
            if not Path(asset_dir).is_relative_to(root_path):
                return 
            
            media_file_paths = []   
            progress_file_path = os.path.join(asset_dir, "progress.txt")
            
            
            # 递归遍历目录
            for current_dir, _, filenames in os.walk(asset_dir):
                for filename in filenames:
                    if detect_media_type(filename) in ( "video","audio","image"):  
                        
                        full_path = os.path.join(current_dir,filename) 
                        media_file_paths.append(full_path)
                            
            # 批量处理音频（去重已处理文件）
            handled_files = load_text(progress_file_path)
            media_file_paths = list(set(media_file_paths) - set(handled_files)) 
            random.shuffle(media_file_paths)
            
            from tqdm import tqdm 
            pbar = tqdm(total=len(media_file_paths), desc="处理中") 
            for file_path in media_file_paths:        
                try:
                    if detect_media_type(filename) == "audio" :
                        self.audio_index.process_audio(file_path)
                    elif  detect_media_type(filename) == "video" :
                        self.video_index.process_video(file_path)
                    elif detect_media_type(filename) == "image" :
                        pass
                    
                    append_text(file_path, progress_file_path)
                    
                except Exception as e:
                    print(f"处理文件失败 {file_path}: {e}")
                pbar.update(1)    
            pbar.close()   
            
    def search(self, query: str, top_k: int = 5):
        
        # 分别搜索音频和视频资源
        audio_results = self.audio_index.search(query, top_k)
        video_results = self.video_index.search(query, "", top_k)
        
        
        unified_results = []
               
        for result in audio_results:
            unified_results.append({
                "type": "audio",
                "id": result["audio_id"],
                "path": result["audio_path"],
                "start": result["clip_start"],
                "duration": result["clip_duration"],
                "score": result["score"],
                "query_text": result["query_text"]
            })
          
        
        for result in video_results:
            unified_results.append({
                "type": "video",
                "id": result["video_id"],
                "path": result["video_path"],
                "start": result["clip_start"],
                "duration": result["clip_duration"],
                "score": result["score"],
                "description": result["description"]
            })
            
        # 按分数排序并返回前top_k个结果（分数越低匹配度越高）
        unified_results.sort(key=lambda x: x["score"])
        return unified_results[:top_k]
