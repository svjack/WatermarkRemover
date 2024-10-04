下面是4个用于处理视频的功能，分别是

1 跳过视频首尾
 python .\video_skipper.py  --input  .\【原神延时摄影】全图27个钓鱼点白天黑夜风景全赏析 -s 5 -e 10 -m 120

2 剪辑矩形区域
python .\video_cliper.py --input .\【原神延时摄影】全图27个钓鱼点白天黑夜风景全赏析  -f 1000

3 去水印
python .\watermark_remover.py  --input  .\【原神延时摄影】全图27个钓鱼点白天黑夜风景全赏析_clip

4 循环视频
python .\video_recer.py --input .\【原神延时摄影】全图27个钓鱼点白天黑夜风景全赏析_clip_rmwtmk  -s 360

下面是它们的源码定义

video_skipper.py

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

video_cliper.py

import cv2
import os
from moviepy.editor import VideoFileClip
import argparse

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            print(f"Created directory: {directory}")
        except OSError as error:
            print(f"Error creating directory {directory}: {error}")
            raise

def get_first_valid_frame(video_clip, threshold=10, num_frames=10):
    total_frames = int(video_clip.fps * video_clip.duration)
    frame_indices = [int(i * total_frames / num_frames) for i in range(num_frames)]

    for idx in frame_indices:
        frame = video_clip.get_frame(idx / video_clip.fps)
        if frame.mean() > threshold:
            return frame

    return video_clip.get_frame(0)

def select_roi_for_clipping(video_clip):
    frame = get_first_valid_frame(video_clip)

    # 将视频帧调整为720p显示
    display_height = 720
    scale_factor = display_height / frame.shape[0]
    display_width = int(frame.shape[1] * scale_factor)
    display_frame = cv2.resize(frame, (display_width, display_height))

    instructions = "Select ROI for clipping and press SPACE or ENTER"
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(display_frame, instructions, (10, 30), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

    r = cv2.selectROI(display_frame)
    cv2.destroyAllWindows()

    r_original = (int(r[0] / scale_factor), int(r[1] / scale_factor), int(r[2] / scale_factor), int(r[3] / scale_factor))

    return r_original

def clip_video(video_clip, roi, output_path, max_frames=None):
    def clip_frame(frame):
        return frame[roi[1]:roi[1] + roi[3], roi[0]:roi[0] + roi[2]]

    if max_frames is not None:
        video_clip = video_clip.subclip(0, min(video_clip.duration, max_frames / video_clip.fps))

    clipped_video = video_clip.fl_image(clip_frame)
    clipped_video.write_videofile(output_path, codec="libx264")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clip a video based on a selected region of interest (ROI).")
    parser.add_argument("-i", "--input", default="video", help="Path to the input video file or directory containing videos. Default is 'video'.")
    parser.add_argument("-o", "--output", default=None, help="Path to the output directory. If not provided, it will be generated as input_path + '_clip'.")
    parser.add_argument("-f", "--frames", type=int, default=None, help="Number of frames to clip. If not provided, the entire video will be processed.")
    args = parser.parse_args()

    input_path = args.input
    output_dir = args.output
    max_frames = args.frames

    # 如果未提供 output_dir，则根据 input_path 生成
    if output_dir is None:
        if os.path.isfile(input_path):
            output_dir = os.path.splitext(input_path)[0] + "_clip"
        elif os.path.isdir(input_path):
            output_dir = input_path + "_clip"
        else:
            print(f"Invalid input path: {input_path}")
            exit(1)

    ensure_directory_exists(output_dir)

    if os.path.isfile(input_path):
        video_files = [input_path]
    elif os.path.isdir(input_path):
        video_files = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.endswith(('.mp4', '.avi', '.mov'))]
    else:
        print(f"Invalid input path: {input_path}")
        exit(1)

    # 初始化默认的 clip_roi
    default_clip_roi = None

    for video_file in video_files:
        video_clip = VideoFileClip(video_file)

        # 如果还没有默认的 clip_roi，则选择一个
        if default_clip_roi is None:
            default_clip_roi = select_roi_for_clipping(video_clip)

        # 使用默认的 clip_roi 进行裁剪
        clipped_video_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(video_file))[0]}_clip.mp4")
        clip_video(video_clip, default_clip_roi, clipped_video_path, max_frames)

        print(f"Successfully clipped {video_file} to {clipped_video_path}")

watermark_remover.py

import cv2
import numpy as np
import glob
from moviepy.editor import VideoFileClip
import os
from tqdm import tqdm
import argparse

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

def get_first_valid_frame(video_clip, threshold=10, num_frames=10):
    total_frames = int(video_clip.fps * video_clip.duration)
    frame_indices = [int(i * total_frames / num_frames) for i in range(num_frames)]

    for idx in frame_indices:
        frame = video_clip.get_frame(idx / video_clip.fps)
        if frame.mean() > threshold:
            return frame

    return video_clip.get_frame(0)

