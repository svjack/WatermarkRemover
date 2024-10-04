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
