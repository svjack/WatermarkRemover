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

def skip_and_limit_video(video_clip, skip_start, skip_end, max_duration):
    total_duration = video_clip.duration

    # 检查跳过的秒数是否比视频长度长
    if skip_start + skip_end >= total_duration:
        print(f"Skipping duration ({skip_start}s + {skip_end}s) is longer than or equal to video duration ({total_duration}s). Skipping entire video.")
        return None

    # 先进行尾部跳过
    end_time = total_duration - skip_end
    skipped_clip = video_clip.subclip(skip_start, end_time)

    # 再限制最长长度
    if skipped_clip.duration > max_duration:
        skipped_clip = skipped_clip.subclip(0, max_duration)

    return skipped_clip

def process_video(video_clip, output_path, skip_start, skip_end, max_duration):
    skipped_video = skip_and_limit_video(video_clip, skip_start, skip_end, max_duration)
    if skipped_video:
        skipped_video.write_videofile(f"{output_path}.mp4", codec="libx264")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Skip the start and end of a video for specified durations and limit the maximum duration.")
    parser.add_argument("-i", "--input", default="video", help="Path to the input video file or directory containing videos. Default is 'video'.")
    parser.add_argument("-o", "--output", default=None, help="Path to the output directory. If not provided, it will be generated as input_path + '_skip'.")
    parser.add_argument("-s", "--skip_start", type=float, default=0, help="Duration in seconds to skip from the start of the video. Default is 0.")
    parser.add_argument("-e", "--skip_end", type=float, default=0, help="Duration in seconds to skip from the end of the video. Default is 0.")
    parser.add_argument("-m", "--max_duration", type=float, default=None, help="Maximum duration in seconds to limit the video. If not provided, the entire video will be processed.")
    args = parser.parse_args()

    input_path = args.input
    output_dir = args.output
    skip_start = args.skip_start
    skip_end = args.skip_end
    max_duration = args.max_duration

    # 如果未提供 output_dir，则根据 input_path 生成
    if output_dir is None:
        if os.path.isfile(input_path):
            output_dir = os.path.splitext(input_path)[0] + "_skip"
        elif os.path.isdir(input_path):
            output_dir = input_path + "_skip"
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
        process_video(video_clip, output_video_path, skip_start, skip_end, max_duration)
        print(f"Successfully processed {video_name}")
