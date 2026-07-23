import time
import numpy as np
import pyautogui
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import pygame
import onnxruntime as ort
import cv2
# import easyocr
from rapidocr_onnxruntime import RapidOCR
import faulthandler
# 开启底层崩溃日志记录
faulthandler.enable(open('crash_log.txt', 'w'))

# ========== ONNX 模型加载 ==========
session = ort.InferenceSession('best.onnx')
input_name = session.get_inputs()[0].name
input_shape = session.get_inputs()[0].shape  # 例如 [1, 3, 640, 640]
IMG_SIZE = input_shape[2]  # 640

# 之前
# EasyOCR 只初始化一次（初始化比较慢）
# reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)

# 现在
ocr_engine = RapidOCR()

# 你模型里的类别名（和训练时一致，按顺序填）
CLASS_NAMES = {0:'jiaru', 1:'checkin', 2:'qiandao', 3:'guanbi'}  # 根据你实际的类别修改


def preprocess(img_np):
    """将截图预处理为 ONNX 模型输入格式"""
    img = cv2.resize(img_np, (IMG_SIZE, IMG_SIZE))
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))  # HWC → CHW
    img = np.expand_dims(img, axis=0)    # 加 batch 维度
    return img


def postprocess(output, orig_w, orig_h, conf_threshold=0.5):
    """解析 YOLOv8 ONNX 输出"""
    # output shape: [1, num_classes+4, num_detections]
    preds = output[0]  # shape: (1, 4+num_classes, N)
    preds = preds[0].T  # shape: (N, 4+num_classes)

    results = []
    for det in preds:
        x_center, y_center, w, h = det[:4]
        class_scores = det[4:]
        cls_id = np.argmax(class_scores)
        conf = class_scores[cls_id]

        if conf < conf_threshold:
            continue

        # 坐标还原到原图尺寸
        x1 = (x_center - w / 2) / IMG_SIZE * orig_w
        y1 = (y_center - h / 2) / IMG_SIZE * orig_h
        x2 = (x_center + w / 2) / IMG_SIZE * orig_w
        y2 = (y_center + h / 2) / IMG_SIZE * orig_h

        cls_name = CLASS_NAMES.get(int(cls_id), f'class_{cls_id}')
        results.append({
            'cls_name': cls_name,
            'conf': float(conf),
            'bbox': (x1, y1, x2, y2)
        })

    return results


# def ocr_crop(img_np, bbox):
#     """裁剪 YOLO 检测到的区域，用 OCR 识别文字"""
#     x1, y1, x2, y2 = bbox
#     crop = img_np[y1:y2, x1:x2]
#
#     if crop.size == 0:
#         return ""
#
#     # EasyOCR 识别裁剪区域
#     results = reader.readtext(crop)
#
#     # 把识别到的所有文字拼接起来
#     texts = [text for (_, text, conf) in results if conf > 0.3]
#     return " ".join(texts)

# def ocr_crop(img_np, bbox):
#     """裁剪 YOLO 检测到的区域，用 OCR 识别文字"""
#     x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
#     # 防止越界
#     h, w = img_np.shape[:2]
#     x1, y1 = max(0, x1), max(0, y1)
#     x2, y2 = min(w, x2), min(h, y2)
#     if x2 <= x1 or y2 <= y1:
#         return ""
#     crop = img_np[y1:y2, x1:x2]
#     # EasyOCR 识别裁剪区域
#     results = reader.readtext(crop)
#     # 把识别到的所有文字拼接起来
#     texts = [text for (_, text, conf) in results if conf > 0.3]
#     return " ".join(texts)


# 之前
# import easyocr
# reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)

# 现在


def ocr_crop(img_np, bbox):
    """裁剪 YOLO 检测到的区域，用 OCR 识别文字"""
    x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])

    h, w = img_np.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)

    if x2 <= x1 or y2 <= y1:
        return ""

    crop = img_np[y1:y2, x1:x2]

    result, _ = ocr_engine(crop)

    if result is None:
        return ""

    texts = [item[1] for item in result if item[2] > 0.3]
    return " ".join(texts)


# ========== 模块顶部新增缓存变量 ==========
_volume_ctrl = None
_volume_devices = None
_volume_interface = None

def set_volume(level, logfunc):
    global _volume_ctrl, _volume_devices, _volume_interface

    if _volume_ctrl is None:
        _volume_devices = AudioUtilities.GetSpeakers()
        if hasattr(_volume_devices, 'Activate'):
            _volume_interface = _volume_devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        else:
            _volume_interface = _volume_devices._dev.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        _volume_ctrl = cast(_volume_interface, POINTER(IAudioEndpointVolume))

    _volume_ctrl.SetMasterVolumeLevelScalar(level, None)
    logfunc(f"音量已设置为 {int(level * 100)}%")


def play_mp3(file_path, logfunc, duration=15):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    time.sleep(duration)
    pygame.mixer.music.stop()
    pygame.mixer.quit()
    logfunc(f"已播放 {duration} 秒，停止")


def find_and_click(target_class_name, logfunc, confidence_threshold=0.6, img_callback=None):
    screen_width, screen_height = pyautogui.size()
    region_width = 1480
    region_height = 860
    left = screen_width - region_width
    top = 0

    screenshot = pyautogui.screenshot(region=(left, top, region_width, region_height))
    img_np = np.array(screenshot)

    # ONNX 推理
    input_tensor = preprocess(img_np)
    output = session.run(None, {input_name: input_tensor})
    detections = postprocess(output, region_width, region_height, confidence_threshold)

    # ===== 绘制所有检测框到图像上 =====
    annotated = img_np.copy()
    for det in detections:
        bbox = det['bbox']
        x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
        color = (0, 255, 0)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        label = f"{det['cls_name']} {det['conf']:.2f}"
        # 文字背景，方便看清
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(annotated, (x1, max(y1 - th - 8, 0)), (x1 + tw, max(y1, th + 8)), color, -1)
        cv2.putText(annotated, label, (x1, max(y1 - 5, th + 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    # 回调：将带标注的图像传回 UI 显示
    if img_callback:
        img_callback(annotated)

    # ===== 处理业务逻辑 =====
    found_target = False
    for det in detections:
        bbox = det['bbox']
        text = ocr_crop(img_np, bbox)

        logfunc(f"cls_name:{det['cls_name']}, conf:{det['conf']:.2f}, text:{text}")

        if det['cls_name'] in target_class_name and ("加入" in text or "签到" in text) and det['conf'] > confidence_threshold:
            logfunc(f"找到目标: {det['cls_name']}, 置信度: {det['conf']:.2f}")
            set_volume(0.9, logfunc)
            play_mp3("music/voice.mp3", logfunc, duration=6)
            set_volume(0.2, logfunc)
            logfunc("提示音播放完毕，声音调整至0.2")
            found_target = True
            break

    if not found_target:
        logfunc(f"未找到目标: {target_class_name}")


