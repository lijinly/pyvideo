#!/usr/bin/env python3
"""
Standalone Video Face Enhancer Script
This script enhances faces in videos using GFPGAN technology with all required functionality included.
"""

import os
import cv2
import torch
import argparse
import numpy as np
from tqdm import tqdm
import imageio
from moviepy import VideoFileClip
import tempfile
import shutil
from domains.config import Config

from gfpgan  import GFPGANer

checkpoints_dir = os.path.join(Config.project_root,'gfpgan','weights')

def load_video_to_cv2(video_path):
    """
    Load video frames to a list of CV2 images.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")
    
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(frame_rgb)
    
    cap.release()
    return frames

class GeneratorWithLen(object):
    """ From https://stackoverflow.com/a/7460929 """
    def __init__(self, gen, length):
        self.gen = gen
        self.length = length

    def __len__(self):
        return self.length

    def __iter__(self):
        return self.gen

def enhancer_generator_no_len(images, method='gfpgan', bg_upsampler='realesrgan'):
    """ 
    Provide a generator function so that all of the enhanced images don't need
    to be stored in memory at the same time. This can save tons of RAM compared to
    the enhancer function.
    """
    
    print('face enhancer....')
    if not isinstance(images, list) and os.path.isfile(images):  # handle video to images
        images = load_video_to_cv2(images)




    # ------------------------ set up background upsampler ------------------------
    if bg_upsampler == 'realesrgan' and torch.cuda.is_available():
        real_model_path = os.path.join( checkpoints_dir,'RealESRGAN_x2plus.pth') 
        if not os.path.isfile(real_model_path):
            real_model_path = 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth'
        
        try:
            from basicsr.archs.rrdbnet_arch import RRDBNet
            from realesrgan import RealESRGANer
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)
            bg_upsampler = RealESRGANer(
                scale=2,
                model=model,
                model_path = real_model_path ,
                tile=400,
                tile_pad=10,
                pre_pad=0,
                half=True)  # need to set False in CPU mode
        except ImportError:
            print("Warning: RealESRGAN is not available. Using no background upsampler.")
            bg_upsampler = None
 
    # ------------------------ set up GFPGAN restorer ------------------------
    if method == 'gfpgan':
        arch = 'clean'
        channel_multiplier = 2
        model_name = 'GFPGANv1.4'
        model_path =os.path.join( checkpoints_dir,'GFPGANv1.4.pth')
        url = 'https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth'
    elif method == 'RestoreFormer':
        arch = 'RestoreFormer'
        channel_multiplier = 2
        model_name = 'RestoreFormer'
        model_path = os.path.join( checkpoints_dir,'RestoreFormer.pth') 
        url = 'https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/RestoreFormer.pth'
    elif method == 'codeformer':
        arch = 'CodeFormer'
        channel_multiplier = 2
        model_name = 'CodeFormer'
        model_path = os.path.join( checkpoints_dir,'codeformer.pth')
        url = 'https://github.com/sczhou/CodeFormer/releases/download/v0.1.0/codeformer.pth'
    else:
        raise ValueError(f'Wrong model version {method}.')
    
    if not os.path.isfile(model_path):
        model_path = url
    
    restorer = GFPGANer(
        model_path=model_path,
        upscale=2,
        arch=arch,
        channel_multiplier=channel_multiplier,
        bg_upsampler=bg_upsampler)
       
    # ------------------------ restore ------------------------
    for idx in tqdm(range(len(images)), 'Face Enhancer:'):
        img = cv2.cvtColor(images[idx], cv2.COLOR_RGB2BGR)
        
        # restore faces and background if necessary
        cropped_faces, restored_faces, r_img = restorer.enhance(
            img,
            has_aligned=False,
            only_center_face=False,
            paste_back=True)
        
        r_img = cv2.cvtColor(r_img, cv2.COLOR_BGR2RGB)
        yield r_img

def enhancer_generator_with_len(images, method='gfpgan', bg_upsampler='realesrgan'):
    """ 
    Provide a generator with a __len__ method so that it can passed to functions that
    call len()
    """
    
    if os.path.isfile(images):  # handle video to images
        # TODO: Create a generator version of load_video_to_cv2
        images = load_video_to_cv2(images)

    gen = enhancer_generator_no_len(images, method=method, bg_upsampler=bg_upsampler)
    gen_with_len = GeneratorWithLen(gen, len(images))
    return gen_with_len

# Replace the enhance_video_faces function with this updated version:
def enhance_video(input_video_path, output_video_path, method='gfpgan', bg_upsampler='realesrgan'):
    """
    Enhance faces in a video using the specified method.
    
    Parameters:
    - input_video_path (str): Path to the input video file
    - output_video_path (str): Path where the enhanced video will be saved
    - method (str): Face enhancement method ('gfpgan', 'RestoreFormer', or 'codeformer')
    - bg_upsampler (str): Background upscaler method ('realesrgan' or None)
    """
    
    # Check if input video exists
    if not os.path.exists(input_video_path):
        raise FileNotFoundError(f"Input video not found: {input_video_path}")
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_video_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"Enhancing video: {input_video_path}")
    print(f"Using method: {method}")
    
    # Generate enhanced frames
    try:
        enhanced_frames = enhancer_generator_with_len(
            input_video_path, 
            method=method, 
            bg_upsampler=bg_upsampler
        )
        
        # Read original video to get properties
        cap = cv2.VideoCapture(input_video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        
        # Create a temporary file for the video without audio
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_video:
            temp_video_path = tmp_video.name
            
        # Write enhanced video (without audio)
        print(f"Saving enhanced video (without audio) to temporary file")
        writer = imageio.get_writer(
            temp_video_path, 
            format='FFMPEG', 
            fps=fps, 
            codec='libx264',
            quality=5,
            pixelformat='yuv420p'
        )
        
        try:
            for frame in enhanced_frames:
                writer.append_data(frame)
        finally:
            writer.close()
        
        # Now add the audio track from the original video
        print("Adding audio track to enhanced video")
        original_clip = VideoFileClip(input_video_path)
        enhanced_clip = VideoFileClip(temp_video_path)
        final_clip = enhanced_clip.with_audio(original_clip.audio)
        mp4_tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') 
        final_clip.write_videofile(output_video_path,
                                       codec='libx264',
                                       audio_codec='aac',
                                       temp_audiofile=mp4_tmp_file.name)
        if os.path.exists(mp4_tmp_file.name):
            os.unlink(mp4_tmp_file.name)
        
        # Clean up temporary file
        os.unlink(temp_video_path)
        original_clip.close()
        enhanced_clip.close()
        final_clip.close()
        
        print(f"Enhanced video saved successfully: {output_video_path}")
        
    except Exception as e:
        print(f"Error during face enhancement: {str(e)}")
        raise

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Enhance faces in videos")
    parser.add_argument("--input", "-i",
                        default="./.work_space/outputs/jiaojiao06_kim.mp4", 
                        help="Input video path")
    parser.add_argument("--output", "-o",
                        default="./.work_space/outputs/jiaojiao06_kim_enhanced.mp4", 
                        help="Output video path")
    parser.add_argument("--method", "-m", 
                        default="gfpgan", 
                        choices=["gfpgan", "RestoreFormer", "codeformer"],
                        help="Face enhancement method")
    parser.add_argument("--bg_upsampler", "-bg", default="realesrgan",
                        choices=["realesrgan", "none"],
                        help="Background upscaler")
    
    args = parser.parse_args()
    
    enhance_video(
        args.input,
        args.output,
        method=args.method,
        bg_upsampler=args.bg_upsampler if args.bg_upsampler != "none" else None
    )