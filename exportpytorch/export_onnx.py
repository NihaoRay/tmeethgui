

if __name__ == "__main__":
    from ultralytics import YOLO

    model = YOLO('../runs/detect/my_popup_model8/weights/best.pt')
    model.export(format='onnx')
    # 会生成 best.onnx