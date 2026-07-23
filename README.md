# TencentMeetingHelper


腾讯会议智能签到助手，基于 AI 目标识别技术，7×24 小时实时监测签到弹窗，第一时间语音提醒您。

开会摸鱼、临时离开、多个会议并行——再也不怕错过签到。


## 环境要求

- Windows
- 显示器的分辨率比例为 16:9 且分别率至少为 1920×1080
- 从 yolov8m.pt 模型上微调的 数据集 train_dataset的地址： https://drive.google.com/file/d/1W9AWTlRy0sT7PyK9b97cfG41U16hIu1d/view?usp=sharing

## 运行方式

- 需要从谷歌drive下载数据集，然后覆盖掉train_dataset，运行 yolo_train.py 文件
- 没有认证的（这个必须要慎用，测试环境下）编译的命令: `pyinstaller --onedir --noconsole --collect-all rapidocr_onnxruntime --exclude-module PyQt5 --exclude-module PySide6 --exclude-module PySide2 --exclude-module PyQt6 --exclude-module matplotlib --exclude-module scipy --exclude-module tensorboard tmeethgui.py`
- 带有认证模块的编译方式（可以发现到只是最后的文件不一样： tmeethgui.py 和 main.py）：`pyinstaller --onedir --noconsole --collect-all rapidocr_onnxruntime --exclude-module PyQt5 --exclude-module PySide6 --exclude-module PySide2 --exclude-module PyQt6 --exclude-module matplotlib --exclude-module scipy --exclude-module tensorboard main.py`


## 安装

前往[Release](https://github.com/NihaoRay/TencentMeetingHelper/releases/)，下载压缩包`tmeethgui.rar`并解压。
打开`config.yaml`，根据需要修改配置。最后双击`tmeethgui.exe`即可运行。

## 下载地址

通过网盘分享的文件：tmeethgui-1.1.rar
链接: https://pan.baidu.com/s/1rFy0SO1UIpxobrmZfiPRYg?pwd=1122 提取码: 1122