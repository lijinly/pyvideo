# run_wav2lip.py
from pathlib import Path
import sys
import os
from Wav2Lip import inference

# Add the Wav2Lip directory to the Python path
# sys.path.append('/home/laoli/videocut/Wav2Lip')
# checkpoint_path = os.path.join('Wav2Lip','checkpoints','wav2lip.pth')

def synic_video(face_path, audio_path,  out_file,avatar_path, **kwargs):
    """
    Run Wav2Lip inference directly from Python code
    
    Args:
        face_path (str): Path to face video/image
        audio_path (str): Path to audio file
        checkpoint_path (str): Path to model checkpoint
        outfile (str): Path to save output video
        **kwargs: Additional arguments (pads, resize_factor, etc.)
    """
    # Import the inference module
    # import inference
    
    # Set up arguments
    inference.args.face = face_path
    inference.args.audio = audio_path
    inference.args.checkpoint_path = avatar_path
    inference.args.outfile = out_file
    if os.path.isfile(face_path) and Path(face_path).suffix in ['jpg', 'png', 'jpeg']:
        inference.args.static = True
    
    # Handle additional arguments
    if 'fps' in kwargs:
        inference.args.fps = kwargs['fps']
    if 'pads' in kwargs:
        inference.args.pads = kwargs['pads']
    if 'face_det_batch_size' in kwargs:
        inference.args.face_det_batch_size = kwargs['face_det_batch_size']
    if 'wav2lip_batch_size' in kwargs:
        inference.args.wav2lip_batch_size = kwargs['wav2lip_batch_size']
    if 'resize_factor' in kwargs:
        inference.args.resize_factor = kwargs['resize_factor']
    if 'crop' in kwargs:
        inference.args.crop = kwargs['crop']
    if 'box' in kwargs:
        inference.args.box = kwargs['box']
    if 'rotate' in kwargs:
        inference.args.rotate = kwargs['rotate']
    if 'nosmooth' in kwargs:
        inference.args.nosmooth = kwargs['nosmooth']
    
    # Run main function
    inference.main()

