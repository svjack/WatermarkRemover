# coding:utf-8

import cv2
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
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

def loop_video(video_clip, loop_duration):
    total_duration = video_clip.duration
    loop_count = int(loop_duration / total_duration)
    remaining_duration = loop_duration % total_duration

    # 创建循环片段
    looped_clips = [video_clip] * loop_count
    if remaining_duration > 0:
        looped_clips.append(video_clip.subclip(0, remaining_duration))

    # 连接所有片段
    final_clip = concatenate_videoclips(looped_clips)
    return final_clip

def process_video(video_clip, output_path, loop_duration):
    looped_video = loop_video(video_clip, loop_duration)
    try:
        looped_video.write_videofile(f"{output_path}.mp4", codec="libx264")
    except:
        print("clipped_video write error")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Loop a video for a specified duration.")
    parser.add_argument("-i", "--input", default="video", help="Path to the input video file or directory containing videos. Default is 'video'.")
    parser.add_argument("-o", "--output", default=None, help="Path to the output directory. If not provided, it will be generated as input_path + '_rec'.")
    parser.add_argument("-s", "--seconds", type=float, default=None, help="Duration in seconds to loop the video. If not provided, the entire video will be processed.")
    args = parser.parse_args()

    input_path = args.input
    output_dir = args.output
    loop_duration = args.seconds

    # 如果未提供 output_dir，则根据 input_path 生成
    if output_dir is None:
        if os.path.isfile(input_path):
            output_dir = os.path.splitext(input_path)[0] + "_rec"
        elif os.path.isdir(input_path):
            output_dir = input_path + "_rec"
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

    for video in videos:
        video_clip = VideoFileClip(os.path.join(input_path, video))
        video_name = os.path.basename(video)
        output_video_path = os.path.join(output_dir, os.path.splitext(video_name)[0])
        process_video(video_clip, output_video_path, loop_duration)
        print(f"Successfully looped {video_name}")
