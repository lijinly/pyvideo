import re 
import dashscope
from dashscope import Generation
import json
import os

from .config import Config 
    
def load_json(input_path:str)->object:
    """
    加载JSON文件
    """
   
    if not os.path.exists(input_path):
        print(f"文件不存在：{input_path}")
        return None
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)  
            
def save_json(objdata, output_path: str):
    """
    保存json文件
    """
    with open(output_path, 'w',encoding="utf-8") as f:
        json.dump(objdata, f,ensure_ascii=False, indent=2)
        
def parse_json( text: str) -> object:
    """
    从一段文本中提取json文本，并转化为json对象
    """
 
    # 删除JSON外的多余字符
    # cleaned = re.sub(r'[^\{\}\[\],:"\d\w\s]', '', text)
    matches = re.findall(r'(\{.*?\}|\[.*?\])', text, re.DOTALL)
    
    objs = []
    
    for match in matches:
        try:               
            json_obj = json.loads(match) 
            print(json_obj)   
            objs.append(json_obj)
            
        except json.JSONDecodeError:
            continue

    return objs

def save_text(text:str,path:str)->None:
    """
    utf-8 格式保存文本文件
    """
    with open(path, "w", encoding="utf-8") as file:
            file.write(text) 
            
def append_text(text:str,path:str):
    """向文件追加一行内容"""
    with open(path, 'a', encoding='utf-8') as f:
        # 写入内容 + 换行符（确保每行独立）
        f.write(text + '\n')   
def load_text(file_path:str)->list[str]:
    """
    加载为一个列表
    """
    # 1. 提取文件所在的目录路径（而不是文件路径）
    dir_path = os.path.dirname(file_path)  # 例如：./assets_database/eshop_videos
    
    # 2. 确保目录存在（创建目录，而非文件）
    os.makedirs(dir_path, exist_ok=True)  # 这里用目录路径，而非文件路径
    
    # 3. 检查文件是否存在，不存在则创建空文件（避免读取时出错）
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            pass  # 创建空文件
    
    # 4. 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        lines = [line.strip() for line in lines]
    return lines
            
# def parse_xml(text:str)->str: 
#     # text = '```xml\n<speak>...</speak>\n```'  # 原始文本

#     # 非贪婪匹配<speak>内部所有内容
#     pattern = r"<speak>(.*?)</speak>"
#     match = re.search(pattern, text, re.DOTALL)

#     if match:
#         result = f"<speak>{match.group(1)}</speak>"
#         return result
#     else:
#         print("未匹配到内容") 
    
def save_image(img:object,path:str)->None:
    """
    保存图片
    """
    with open(path, 'wb+') as f:
        f.write(img)
####################################################################

import os 

