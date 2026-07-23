import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from real_handle_onnx import find_and_click, play_mp3, set_volume


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("腾讯会议签到工具")
        root.attributes('-topmost', True)  # 窗口始终置顶
        self.root.geometry("400x300")
        self.root.resizable(True, True)

        ### 在桌面的左下方
        # 设置窗口大小
        win_width = 400
        win_height = 450
        # 获取屏幕尺寸
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        # 计算左下角位置（留一点底部边距，避免被任务栏遮挡）
        x = 20
        y = screen_height - win_height - 120  # 70 是任务栏大概高度
        root.geometry(f"{win_width}x{win_height}+{x}+{y}")

        # --- 输入区域 ---
        frame_input = ttk.LabelFrame(root, text="输入参数", padding=10)
        frame_input.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Label(frame_input, text="（暂未开通）选择文件：").grid(row=0, column=0, sticky="w")
        self.file_path = tk.StringVar()
        ttk.Entry(frame_input, textvariable=self.file_path, width=40).grid(row=0, column=1, padx=5)
        ttk.Button(frame_input, text="浏览", command=self.browse_file).grid(row=0, column=2)

        ttk.Label(frame_input, text="（暂未开通）音量大小（0-1）：").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.param = tk.StringVar(value="0.6")
        ttk.Entry(frame_input, textvariable=self.param, width=40).grid(row=1, column=1, padx=5, pady=(10, 0))

        # --- 按钮区域 ---
        frame_btn = ttk.Frame(root)
        frame_btn.pack(fill="x", padx=10, pady=5)

        self.btn_run = ttk.Button(frame_btn, text="开始执行", command=self.run_task)
        self.btn_run.pack(side="left", padx=(0, 10))

        self.progress = ttk.Progressbar(frame_btn, mode="indeterminate", length=200)
        self.progress.pack(side="left", fill="x", expand=True)

        # --- 输出区域 ---
        frame_output = ttk.LabelFrame(root, text="运行日志", padding=10)
        frame_output.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self.log_text = tk.Text(frame_output, height=10, state="disabled", wrap="word")
        scrollbar = ttk.Scrollbar(frame_output, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("所有文件", "*.*"), ("文本文件", "*.txt")])
        if path:
            self.file_path.set(path)

    def log(self, message):
        """线程安全的日志方法"""
        self.root.after(0, self._append_log, message)

    def _append_log(self, message):
        """实际写入控件，只在主线程执行"""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

        # 超过500行，删除最早的部分
        max_lines = 100
        current_lines = int(self.log_text.index("end-1c").split(".")[0])
        if current_lines > max_lines:
            self.log_text.delete("1.0", f"{current_lines - max_lines}.0")

        self.log_text.configure(state="disabled")

    def run_task(self):
        self.btn_run.configure(state="disabled")
        self.progress.start()
        thread = threading.Thread(target=self._do_work, daemon=True)
        thread.start()

    def _do_work(self):
        import comtypes
        comtypes.CoInitialize()  # 子线程必须初始化 COM
        try:
            self.log(f"文件路径: {self.file_path.get()}")
            self.log(f"参数: {self.param.get()}")
            self.log("开始处理...")

            # ========================================
            # set_volume(0.5, self.log)
            import time
            while True:
                start_time = time.time()
                # --- 重要设置 ---
                # 如果你想测试识别准不准，把这里设为 True (不会乱点鼠标)
                # 如果你要正式挂机运行，把这里设为 False (会截屏并点击)
                # IS_TEST_MODE = False
                IS_TEST_MODE = True
                find_and_click('checkin', self.log, confidence_threshold=0.55)
                run_time = time.time() - start_time
                self.log(f"单次运行耗时: {run_time:.4f} 秒\n")
                time.sleep(5)  # 间隔5秒
            # ========================================
        except Exception as e:
            error_msg = str(e)
            self.log(f"❌ 出错: {error_msg}")
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
            set_volume(0.9, self.log)
            for i in range(2):
                play_mp3("music/close.mp3", self.log, duration=2)
            set_volume(0.2, self.log)
        finally:
            set_volume(0.9, self.log)
            for i in range(2):
                play_mp3("music/close.mp3", self.log, duration=2)
            set_volume(0.2, self.log)
            self.root.after(0, lambda: self.btn_run.configure(state="normal"))
            self.root.after(0, self.progress.stop)
            comtypes.CoUninitialize()  # 用完记得释放


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()