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

def speed_change_video(video_clip, speed_factor, output_path):
    if speed_factor == 1:
        # 如果变速因子为1，直接复制原视频
        video_clip.write_videofile(output_path, codec="libx264")
    else:
        # 否则，按变速因子调整视频速度
        new_duration = video_clip.duration / speed_factor
        sped_up_clip = video_clip.speedx(speed_factor)
        sped_up_clip.write_videofile(output_path, codec="libx264")

'''
python video_speedchanger.py -i .\原神变速测试125  -s 1.25
python video_speedchanger.py -i .\原神变速测试75  -s 0.75
python video_speedchanger.py -i .\原神变速测试95  -s 0.95
'''

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Change the speed of videos in a directory.")
    parser.add_argument("-i", "--input", default="video", help="Path to the input video file or directory containing videos. Default is 'video'.")
    parser.add_argument("-o", "--output", default=None, help="Path to the output directory. If not provided, it will be generated as input_path + '_speed'.")
    parser.add_argument("-s", "--speed", type=float, default=1.0, help="Speed factor for video. Default is 1.0 (no change).")
    args = parser.parse_args()

    input_path = args.input
    output_dir = args.output
    speed_factor = args.speed

    # 如果未提供 output_dir，则根据 input_path 生成
    if output_dir is None:
        if os.path.isfile(input_path):
            output_dir = os.path.splitext(input_path)[0] + "_speed"
        elif os.path.isdir(input_path):
            output_dir = input_path + "_speed"
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

    for video_file in video_files:
        video_clip = VideoFileClip(video_file)

        # 生成输出视频路径
        sped_up_video_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(video_file))[0]}_speed_{speed_factor}x.mp4")

        # 变速处理
        speed_change_video(video_clip, speed_factor, sped_up_video_path)

        print(f"Successfully changed speed of {video_file} to {sped_up_video_path}")
