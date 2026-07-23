from ultralytics import YOLO
import cv2
import pyautogui
import numpy as np
from ultralytics import YOLO
from PIL import Image
import time


# 1. 加载模型
# 'best.pt' 是你自己训练好的模型路径
# 如果没有训练，暂时用 'yolov8n.pt' 测试（虽然它识别不出按钮）
# try:
#     model = YOLO('runs/detect/my_popup_model9/weights/best.pt')
# except:
#     print("未找到自定义模型，正在下载标准模型用于演示逻辑...")
#     model = YOLO('yolov8n.pt')

model = YOLO('runs/detect/my_popup_model9/weights/best.pt')
def find_and_click(target_class_name, confidence_threshold=0.6):
    """
    截图并使用YOLO识别，如果找到指定类别的物体，则点击它。

    :param target_class_name: 你训练时设定的标签名，例如 'submit_btn'
    :param confidence_threshold: 置信度阈值，低于这个分数的忽略
    """
    # 2. 获取屏幕截图
    # pyautogui 截取的是 PIL 格式 (RGB)
    # screen = pyautogui.screenshot()
    screen = Image.open('test/test_screen_2.png')
    # 3. 格式转换
    # YOLO/OpenCV 处理图像通常需要 numpy 数组
    # 并且 OpenCV 使用 BGR 格式，所以如果需要画图显示，要转一下
    # 但直接传给 ultralytics 的 predict，PIL 格式也是支持的，这里转 numpy 是为了通用性
    img_np = np.array(screen)
    # img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR) # 如果需要用 cv2.imshow 显示，需要这步

    # 4. 模型推理 (Inference)
    # source可以是图片路径、PIL对象、numpy数组
    results = model.predict(source=img_np, save=False, verbose=False)
    # results 是一个列表（因为可能有多张图），我们只传了一张
    result = results[0]
    result.show()

    found_target = False
    # 5. 解析结果
    # result.boxes 包含了所有的检测框
    for box in result.boxes:
        # 获取类别 ID
        cls_id = int(box.cls[0])
        # 获取类别名称
        cls_name = model.names[cls_id]
        # 获取置信度
        conf = float(box.conf[0])
        print(f"查找类别 cls_name:{cls_name}, 置信度 conf:{conf}")
        # 筛选：类别匹配 且 置信度达标
        if cls_name.startswith(target_class_name) and conf > confidence_threshold:
            # 获取坐标 (x1, y1, x2, y2)
            # xyxy 是 tensor 格式，转为 numpy 或 list
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            # 6. 计算中心点
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)

            print(f"找到目标: {cls_name}, 置信度: {conf:.2f}, 中心点: ({center_x}, {center_y})")

            # 7. 执行操作 (点击)
            # 这里的坐标直接对应屏幕坐标，因为我们是全屏截图
            pyautogui.moveTo(center_x, center_y, duration=0.5)
            pyautogui.click()

            found_target = True
            # break  # 找到一个就退出，如果想点击所有匹配项，去掉 break

    if not found_target:
        print(f"当前屏幕未找到目标: {target_class_name}")


# --- 调用示例 ---
if __name__ == "__main__":
    # # 加载你自己训练好的模型
    # model = YOLO('runs/detect/my_popup_model/weights/best.pt')
    # # 对一张图片进行预测
    # results = model('test/test_screen.png')
    # # 或者直接显示结果看看准不准
    # results[0].show()

    # 假设你训练的模型里有个标签叫 'login_button'
    # 如果你用 yolov8n.pt 测试，可以把这里改成 'person' 找屏幕上的人

    try:
        while True:

            start_time = time.time()
            # 要测试的代码
            find_and_click('check_in')
            end_time = time.time()
            run_time = end_time - start_time
            print(f"方法1 - 运行时间: {run_time:.6f} 秒")

            time.sleep(10)  # 等待10秒
    except KeyboardInterrupt:
        print("\n程序被用户中断")



