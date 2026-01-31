import os 
from pathlib import Path
import random 
from pydub import AudioSegment  
import chromadb
from chromadb.config import Settings
import torch  
import torchaudio 
from transformers import ClapModel, ClapProcessor

from .config import Config
from .tools import append_text, generate_file_hash, load_text,get_audio_duration 
 

class AudioIndexDB:
    def __init__(self): 

        self.clap_model = ClapModel.from_pretrained(
            Config.clap_model ,# "laion/clap-htsat-unfused", 
            cache_dir=Config.cache_dir,
            dtype=torch.float32,  # 显式使用半精度
            use_safetensors=True
        ).to(Config.DEVICE)
        
               
        self.clap_processor = ClapProcessor.from_pretrained(
            Config.clap_model ,# "laion/clap-htsat-unfused",
            cache_dir=Config.cache_dir,
            use_safetensors=True
        ) 
        
        # 初始化数据库       
        self.client = chromadb.PersistentClient(
            path= Config.audio_chroma_dir,            
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="audio_assets", 
            metadata={"hnsw:space": "cosine"}
        )
     
  
    def _extract_audio_features(self, audio_path):
        """
        抽取音频特征，统一使用float32类型
        1. 截取音频前10秒
        2. 转换为wav格式
        3. 提取音频特征
        
        参数:
            audio_path: 输入音频文件路径(支持多种格式)
        返回:
            audio_embedding: 音频特征向量(torch.Tensor)
        """
        temp_path = None
        try:
            # 1. 加载音频并截取前10秒
            audio = AudioSegment.from_file(audio_path)
            ten_seconds = 10 * 1000  # pydub使用毫秒
            audio = audio[:ten_seconds]  # 截取前10秒
            
            # 2. 转换为wav格式并保存临时文件
            original_path = Path(audio_path)
            temp_path = os.path.join(original_path.parent,original_path.stem+".temp") 
           
            audio.export(temp_path, format="wav")
            
            # 3. 加载音频波形数据并强制转换为float32
            waveform, sr = torchaudio.load(temp_path)
            waveform = waveform.to(torch.float32)  # 立即转换为float32
            
            # 4. 统一处理为单声道
            waveform = waveform.mean(dim=0, keepdim=True)  # 转为单声道
            
            # 5. 处理采样率(CLAP模型需要48000Hz)
            if sr != 48000:
                waveform = torchaudio.functional.resample(
                    waveform, 
                    orig_freq=sr, 
                    new_freq=48000
                ).to(torch.float32)  # 确保重采样后仍然是float32
            
            # 6. 确保音频长度为10秒(48000Hz * 10秒)
            target_samples = 48000 * 10
            if waveform.size(1) != target_samples:
                # 如果不足10秒则填充，超过10秒则截取
                padding = torch.zeros(
                    1, 
                    target_samples - waveform.size(1), 
                    dtype=torch.float32,
                    device=waveform.device
                )
                waveform = torch.cat([waveform, padding], dim=1)
                waveform = waveform[:, :target_samples]  # 双重保险
            
            # 7. 使用CLAP处理器提取特征
            audio_input = self.clap_processor(
                audios=waveform.numpy(),
                return_tensors="pt",
                sampling_rate=48000
            )
            
            # 8. 确保所有输入都是float32并发送到设备
            audio_input = {
                k: v.to(Config.DEVICE).to(torch.float32) if torch.is_tensor(v) else v
                for k, v in audio_input.items()
            }
            
            # 9. 禁用混合精度以确保使用float32
            with torch.amp.autocast('cuda',enabled=False):
                audio_embedding = self.clap_model.get_audio_features(**audio_input)
            
            return audio_embedding.squeeze(0).to(torch.float32)  # 最终确保输出是float32
            
        except Exception as e:
            raise RuntimeError(f"处理音频 {audio_path} 失败: {str(e)}")
            
        finally:
            # 确保临时文件被清理
            if temp_path is not None and os.path.exists(temp_path):
                os.remove(temp_path)
 
    def _text_to_audio_embedding(self, text):
        # 文本向量化
        text_input = self.clap_processor(
            text=text,
            return_tensors="pt"
        )

        # 正确处理文本输入：input_ids保持整数类型，attention_mask可以转为float32
        text_input = {
            "input_ids": text_input["input_ids"].to(Config.DEVICE),  # 保持默认的long/int类型
            "attention_mask": text_input["attention_mask"].to(Config.DEVICE).to(torch.float32)  # attention_mask转为float32
        }

        # 确保模型输出float32
        with torch.amp.autocast('cuda',enabled=False):  # 禁用自动混合精度
            text_embedding = self.clap_model.get_text_features(**text_input)
        
        # 确保返回一维张量
        if text_embedding.dim() > 1:
            text_embedding = text_embedding.squeeze(0)  # 去除多余的批次维度
        
        return text_embedding
     
    
    def process_audio(self, audio_path):
        """处理单个音频文件，提取每个场景的特征""" 
        audio_relative_path = os.path.relpath(audio_path, Config.asset_root_dir) 
        # 提取音频特征
        audio_duration = get_audio_duration(audio_path)
        audio_id = generate_file_hash(audio_path)
        audio_features = self._extract_audio_features(audio_path) 
      
        item = {
            "vocal_text": "",#vocal_text,
            "audio_idx": audio_id,
            "features": audio_features.tolist(),
            "clip_start": 0,
            "clip_duration":audio_duration,
            "audio_path": audio_relative_path
        } 
        
       
        
        # 存入数据库
        self.collection.add(
            ids=[item["audio_idx"] ],
            embeddings=[item["features"] ],
            metadatas=[{
                "clip_start": item["clip_start"],             
                "clip_duration": item["clip_duration"],
                "audio_path": item["audio_path"]
            }  ],
            documents=[item["vocal_text"] ]
        )
       
            
    

    def init_db_index(self, audio_dir: str):
        """构建音频特征索引数据库"""
        media_file_paths = []   
        progress_file_path = os.path.join(audio_dir, "progress.txt")
        
        # 递归遍历目录
        for current_dir, _, filenames in os.walk(audio_dir):
            for filename in filenames:
                if filename.lower().endswith((".mp3", ".wav", ".wma")):
                    full_path = Path(current_dir) / filename 
                    media_file_paths.append("/".join(full_path.parts))
                        
        # 批量处理音频（去重已处理文件）
        handled_files = load_text(progress_file_path)
        media_file_paths = list(set(media_file_paths) - set(handled_files)) 
        random.shuffle(media_file_paths)
        
        from tqdm import tqdm 
        pbar = tqdm(total=len(media_file_paths), desc="处理中") 
        for file_path in media_file_paths:        
            try:
                self.process_audio(file_path)
                append_text(file_path, progress_file_path)
            except Exception as e:
                print(f"处理文件失败 {file_path}: {e}")
            pbar.update(1)    
        pbar.close()   
    
    def search(self, text_query, top_k=5):
        """用文本描述检索相似音频场景（精简版，仅使用音频特征）"""
        # 将文本转换为音频特征嵌入（CLAP）
        query_embedding = self._text_to_audio_embedding(text_query)
        
        # 直接查询音频特征数据库
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],  # 确保转换为list
            n_results=top_k
        )
        
        # 获取实际返回的结果数量
        actual_results_count = len(results["ids"][0]) if results["ids"] and results["ids"][0] else 0
        
        if actual_results_count == 0:
            return []
        
        if actual_results_count > top_k:
            actual_results_count = top_k

        # 格式化结果，使用实际返回的结果数量，避免索引越界
        return [{
            "audio_id": results["ids"][0][i],
            "audio_path": results["metadatas"][0][i]["audio_path"],
            "clip_start": results["metadatas"][0][i]["clip_start"],          
            "clip_duration": results["metadatas"][0][i]["clip_duration"],
            "score": results["distances"][0][i],  # 直接使用音频特征距离
            "query_text": text_query
        } for i in range(actual_results_count)]
        
        
        
# 使用示例
if __name__ == "__main__":
    indexer = AudioIndexDB(root_dir=".work_space/default")
    
    audio_dir = "./.asset_space/audios/bgm"
    # 首次运行需构建索引
    indexer.init_db_index(audio_dir=audio_dir)
    
    # 文本检索示例
    text_query = "欢快的背景音乐带有鼓点"
    matches = indexer.search(text_query)
    
    print(f"检索结果: '{text_query}'")
  
    