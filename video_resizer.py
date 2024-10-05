# coding:utf-8

import cv2
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

def resize_video(video_clip, width, height):
    # 调整视频尺寸
    resized_clip = video_clip.resize(newsize=(width, height))
    return resized_clip

def process_video(video_clip, output_path, width, height):
    resized_video = resize_video(video_clip, width, height)
    if resized_video:
        resized_video.write_videofile(f"{output_path}.mp4", codec="libx264")

'''
python video_resizer.py -i .\原神风景视频（去水印）拣选后_少量文件 -w 640 -ht 480
'''

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resize videos in a directory to specified dimensions.")
    parser.add_argument("-i", "--input", default="video", help="Path to the input video file or directory containing videos. Default is 'video'.")
    parser.add_argument("-o", "--output", default=None, help="Path to the output directory. If not provided, it will be generated as input_path + '_resized'.")
    parser.add_argument("-w", "--width", type=int, required=True, help="Target width for the resized video.")
    parser.add_argument("-ht", "--height", type=int, required=True, help="Target height for the resized video.")
    args = parser.parse_args()

    input_path = args.input
    output_dir = args.output
    width = args.width
    height = args.height

    # 如果未提供 output_dir，则根据 input_path 生成
    if output_dir is None:
        if os.path.isfile(input_path):
            output_dir = os.path.splitext(input_path)[0] + "_resized"
        elif os.path.isdir(input_path):
            output_dir = input_path + "_resized"
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
        process_video(video_clip, output_video_path, width, height)
        print(f"Successfully processed {video_name}")
