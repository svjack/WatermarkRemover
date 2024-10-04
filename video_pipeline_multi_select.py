import cv2
import os
import numpy as np
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

def get_first_valid_frame(video_clip, threshold=10, num_frames=10):
    total_frames = int(video_clip.fps * video_clip.duration)
    frame_indices = [int(i * total_frames / num_frames) for i in range(num_frames)]

    for idx in frame_indices:
        frame = video_clip.get_frame(idx / video_clip.fps)
        if frame.mean() > threshold:
            return frame

    return video_clip.get_frame(0)

def select_roi(frame, instructions):
    # 将视频帧调整为720p显示
    display_height = 720
    scale_factor = display_height / frame.shape[0]
    display_width = int(frame.shape[1] * scale_factor)
    display_frame = cv2.resize(frame, (display_width, display_height))

    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(display_frame, instructions, (10, 30), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

    rois = []
    while True:
        r = cv2.selectROI("Select ROI", display_frame)
        if r == (0, 0, 0, 0):  # 如果用户按下c键，退出选择
            break
        rois.append(r)
        cv2.rectangle(display_frame, (r[0], r[1]), (r[0] + r[2], r[1] + r[3]), (0, 255, 0), 2)
        cv2.imshow("Select ROI", display_frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):  # 如果用户按下 'c' 键，取消选择
            rois = []
            break

    cv2.destroyAllWindows()

    rois_original = [(int(r[0] / scale_factor), int(r[1] / scale_factor), int(r[2] / scale_factor), int(r[3] / scale_factor)) for r in rois]

    return rois_original

def skip_and_limit_video(video_clip, skip_start, skip_end, max_duration):
    total_duration = video_clip.duration

    if skip_start + skip_end >= total_duration:
        print(f"Skipping duration ({skip_start}s + {skip_end}s) is longer than or equal to video duration ({total_duration}s). Skipping entire video.")
        return None

    end_time = total_duration - skip_end
    skipped_clip = video_clip.subclip(skip_start, end_time)

    if skipped_clip.duration > max_duration:
        skipped_clip = skipped_clip.subclip(0, max_duration)

    return skipped_clip

def clip_video(video_clip, rois, max_frames=None):
    def clip_frame(frame):
        for roi in rois:
            frame = frame[roi[1]:roi[1] + roi[3], roi[0]:roi[0] + roi[2]]
        return frame

    if max_frames is not None:
        video_clip = video_clip.subclip(0, min(video_clip.duration, max_frames / video_clip.fps))

    clipped_video = video_clip.fl_image(clip_frame)
    return clipped_video

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
    rois = select_roi(frames[0], "Select ROI for watermark and press SPACE or ENTER. Press 'c' to finish.")

    masks = []
    for roi in rois:
        masks.extend([detect_watermark_adaptive(frame, roi) for frame in frames])

    final_mask = sum((mask == 255).astype(np.uint8) for mask in masks)
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

def loop_video(video_clip, loop_duration):
    total_duration = video_clip.duration
    loop_count = int(loop_duration / total_duration)
    remaining_duration = loop_duration % total_duration

    looped_clips = [video_clip] * loop_count
    if remaining_duration > 0:
        looped_clips.append(video_clip.subclip(0, remaining_duration))

    final_clip = concatenate_videoclips(looped_clips)
    return final_clip

def process_video_pipeline(input_path, output_dir, skip_start=0, skip_end=0, max_duration=None, clip_roi=None, max_frames=None, watermark_mask=None, loop_duration=None):
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

        # Step 1: Skip and limit video
        if skip_start > 0 or skip_end > 0 or max_duration is not None:
            video_clip = skip_and_limit_video(video_clip, skip_start, skip_end, max_duration)
            if video_clip is None:
                continue
            output_video_path += "_skip"

        # Step 2: Clip video
        if clip_roi is not None:
            if clip_roi == "auto":
                frame = get_first_valid_frame(video_clip)
                clip_roi = select_roi(frame, "Select ROI for clipping and press SPACE or ENTER. Press 'c' to finish.")
            video_clip = clip_video(video_clip, clip_roi, max_frames)
            output_video_path += "_clip"

        # Step 3: Remove watermark
        if watermark_mask is not None:
            if watermark_mask == "auto":
                watermark_mask = generate_watermark_mask(video_clip)
            mask_func = lambda frame: cv2.inpaint(frame, watermark_mask, 3, cv2.INPAINT_NS)
            process_video(video_clip, output_video_path + "_rmwtmk", mask_func, max_frames)
            video_clip = VideoFileClip(output_video_path + "_rmwtmk.mp4")

        # Step 4: Loop video
        if loop_duration is not None:
            looped_video = loop_video(video_clip, loop_duration)
            looped_video.write_videofile(output_video_path + "_rec.mp4", codec="libx264")

        print(f"Successfully processed {video_name}")

'''
python video_pipeline_multi_select.py -i input_video.mp4 -o output_dir -s 5 -e 10 -m 120 -c auto -w auto -l 360

python .\video_pipeline_multi_select.py  --input  .\【原神】须弥3.0雨林音乐实录合集 -s 5 -e 10 -m 120 -c auto -w auto -l 360
'''

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process videos with a pipeline of operations.")
    parser.add_argument("-i", "--input", default="video", help="Path to the input video file or directory containing videos. Default is 'video'.")
    parser.add_argument("-o", "--output", default=None, help="Path to the output directory. If not provided, it will be generated as input_path + '_processed'.")
    parser.add_argument("-s", "--skip_start", type=float, default=0, help="Duration in seconds to skip from the start of the video. Default is 0.")
    parser.add_argument("-e", "--skip_end", type=float, default=0, help="Duration in seconds to skip from the end of the video. Default is 0.")
    parser.add_argument("-m", "--max_duration", type=float, default=None, help="Maximum duration in seconds to limit the video. If not provided, the entire video will be processed.")
    parser.add_argument("-c", "--clip_roi", default=None, help="Region of interest (ROI) for clipping. Use 'auto' to select ROI interactively.")
    parser.add_argument("-f", "--frames", type=int, default=None, help="Number of frames to process. If not provided, the entire video will be processed.")
    parser.add_argument("-w", "--watermark_mask", default=None, help="Watermark mask. Use 'auto' to generate mask interactively.")
    parser.add_argument("-l", "--loop_duration", type=float, default=None, help="Duration in seconds to loop the video. If not provided, the entire video will be processed.")
    args = parser.parse_args()

    input_path = args.input
    output_dir = args.output
    skip_start = args.skip_start
    skip_end = args.skip_end
    max_duration = args.max_duration
    clip_roi = args.clip_roi
    max_frames = args.frames
    watermark_mask = args.watermark_mask
    loop_duration = args.loop_duration

    if output_dir is None:
        if os.path.isfile(input_path):
            output_dir = os.path.splitext(input_path)[0] + "_processed"
        elif os.path.isdir(input_path):
            output_dir = input_path + "_processed"
        else:
            print(f"Invalid input path: {input_path}")
            exit(1)

    process_video_pipeline(input_path, output_dir, skip_start, skip_end, max_duration, clip_roi, max_frames, watermark_mask, loop_duration)
