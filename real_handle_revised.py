import time
import numpy as np
import pyautogui
from ultralytics import YOLO
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import pygame

# 加载模型
model = YOLO('runs/detect/my_popup_model6/weights/best.pt')

def set_volume(level):
    """设置系统音量，level 范围 0.0 ~ 1.0"""
    devices = AudioUtilities.GetSpeakers()
    # 兼容新旧版本
    if hasattr(devices, 'Activate'):
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    else:
        # 新版 pycaw，取内部 COM 对象
        interface = devices._dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volume.SetMasterVolumeLevelScalar(level, None)
    print(f"音量已设置为 {int(level * 100)}%")

def play_mp3(file_path, duration=15):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    time.sleep(duration)
    pygame.mixer.music.stop()
    pygame.mixer.quit()
    print(f"已播放 {duration} 秒，停止")


def find_and_click(target_class_name, confidence_threshold=0.6):
    # --- 1. 获取图像源 ---
    # if use_local_image:
    #     print("警告：正在使用本地静态图片进行测试，点击操作可能不准确！")
    #     screen = Image.open('test/test_screen_2.png')  # 你的测试图片
    # else:
    #     # 实战模式：截取全屏
    #     screen = pyautogui.screenshot()
    # 1. 获取屏幕的分辨率
    screen_width, screen_height = pyautogui.size()
    # 2. 定义截图区域的宽度和高度
    region_width = 1480
    region_height = 860
    # 3. 计算区域的起始坐标 (left, top)
    # 左边界 = 屏幕总宽度 - 区域宽度
    left = screen_width - region_width
    # 上边界 = 0 (因为是右上角)
    top = 0
    # 4. 进行截图
    # region 参数格式: (left, top, width, height)
    screenshot = pyautogui.screenshot(region=(left, top, region_width, region_height))
    # screen = pyautogui.screenshot()
    # 转为 numpy 数组 (RGB)
    img_np = np.array(screenshot)
    # --- 2. 模型推理 ---
    results = model.predict(source=img_np, save=False, verbose=False)
    result = results[0]
    result.show()
    found_target = False
    # --- 3. 解析结果 ---
    for box in result.boxes:
        cls_id = int(box.cls[0])
        cls_name = model.names[cls_id]
        conf = float(box.conf[0])
        print(f"cls_name:{cls_name}, conf:{conf}")
        # 筛选目标
        if cls_name.startswith(target_class_name) and conf > confidence_threshold:
            print(f"找到目标: {cls_name}, 置信度: {conf:.2f}")
            set_volume(0.9)  # 设置音量为50%
            play_mp3("music/voice.mp3", duration=6)
            set_volume(0.2)  # 设置音量为50%
            print("提示音播放完毕，声音调整至0.2")
            found_target = True
            # 如果只想点击置信度最高的一个，可以在这里 break
            break
    if not found_target:
        print(f"未找到目标: {target_class_name}")

if __name__ == "__main__":
    # set_volume(0.5)  # 设置音量为50%
    # play_mp3("music/voice.mp3", duration=10)
    # print("提示音播放完毕")
    try:
        while True:
            start_time = time.time()
            # --- 重要设置 ---
            # 如果你想测试识别准不准，把这里设为 True (不会乱点鼠标)
            # 如果你要正式挂机运行，把这里设为 False (会截屏并点击)
            # IS_TEST_MODE = False
            IS_TEST_MODE = True

            find_and_click('checkin', confidence_threshold=0.5)

            run_time = time.time() - start_time
            print(f"单次运行耗时: {run_time:.4f} 秒\n")

            time.sleep(5)  # 间隔5秒

    except KeyboardInterrupt:
        print("\n程序已停止")