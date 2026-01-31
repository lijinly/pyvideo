from datetime import datetime
import os
from pathlib import Path
import random
import cv2
import numpy as np
from PIL import Image
import chromadb 
from chromadb.config import Settings 
import torch 
from transformers import BlipProcessor, BlipForConditionalGeneration, BlipForImageTextRetrieval 
import jieba
from sklearn.metrics.pairwise import cosine_similarity  
from utils.logs import setup_logger
 
from .config import Config
from .tools import append_text, detect_media_type, generate_file_hash, load_text, save_json
import jieba
import nltk

class VideoIndexDB:
    def __init__(self):       
      

        # 将缓存路径添加到NLTK的数据路径列表中（优先查找）
        nltk.data.path.insert(0, Config.nltk_cache_dir) 
        jieba.dt.tmp_dir = Config.jieba_cache_dir 

        self.logger = setup_logger(name="VideoIndexDB")
        
        # 检查CUDA是否可用
        self.device = Config.DEVICE 
               
        # 强制transformer 离线模式
        # os.environ["TRANSFORMERS_OFFLINE"] = "1"
        # 初始化多模态模型并移动到GPU
        self.generate_processor = BlipProcessor.from_pretrained(
            Config.blip_generate_model,
            cache_dir=Config.cache_dir,
            use_fast=True,
            use_safetensors=True
        )
        self.retrieval_processor = BlipProcessor.from_pretrained(
            Config.blip_retrieval_model,
            cache_dir=Config.cache_dir,
            use_fast=True,
            use_safetensors=True
        )
       
        # 加载模型并移动到指定设备
        self.generate_model = BlipForConditionalGeneration.from_pretrained(
            Config.blip_generate_model, 
            dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            cache_dir=Config.cache_dir,
            use_safetensors=True
        ).to(self.device)
        
        self.retrieval_model = BlipForImageTextRetrieval.from_pretrained( 
            Config.blip_retrieval_model, 
            dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            cache_dir=Config.cache_dir,
            use_safetensors=True
        ).to(self.device)
        
        # 启用推理优化
        if torch.cuda.is_available():
            self.generate_model.eval()
            self.retrieval_model.eval()
            # 启用FP16推理加速
            self.generate_model.half()
            self.retrieval_model.half()
        
        # 初始化数据库
        chromasettings = Settings(anonymized_telemetry=False)
        self.client = chromadb.PersistentClient(
            path=Config.video_chroma_dir,
            settings=chromasettings
        )
        self.collection = self.client.get_or_create_collection(
            name="video_assets", 
            metadata={"hnsw:space": "cosine"}
        )

    def _extract_frames(self, video_path: str) -> tuple:
        # 保持不变
        key_frames = []
        frame_idx = 0
        prev_frame = None
        
        cap = cv2.VideoCapture(video_path, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            self.logger.info(f"无法打开视频: {video_path}")
            return key_frames
        
        READ_TIMEOUT = 5000
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = round(total_frames/fps, 3)
        
        try:
            while True:
                start_time = cv2.getTickCount()
                ret = False
                frame = None
                
                while not ret:
                    ret, frame = cap.read()
                    elapsed = (cv2.getTickCount() - start_time) / cv2.getTickFrequency() * 1000
                    if elapsed > READ_TIMEOUT:                     
                        ret = False
                        self.logger.info(f"读取超时（{READ_TIMEOUT}ms），退出读取：{video_path}")
                        break
                
                if not ret:  
                    duration = round(frame_idx/fps, 3)                 
                    break
                
                if prev_frame is None:
                    key_frames.append({
                        "frame": Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)),
                        "idx": frame_idx
                    })
                    prev_frame = frame
                else:
                    diff = cv2.absdiff(prev_frame, frame)
                    avg_diff = np.mean(diff)
                    if avg_diff > 25:
                        key_frames.append({
                            "frame": Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)),
                            "idx": frame_idx
                        })
                        prev_frame = frame
                
                next_idx = frame_idx + Config.frame_interval
                if next_idx >= total_frames:
                    break
                
                skip_count = 0
                ret_skip = False
                while frame_idx < next_idx and skip_count < Config.frame_interval:
                    ret_skip, _ = cap.read()
                    if not ret_skip:                        
                        self.logger.info(f"跳帧失败，当前索引: {frame_idx},{video_path}")
                        break
                    frame_idx += 1
                    skip_count += 1
                if not ret_skip:
                    duration = round(frame_idx/fps, 3)           
                    break
        
        finally:
            cap.release()
        
        return key_frames, duration, fps

    def _extract_frame_vector(self, image: Image.Image) -> object:
        """提取图像向量并使用CUDA加速"""
        # 预处理图像并移至GPU
        inputs = self.retrieval_processor(images=image, return_tensors="pt").to(self.retrieval_model.device)
        
        # 提取图像特征（使用CUDA加速）
        with torch.no_grad():  # 禁用梯度计算，节省内存和计算时间
            outputs = self.retrieval_model.vision_model(** inputs)
        
        # 处理特征向量
        image_embeds = outputs.last_hidden_state[:, 0, :]
        image_embeds = image_embeds / image_embeds.norm(dim=-1, keepdim=True)
        # 移回CPU并转换为numpy数组
        return image_embeds.cpu().numpy().squeeze()

    def _extract_frame_desc(self, frame: Image.Image) -> tuple:
        """生成图像描述并使用CUDA加速"""
        # 预处理图像并移至GPU
        inputs = self.generate_processor(images=frame, return_tensors="pt").to(self.device)
        
        # 生成描述（使用CUDA加速）
        with torch.no_grad():
            out = self.generate_model.generate(**inputs, max_new_tokens=30)
        
        description = self.generate_processor.decode(out[0], skip_special_tokens=True)
        
        # 中英文混合处理
        description = " ".join(
            word for word in jieba.cut(description) 
            if word not in Config.stop_words and len(word) > 1
        )
        
        return description 

    def process_video(self, video_path: str):
        # 保持不变，内部调用的方法已实现CUDA加速
        video_relative_path = os.path.relpath(video_path, Config.asset_root_dir)
        video_id = generate_file_hash(video_path)
        keyframes, video_duration, video_fps = self._extract_frames(video_path)
        video_media_type = detect_media_type(video_path)
        
        frame_index = []        
        last_visual_embedding = []
        
        for key_frame in keyframes:
            idx = key_frame["idx"]
            frame = key_frame["frame"]
            
            visual_embedding = self._extract_frame_vector(frame)
                                    
            if len(last_visual_embedding) == 0:
                visual_description = self._extract_frame_desc(frame)
                product_type = self._detect_product_type(visual_description)     
                
                frame_index.append({
                    "idx": idx,
                    "visual_description": visual_description,
                    "product_type": product_type,
                    "visual_embedding": visual_embedding,
                    "clip_start": round(idx / video_fps, 3)
                })
            else:
                vec1 = np.array(last_visual_embedding)
                vec2 = np.array(visual_embedding)

                vec1_2d = vec1.reshape(1, -1)
                vec2_2d = vec2.reshape(1, -1)

                similarity = 1 - cosine_similarity(vec1_2d, vec2_2d)[0][0]
                
                if similarity > 0.15:
                    visual_description = self._extract_frame_desc(frame)
                    product_type = self._detect_product_type(visual_description)
                    frame_index.append({
                        "idx": idx,
                        "visual_description": visual_description,
                        "product_type": product_type,
                        "visual_embedding": visual_embedding,
                        "clip_start": round(idx / video_fps, 3)
                    })
           
            last_visual_embedding = visual_embedding       
                 
        # 计算clip的长度
        last_clip_start = video_duration    
        for item in frame_index[::-1]:  
            clip_duration = max(0, round(last_clip_start - item["clip_start"], 3))
            if clip_duration > 0:                
                item["clip_duration"] = clip_duration
            last_clip_start = item["clip_start"]
            
        ids = []
        embeddings = []
        meta_datas = []
        documents = []
        
        for item in frame_index:
            idx = item["idx"]
            ids.append(f"{video_id}_{idx}")
            embeddings.append(item["visual_embedding"].tolist())
            meta_datas.append({
                "video_id": video_id,
                "frame_idx": item["idx"],
                "description": item["visual_description"],
                "product_type": item["product_type"],
                "media_type": video_media_type,
                "clip_duration": item["clip_duration"],
                "video_duration": video_duration,
                "clip_start": item["clip_start"],
                "video_path": video_relative_path,
                "upload_time": datetime.now().isoformat(),
            })
            documents.append(item["visual_description"])
            
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=meta_datas,
            documents=documents
        ) 
        
        json_path = Path(video_path).with_suffix('.json')        
        save_json(meta_datas, json_path)
   
    def _extract_text_vector(self, text: str) -> list:
        """提取文本向量并使用CUDA加速"""
        # 预处理文本并移至GPU
        inputs = self.retrieval_processor(text=text, return_tensors="pt").to(self.retrieval_model.device)
        
        # 提取文本特征（使用CUDA加速）
        with torch.no_grad():
            outputs = self.retrieval_model.text_encoder(**inputs)
        
        # 处理特征向量
        text_embeds = outputs.last_hidden_state[:, 0, :]
        text_embeds = text_embeds / text_embeds.norm(dim=-1, keepdim=True)
        # 移回CPU并转换为numpy数组
        return text_embeds.cpu().numpy().squeeze()
    
    def _detect_product_type(self, text: str) -> str:
        # 保持不变
        categories = Config.product_categories
        for cate, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return cate
        return "其他"

    def search(self, query: str, product_type: str = "", top_k: int = 30) -> list:
        # 保持不变，内部调用的方法已实现CUDA加速
        query = self._clean_query(query)
        text_feat = self._extract_text_vector(text=query)   
      
        meta_where = {"product_type": {"$eq": product_type}} if product_type else None
        
        results = self.collection.query(
            query_embeddings=[text_feat.tolist()],  # 修复：转换为list格式
            n_results=top_k,
            where=meta_where
        )
        
        texts = [item for item in results["documents"][0]]
        texts_embeddings = [self._extract_text_vector(text) for text in texts]
        query_embedings = [self._extract_text_vector(query)]
        
        scores = [1 - cosine_similarity([text], query_embedings)[0][0] for text in texts_embeddings]
            
        return sorted(
            [
                {
                    "video_id": results["ids"][0][i],
                    "score": (results["distances"][0][i] + scores[i])/2,
                    "description": results["documents"][0][i],
                    "video_path": results["metadatas"][0][i]["video_path"],
                    "clip_duration": results["metadatas"][0][i]["clip_duration"],
                    "clip_start": results["metadatas"][0][i]["clip_start"]
                } for i in range(len(results["ids"][0])) 
                if results["distances"][0][i] < 1
            ],
            key=lambda x: x["score"]
        )

    def _clean_query(self, text: str) -> str:
        # 保持不变
        return " ".join(
            word for word in jieba.cut(text) 
            if word.strip() and word not in Config.stop_words
        )

    def init_db_index(self, video_dir: str):
        # 保持不变
        media_file_paths = []   
        progress_file_path = os.path.join(video_dir, "progress.txt")
        
        for current_dir, _, filenames in os.walk(video_dir):
            for filename in filenames:
                if filename.lower().endswith((".mp4", ".mov")):
                    full_path = Path(current_dir) / filename 
                    media_file_paths.append("/".join(full_path.parts))
                        
        handled_files = load_text(progress_file_path)
        media_file_paths = list(set(media_file_paths) - set(handled_files)) 
        
        random.shuffle(media_file_paths)
        
        from tqdm import tqdm 
        pbar = tqdm(total=len(media_file_paths), desc="处理中") 
        for file_path in media_file_paths:        
            self.process_video(file_path)
            append_text(file_path, progress_file_path)
            pbar.update(1)    
        pbar.close()   

if __name__ == "__main__":
    analyzer = VideoIndexDB()
    analyzer.init_db_index(video_dir="assets_database/eshop_videos") 
    
    querytext = "一家三口站在高铁站出口，孩子牵着宠物狗，父母微笑着看向镜头"
    results = analyzer.search(query=querytext)
    
    print(f"检索结果: '{querytext}'")