# coding:utf-8

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
    try:
        processed_video.write_videofile(f"{output_path}.mp4", codec="libx264")
    except:
        print("clipped_video write error")

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