def detect_media_type(file_path: str) -> str:
    """
    根据文件后缀名推断多媒体资源类型
    :param file_path: 文件路径
    :return: 'audio', 'video', 'image', 'other'
    """
    # 获取小写格式的文件扩展名（含点号）
    ext = os.path.splitext(file_path)[1].lower()
    
    # 多媒体类型扩展名分类字典
    media_types = {
        'audio': {'.mp3', '.wav', '.aac', '.wma', '.flac', '.ogg', '.m4a'},
        'video': {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.mpeg', '.webm'},
        'image': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'}
    }
    
    # 匹配扩展名所属类型
    for media_type, extensions in media_types.items():
        if ext in extensions:
            return media_type
    
    return 'other'
###################################################################

            
def chat(prompt:str)->str:
    """
    基于阿里云qwen-max-latest的通用对话功能
    """
    
    dashscope.api_key = Config.dashscope_api_key 
        
    # 调用通义千问3模型并启用联网检索功能
    response = Generation.call(
        model="qwen-max-latest",
        prompt=prompt,
        temperature=0.8,  #美妆文案需要更多创意，调高温度值
        top_p=0.85,
        max_length=3072,
        enable_internet=True  # 启用联网检索功能
    )

    # 检查响应状态
    if response.status_code == 200:
        return response.output.text           
    else:
        raise Exception( f"API调用失败，状态码: {response.status_code}，错误信息: {response.message}")
    
####################################################################################################
import re
def extract_main_description(text):
    """提起主体描述的内容"""
    pattern = re.compile(r'主体描述\s*：(.*?)(?=--|\n|$)')
    match = pattern.search(text)

    if match:
        result = match.group(1).strip()  
        return result
    else:
        return ""
 

##########################################################################################
# import jieba
# import nltk

# # 将缓存路径添加到NLTK的数据路径列表中（优先查找）
# nltk.data.path.insert(0, Config.nltk_cache_dir) 
# jieba.dt.tmp_dir = Config.jieba_cache_dir 
# jieba.initialize() 

# def extract_segments_zh_en(text):
#     """提取文本中的中英文片段"""
#     # 中文分词（保留词语）
#     chinese_words = [word for word in jieba.lcut(text) if '\u4e00' <= word <= '\u9fff']
#     # 英文分词（保留完整单词）
#     english_words = nltk.word_tokenize(''.join(re.findall(r'[a-zA-Z\s,.!?]+', text)))
#     return chinese_words, english_words,[*chinese_words,*english_words]


###########################################################################################


def split_with_quotes(text):
    """
    把一段文本按阅读停顿划分为行，同时消除句中所有标点（用空格替代）
    
    处理逻辑：
    1. 先按句末标点断句
    2. 每一句中的标点用空格代替（忽略引号内的句末标点）
    3. 合并空格
    """
    # 步骤1：按句末标点分割（忽略引号内的句末标点）
    split_pattern = r'(?<!["\'])(?<=[。！？.!?])(?!["\'])'
    sentences = re.split(split_pattern, text)
    
    # 步骤2：对每个句子，将标点替换为空格（保留引号内的内容）
    processed_sentences = []
    for sentence in sentences:
        # 替换所有标点为空格（除了引号和空格）
        punctuation_pattern = r'[^\w\s]'
        sentence_with_spaces = re.sub(punctuation_pattern, ' ', sentence)
        # 合并多个空格为单个空格并去除首尾空格
        merged_sentence = re.sub(r'\s+', ' ', sentence_with_spaces).strip()
        if merged_sentence:  # 只保留非空句子
            processed_sentences.append(merged_sentence)
    
    # 步骤3：过滤空字符串
    return [sentence for sentence in processed_sentences if sentence]

##########################################################################################
def process_phone_numbers(text):
    """
    处理文本中的电话号码，将其中的-替换为空格，并保持在原位置
    
    参数:
        text: 包含电话号码的原始文本
        
    返回:
        处理后的文本，其中电话号码中的-已被替换为空格
    """
    # 定义匹配电话号码的正则表达式模式
    # 匹配常见的电话号码格式，如：123-456-7890, (123)456-7890, 1234567890等
    pattern = r'(\d{3}[-\s]?\d{3}[-\s]?\d{4}|\(\d{3}\)\s?\d{3}[-\s]?\d{4})'
    
    def replace_dash(match):
        """替换匹配到的电话号码中的短横线为空格"""
        phone_number = match.group(0)
        # 将所有短横线替换为空格
        return phone_number.replace('-', ' ')
    
    # 使用sub方法替换文本中的电话号码
    processed_text = re.sub(pattern, replace_dash, text)
    return processed_text
###########################################################################################

import hashlib

def generate_file_hash(file_path):
    """获取文件hash，防重复"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):  # 分块读取大文件
            sha256.update(chunk)
    return sha256.hexdigest()  # 64字符哈希值

 
 
############################################################################################
import cv2

def get_video_duration_fps(video_path):
    """
    计算视频文件的长度（秒）和帧率（fps）
    """
    if not os.path.exists(video_path):
        return 0,0
 
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("无法打开视频文件")
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return round( frame_count / fps  ,3),fps
#########################################################################################
from pydub import AudioSegment

def get_audio_duration(file_path):
    """返回音频文件的长度"""
    audio = AudioSegment.from_file(file_path)
    return round(len(audio) / 1000.0,3)  # 毫秒转秒
##########################################################################################

import cv2
import numpy as np
import os

def save_last_frame(video_path, output_path):
    """
    截取视频最后一帧，并保存到中文路径
    
    参数:
        video_path (str): 视频文件路径（可含中文）
        output_path (str): 输出图片路径（可含中文）
    """
    # 1. 打开视频文件
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("错误：无法打开视频文件！")
        return False
    
    # 2. 获取视频总帧数，并跳转到最后一帧
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
    
    # 3. 读取最后一帧
    ret, frame = cap.read()
    if not ret:
        print("错误：无法读取最后一帧！")
        return False
    
    # 4. 释放视频资源
    cap.release()
    
    # 5. 处理中文路径问题：使用 cv2.imencode + 二进制写入
    try:
        # 将图像编码为内存中的二进制数据
        _, buffer = cv2.imencode("."+output_path.split(".")[1], frame)
        # 以二进制模式写入文件（兼容中文路径）
        with open(output_path, 'wb') as f:
            f.write(buffer)
        print(f"成功保存最后一帧到：{output_path}")
        return True
    except Exception as e:
        print(f"保存失败：{str(e)}")
        return False
    
##############################################################################################
from moviepy import VideoFileClip, concatenate_videoclips

def concatenate_and_save_videos(video_clips:list, duration, output_path:str, method="chain", fps:int=30, codec="libx264"):
    """
    连接两个视频片段并保存为新的视频文件
    
    参数:
        video_path1 (str): 第一个视频文件路径
        video_path2 (str): 第二个视频文件路径
        output_path (str): 输出视频路径 (默认为 "merged_video.mp4")
        method (str): 连接方法，"compose"或"chain" (默认为"compose")
        fps (int/None): 输出视频帧率，None表示使用第一个视频的帧率
        codec (str): 视频编码器 (默认为"libx264")
    
    返回:
        bool: 操作是否成功
    """
    try:
        # 1. 加载视频片段
        video_clips = [ VideoFileClip(item) for item in video_clips]
        
        # 2. 连接视频片段
        final_clip = concatenate_videoclips(video_clips, method=method)
        final_clip = final_clip.with_duration(duration)
        
        # 3. 设置输出帧率(如果未指定则使用第一个视频的帧率)
        output_fps = fps if fps is not None else 30
        
        # 4. 保存合并后的视频
        final_clip.write_videofile(
            output_path,
            codec=codec,
            fps=output_fps,
            threads=4  # 使用多线程加速
        )
        
        # 5. 关闭视频剪辑以释放资源
     
        final_clip.close()
        
        print(f"视频已成功合并并保存到: {output_path}")
        return True
        
    except Exception as e:
        print(f"合并视频时出错: {str(e)}")
        return False
    

##########################################################################################

from ffmpeg._probe import probe
from ffmpeg._ffmpeg import input
import numpy as np 
from math import ceil
def get_valid_frames_duration(input_path,
                                black_threshold=0.1, 
                            #    color_threshold=0.98,
                               min_consecutive=5):
    """
    检测并删除视频尾部的空帧
    
    参数:
        input_path: 输入视频路径
        output_path: 输出视频路径
        black_threshold: 黑帧亮度阈值(0-1, 默认0.1)
        min_consecutive: 最小连续空帧数(默认5帧)
    """
    # 获取视频信息
    fpprobe = probe(input_path)
    video_info = next(s for s in fpprobe['streams'] if s['codec_type'] == 'video')
    duration = float(video_info['duration'])
    fps = eval(video_info['avg_frame_rate'])
    total_frames = int(video_info['nb_frames'])
    
    print(f"原始视频: {duration:.2f}秒, {total_frames}帧, {fps:.2f}fps")   
   
    def is_solid_color_frame(frame_num, threshold=0.95, sample_size=32):
        """
        改进版的纯色帧检测函数
        
        参数:
            input_path: 视频路径
            frame_num: 帧序号
            fps: 视频帧率
            threshold: 纯色判定阈值(0-1)
            sample_size: 采样分辨率
            
        返回:
            bool: 是否为纯色帧
        """
        try:
            # 计算精确时间戳（增加微小偏移避免关键帧问题）
            timestamp = max(0, frame_num / fps - 0.001)
            
            # 使用ffmpeg抽取帧
            out, _ = (
                input(input_path, ss=timestamp)
                .filter('select', 'eq(n,{})'.format(frame_num))  # 精确选择帧
                .filter('scale', sample_size, sample_size)
                .filter('format', 'rgb24')  # 确保输出格式
                .output('pipe:', format='rawvideo', pix_fmt='rgb24', vframes=1)
                .run(capture_stdout=True, quiet=True)
            )
            
            # 处理帧数据
            frame = np.frombuffer(out, np.uint8)
            if len(frame) == 0:
                raise ValueError("获取帧数据失败")
                
            frame = frame.reshape(sample_size, sample_size, 3)
            
            # 计算颜色标准差（改进的纯色检测）
            color_std = np.std(frame, axis=(0,1))  # 计算RGB三个通道的标准差
            max_std = np.max(color_std)  # 取最大标准差
            
            # 阈值判断（更严格的纯色检测）
            return max_std < 255 * (1 - threshold)
            
        except Exception as e:
            print(f"检测帧 {frame_num} 时出错: {str(e)}")
            return False

    # 从末尾向前查找第一个非空帧
    last_valid_frame = total_frames - 1
    consecutive_blacks = 0
 
    for frame_num in range(total_frames-1, -1, -1):
        if is_solid_color_frame(frame_num):
            consecutive_blacks += 1
        else:
            break
    last_valid_frame = frame_num - consecutive_blacks   
        
    print(f"black frames:{consecutive_blacks}")
    # 计算需要保留的时长
    cut_time = last_valid_frame / fps
    
    return  cut_time 
##############################################################################################################
import pathlib

def build_user_space_dir(user_id:str="default"):
    """
    为用户创建工作空间
    """
    user_space_path = pathlib.Path( f".work_space/{user_id}")
    user_space_path.mkdir(parents=True,exist_ok=True)
    return user_space_path
    
###################################################################################################
import shutil
from pathlib import Path

def copy_file_if_not_exists(source_file, target_dir):
    """
    如果目标目录下没有该文件，则从源文件拷贝到目标目录
    
    :param source_file: 源文件路径（字符串或 Path 对象）
    :param target_dir: 目标目录路径（字符串或 Path 对象）
    """
    src = Path(source_file)
    dst_dir = Path(target_dir)

    # 检查源文件是否存在
    if not src.is_file():
        print(f"源文件不存在：{src}")
        return

    # 确保目标目录存在
    dst_dir.mkdir(parents=True, exist_ok=True)

    # 目标文件的完整路径
    dst_file = dst_dir / src.name

    # 检查目标文件是否已存在
    if dst_file.exists():
        print(f"目标文件已存在，无需拷贝：{dst_file}")
    else:
        # 执行拷贝（推荐用 copy2，保留元数据）
        shutil.copy2(src, dst_file)
        print(f"已拷贝文件到：{dst_file}")    
#########################################################################################################


# # 初始化日志系统
# # 示例：根目录为 ./logs，单个文件最大5MB，最多保留3个备份
# logger = setup_rotating_logger(
#     root_dir="./logs",
#     max_size=5*1024*1024,  # 5MB
#     backup_count=3
# )

# # 测试日志输出
# if __name__ == "__main__":
#     for i in range(10000):  # 循环输出日志，触发轮转
#         logger.info(f"这是第{i}条测试日志，用于触发文件轮转...")
##############################################################################################################    
    
if __name__ == "__main__": 
    video_path = "content_design/检索素材库生成视频_02/config_design_1/compose_video.mp4"
    output_path = "content_design/检索素材库生成视频_02/config_design_1/last_frame.jpg"
    save_last_frame(video_path, output_path=output_path)  