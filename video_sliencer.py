# coding:utf-8

import os
from moviepy.editor import VideoFileClip
import argparse
from tqdm import tqdm

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            print(f"Created directory: {directory}")
        except OSError as error:
            print(f"Error creating directory {directory}: {error}")
            raise

def is_valid_video_file(file):
    try:
        with VideoFileClip(file) as video_clip:
            return True
    except Exception as e:
        print(f"Invalid video file: {file}, Error: {e}")
        return False

def remove_audio_from_video(video_clip):
    return video_clip.without_audio()

def process_video(video_clip, output_path):
    video_without_audio = remove_audio_from_video(video_clip)
    try:
        video_without_audio.write_videofile(f"{output_path}.mp4", codec="libx264")
    except:
        print("Error writing video without audio")

'''
python video_sliencer.py -i .\原神风景视频（去水印）拣选后_单个文件夹_改变到2560x1080_skip_resized_裁剪_到人物_2560_温蒂
python video_sliencer.py -i .\原神风景视频（去水印）拣选后_单个文件夹_改变到2560x1080_skip_resized_裁剪_到人物_2560
'''

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove audio from a video and save it to a new path.")
    parser.add_argument("-i", "--input", default="video", help="Path to the input video file or directory containing videos. Default is 'video'.")
    parser.add_argument("-o", "--output", default=None, help="Path to the output directory. If not provided, it will be generated as input_path + '_no_audio'.")
    args = parser.parse_args()

    input_path = args.input
    output_dir = args.output

    # 如果未提供 output_dir，则根据 input_path 生成
    if output_dir is None:
        if os.path.isfile(input_path):
            output_dir = os.path.splitext(input_path)[0] + "_no_audio"
        elif os.path.isdir(input_path):
            output_dir = input_path + "_no_audio"
        else:
            print(f"Invalid input path: {input_path}")
            exit(1)

    ensure_directory_exists(output_dir)

    if os.path.isfile(input_path):
        videos = [input_path] if is_valid_video_file(input_path) else []
    elif os.path.isdir(input_path):
        videos = [f for f in os.listdir(input_path) if is_valid_video_file(os.path.join(input_path, f))]
    else:
        print(f"Invalid input path: {input_path}")
        exit(1)

    for video in tqdm(videos, desc="Processing videos"):
        video_clip = VideoFileClip(os.path.join(input_path, video))
        video_name = os.path.basename(video)
        output_video_path = os.path.join(output_dir, os.path.splitext(video_name)[0])
        process_video(video_clip, output_video_path)
        print(f"Successfully processed {video_name}")