def select_roi_for_mask(video_clip):
    frame = get_first_valid_frame(video_clip)

    # 将视频帧调整为720p显示
    display_height = 720
    scale_factor = display_height / frame.shape[0]
    display_width = int(frame.shape[1] * scale_factor)
    display_frame = cv2.resize(frame, (display_width, display_height))

    instructions = "Select ROI and press SPACE or ENTER"
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(display_frame, instructions, (10, 30), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

    r = cv2.selectROI(display_frame)
    cv2.destroyAllWindows()

    r_original = (int(r[0] / scale_factor), int(r[1] / scale_factor), int(r[2] / scale_factor), int(r[3] / scale_factor))

    return r_original

def detect_watermark_adaptive(frame, roi):
    roi_frame = frame[roi[1]:roi[1] + roi[3], roi[0]:roi[0] + roi[2]]
    gray_frame = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
    _, binary_frame = cv2.threshold(gray_frame, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    mask = np.zeros_like(frame[:, :, 0], dtype=np.uint8)
    mask[roi[1]:roi[1] + roi[3], roi[0]:roi[0] + roi[2]] = binary_frame

    return mask

def generate_watermark_mask(video_clip, num_frames=10, min_frame_count=7):
    total_frames = int(video_clip.duration * video_clip.fps)
    frame_indices = [int(i * total_frames / num_frames) for i in range(num_frames)]

    frames = [video_clip.get_frame(idx / video_clip.fps) for idx in frame_indices]
    r_original = select_roi_for_mask(video_clip)

    masks = [detect_watermark_adaptive(frame, r_original) for frame in frames]

    final_mask = sum((mask == 255).astype(np.uint8) for mask in masks)
    # 根据像素点在至少min_frame_count张以上的帧中的出现来生成最终的遮罩
    final_mask = np.where(final_mask >= min_frame_count, 255, 0).astype(np.uint8)

    kernel = np.ones((5, 5), np.uint8)
    return cv2.dilate(final_mask, kernel)

def process_video(video_clip, output_path, apply_mask_func, max_frames=None):
    total_frames = int(video_clip.duration * video_clip.fps)
    progress_bar = tqdm(total=total_frames, desc="Processing Frames", unit="frames")

    if max_frames is not None:
        video_clip = video_clip.subclip(0, min(video_clip.duration, max_frames / video_clip.fps))

    def process_frame(frame):
        result = apply_mask_func(frame)
        progress_bar.update(1)
        return result

    processed_video = video_clip.fl_image(process_frame)
    processed_video.write_videofile(f"{output_path}.mp4", codec="libx264")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process videos to detect and remove watermarks.")
    parser.add_argument("-i", "--input", default="video", help="Path to the input video file or directory containing videos. Default is 'video'.")
    parser.add_argument("-o", "--output", default=None, help="Path to the output directory. If not provided, it will be generated as input_path + '_rmwtmk'.")
    parser.add_argument("-f", "--frames", type=int, default=None, help="Number of frames to process. If not provided, the entire video will be processed.")
    args = parser.parse_args()

    input_path = args.input
    output_dir = args.output
    max_frames = args.frames

    # 如果未提供 output_dir，则根据 input_path 生成
    if output_dir is None:
        if os.path.isfile(input_path):
            output_dir = os.path.splitext(input_path)[0] + "_rmwtmk"
        elif os.path.isdir(input_path):
            output_dir = input_path + "_rmwtmk"
        else:
            print(f"Invalid input path: {input_path}")
            exit(1)

    ensure_directory_exists(output_dir)

    if os.path.isfile(input_path):
        videos = [input_path] if is_valid_video_file(input_path) else []
    elif os.path.isdir(input_path):
        videos = [f for f in glob.glob(os.path.join(input_path, "*")) if is_valid_video_file(f)]
    else:
        print(f"Invalid input path: {input_path}")
        exit(1)

    watermark_mask = None

    for video in videos:
        video_clip = VideoFileClip(video)
        if watermark_mask is None:
            watermark_mask = generate_watermark_mask(video_clip)

        mask_func = lambda frame: cv2.inpaint(frame, watermark_mask, 3, cv2.INPAINT_NS)
        video_name = os.path.basename(video)
        output_video_path = os.path.join(output_dir, os.path.splitext(video_name)[0])
        process_video(video_clip, output_video_path, mask_func, max_frames)
        print(f"Successfully processed {video_name}")

video_recer.py

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
    looped_video.write_videofile(f"{output_path}.mp4", codec="libx264")

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

这四种功能都是对一个视频路径进行的，并输出到另一个视频路径
这四种功能是可以按照上面的4个顺序进行的

现在要求你 将这四个功能按照上面的顺序进行合并（
这里要注意各个功能输入路径与输出路径的挂钩问题，
既一个的输入必须是上一个的输出
）
并且合适地修改和合并命令行输入参数

而且使得这4个功能是按序可选的，可以跳过其中的任意一个功能
