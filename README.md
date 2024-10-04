# WatermarkRemover
通过手动框选区域批量去除多个视频中位置固定的某个水印，项目基于Python 3.12。

## 如何使用

### 1. 安装依赖：
  `pip install -r requirements.txt`

### 2. 准备视频文件
  待处理视频放在`video`文件夹下，所有视频尺寸须保持一致。

### 3. 运行程序
#### 分不同功能处理视频
###### 1 跳过视频首尾
  ` python .\video_skipper.py  --input  .\【原神延时摄影】全图27个钓鱼点白天黑夜风景全赏析 -s 5 -e 10 -m 120`
###### 2 剪辑矩形区域
  `python .\video_cliper.py --input .\【原神延时摄影】全图27个钓鱼点白天黑夜风景全赏析  -f 1000`
###### 3 去水印
  `python .\watermark_remover.py  --input  .\【原神延时摄影】全图27个钓鱼点白天黑夜风景全赏析_clip`
###### 4 循环视频
  `python .\video_recer.py --input .\【原神延时摄影】全图27个钓鱼点白天黑夜风景全赏析_clip_rmwtmk  -s 360`
#### 跳过+剪辑+去水印（多区域选择）+循环
  `python .\video_pipeline_multi_select.py  --input  .\【原神】须弥3.0雨林音乐实录合集 -s 5 -e 10 -m 120 -c auto -w auto -l 360`

### 4.选择水印区域
  鼠标框选水印对应区域后按**SPACE**或**ENTER**键，处理后视频在`output`文件夹下，格式为mp4。

## 效果
- 原始帧
<a href=''><img src='https://raw.githubusercontent.com/lxulxu/WatermarkRemover/master/image/origin.jpg'></a>
- 去除水印
<a href=''><img src='https://raw.githubusercontent.com/lxulxu/WatermarkRemover/master/image/no_watermark.jpg'></a>

