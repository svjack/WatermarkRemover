# coding:utf-8

import cv2
import os
import numpy as np
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

def calculate_brightness(frame):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return np.mean(gray_frame)

def select_bright_frames(video_clip, top_k=10, time_window=10, frame_skip=10, take_one_step = 50):
    assert take_one_step > 0
    assert type(take_one_step) == type(0)
    total_frames = int(video_clip.fps * video_clip.duration)
    total_duration = video_clip.duration
    window_size = total_duration / time_window

    bright_frames = []

    print("start time_window")
    for window in tqdm(range(time_window)):
        start_time = window * window_size
        end_time = (window + 1) * window_size

        window_frames = []
        for i in tqdm(range(int(start_time * video_clip.fps), int(end_time * video_clip.fps), frame_skip)):
            if i % take_one_step == 0:
                frame = video_clip.get_frame(i / video_clip.fps)
                brightness = calculate_brightness(frame)
                window_frames.append((i, brightness))
        if not window_frames:
            for i in tqdm(range(int(start_time * video_clip.fps), int(end_time * video_clip.fps), frame_skip)):
                if i % 1 == 0:
                    frame = video_clip.get_frame(i / video_clip.fps)
                    brightness = calculate_brightness(frame)
                    window_frames.append((i, brightness))

        # 选择当前时间窗口内最明亮的帧
        window_frames.sort(key=lambda x: x[1], reverse=True)
        if window_frames:
            bright_frames.append(window_frames[0])

    # 选择前 top_k 个明亮帧
    bright_frames.sort(key=lambda x: x[1], reverse=True)
    top_bright_frames = bright_frames[:top_k]
    top_bright_frames.sort(key=lambda x: x[0])  # 按帧索引排序

    return top_bright_frames

def interactive_frame_selection(video_clip, bright_frames):
    for idx, (frame_idx, _) in enumerate(bright_frames):
        frame = video_clip.get_frame(frame_idx / video_clip.fps)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # 将视频帧调整为720p显示
        display_height = 720
        scale_factor = display_height / frame.shape[0]
        display_width = int(frame.shape[1] * scale_factor)
        display_frame = cv2.resize(frame, (display_width, display_height))

        instructions = f"Frame {idx + 1}/{len(bright_frames)}: Press 's' to select this frame, 'n' to skip to the next frame, 'q' to quit."
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(display_frame, instructions, (10, 30), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

        cv2.imshow("Select Bright Frame", display_frame)
        key = cv2.waitKey(0) & 0xFF

        if key == ord('s'):
            cv2.destroyAllWindows()
            return frame_idx / video_clip.fps
        elif key == ord('q'):
            cv2.destroyAllWindows()
            return None

    cv2.destroyAllWindows()
    return None

def process_video(video_clip, output_path, start_time):
    if start_time is not None:
        clipped_video = video_clip.subclip(start_time)
        try:
            clipped_video.write_videofile(f"{output_path}.mp4", codec="libx264")
        except:
            print("clipped_video write error")
    else:
        print("No frame selected.")

def calculate_bright_frames_for_all_videos(input_path, top_k, time_window, frame_skip):
    bright_frames_dict = {}

    if os.path.isfile(input_path):
        videos = [input_path] if is_valid_video_file(input_path) else []
    elif os.path.isdir(input_path):
        videos = [f for f in os.listdir(input_path) if is_valid_video_file(os.path.join(input_path, f))]
    else:
        print(f"Invalid input path: {input_path}")
        exit(1)

    for video in tqdm(videos, desc="Calculating bright frames"):
        video_clip = VideoFileClip(os.path.join(input_path, video))
        bright_frames = select_bright_frames(video_clip, top_k, time_window, frame_skip)
        bright_frames_dict[video] = bright_frames

    return bright_frames_dict

def select_start_times(input_path, bright_frames_dict):
    start_times_dict = {}

    for video, bright_frames in tqdm(bright_frames_dict.items(), desc="Selecting start times"):
        video_clip = VideoFileClip(os.path.join(input_path, video))
        start_time = interactive_frame_selection(video_clip, bright_frames)
        start_times_dict[video] = start_time

    return start_times_dict

def process_selected_frames(input_path, output_dir, start_times_dict):
    ensure_directory_exists(output_dir)

    for video, start_time in tqdm(start_times_dict.items(), desc="Processing videos"):
        video_clip = VideoFileClip(os.path.join(input_path, video))
        video_name = os.path.basename(video)
        output_video_path = os.path.join(output_dir, os.path.splitext(video_name)[0])

        process_video(video_clip, output_video_path, start_time)
        print(f"Successfully processed {video_name}")

'''
python video_darkness_skipper.py -i .\【原神延时摄影】全图27个钓鱼点白天黑夜风景全赏析_skip_3个  -k 10 -w 10 -s 10
'''

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interactively select the start frame for video clipping based on brightness.")
    parser.add_argument("-i", "--input", default="video", help="Path to the input video file or directory containing videos. Default is 'video'.")
    parser.add_argument("-o", "--output", default=None, help="Path to the output directory. If not provided, it will be generated as input_path + '_bright'.")
    parser.add_argument("-k", "--top_k", type=int, default=10, help="Number of top bright frames to select from. Default is 10.")
    parser.add_argument("-w", "--time_window", type=int, default=10, help="Number of time windows to divide the video into. Default is 10.")
    parser.add_argument("-s", "--frame_skip", type=int, default=10, help="Number of frames to skip when calculating brightness. Default is 10.")
    args = parser.parse_args()

    input_path = args.input
    output_dir = args.output
    top_k = args.top_k
    time_window = args.time_window
    frame_skip = args.frame_skip

    if output_dir is None:
        if os.path.isfile(input_path):
            output_dir = os.path.splitext(input_path)[0] + "_bright"
        elif os.path.isdir(input_path):
            output_dir = input_path + "_bright"
        else:
            print(f"Invalid input path: {input_path}")
            exit(1)

    #### 三个”集中“： 集中计算 集中选取 集中处理
    bright_frames_dict = calculate_bright_frames_for_all_videos(input_path, top_k, time_window, frame_skip)
    start_times_dict = select_start_times(input_path, bright_frames_dict)
    process_selected_frames(input_path, output_dir, start_times_dict)
