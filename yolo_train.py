from ultralytics import YOLO

def main():
    # 1. 加载预训练模型
    # 'yolov8n.pt' 是最轻量级的版本，速度最快，适合简单的弹框识别
    # 如果电脑显卡好，可以换成 'yolov8s.pt' 或 'yolov8m.pt' 精度更高
    # my_popup_model_pro2/weights/best.pt 是通过 yolov8l.pt 基础上微调出来web页面按钮选择。
    model = YOLO('runs/detect/my_popup_model_pro2/weights/best.pt')

    # 2. 开始训练
    results = model.train(
        data='yolo_img/data.yaml', # 指向你刚才写的 yaml 文件
        epochs=150,      # 训练轮数。数据少的话 50-100 轮足够了
        imgsz=640,      # 图片大小，默认 640
        batch=20,       # 显存不够就改小，比如 8 或 4
        workers=8,      # Windows下建议设为0，否则容易报错
        patience=30,  # 早停机制：如果连续 30 轮精度不再提升，则自动停止，防止过拟合
        optimizer='auto',  # 自动选择优化器 (通常大 batch 会自动选 SGD 或 AdamW)
        device='0',     # 使用显卡训练。如果没有显卡，写 'cpu'
        name='my_popup_model_pro' # 训练结果保存的文件夹名字
    )

if __name__ == '__main__':
    # Windows 下必须把代码放在 main block 里运行
    main()