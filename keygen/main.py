import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
# from real_handle_onnx import find_and_click, play_mp3, set_volume
from license_manager import check_license, save_license, verify_license, get_machine_code


class LicenseDialog:
    """授权码输入弹窗"""
    def __init__(self, parent, machine_code):
        self.result = False
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("软件授权")
        self.dialog.geometry("450x280")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()
        self.dialog.attributes('-topmost', True)

        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - 450) // 2
        y = (self.dialog.winfo_screenheight() - 280) // 2
        self.dialog.geometry(f"+{x}+{y}")

        self.machine_code = machine_code

        # 标题
        ttk.Label(self.dialog, text="软件尚未授权", font=("微软雅黑", 14, "bold")).pack(pady=(15, 5))

        # 说明
        ttk.Label(self.dialog, text="请将以下机器码发送给开发者获取授权码",
                  font=("微软雅黑", 9)).pack()

        # 机器码显示
        frame_mc = ttk.Frame(self.dialog)
        frame_mc.pack(fill="x", padx=30, pady=(10, 5))
        ttk.Label(frame_mc, text="机器码：").pack(side="left")
        mc_entry = ttk.Entry(frame_mc, width=30)
        mc_entry.insert(0, machine_code)
        mc_entry.configure(state="readonly")
        mc_entry.pack(side="left", padx=5)
        ttk.Button(frame_mc, text="复制", command=lambda: self._copy(machine_code)).pack(side="left")

        # 授权码输入
        frame_lk = ttk.Frame(self.dialog)
        frame_lk.pack(fill="x", padx=30, pady=5)
        ttk.Label(frame_lk, text="授权码：").pack(side="left")
        self.license_var = tk.StringVar()
        ttk.Entry(frame_lk, textvariable=self.license_var, width=30).pack(side="left", padx=5)

        # 按钮
        frame_btn = ttk.Frame(self.dialog)
        frame_btn.pack(pady=15)
        ttk.Button(frame_btn, text="激活", command=self._activate, width=12).pack(side="left", padx=10)
        ttk.Button(frame_btn, text="退出", command=self._quit, width=12).pack(side="left", padx=10)

        # 关闭窗口等同退出
        self.dialog.protocol("WM_DELETE_WINDOW", self._quit)

    def _copy(self, text):
        self.dialog.clipboard_clear()
        self.dialog.clipboard_append(text)
        messagebox.showinfo("提示", "机器码已复制到剪贴板", parent=self.dialog)

    def _activate(self):
        license_key = self.license_var.get().strip()
        if not license_key:
            messagebox.showwarning("提示", "请输入授权码", parent=self.dialog)
            return
        if verify_license(self.machine_code, license_key):
            save_license(license_key)
            messagebox.showinfo("成功", "授权成功！", parent=self.dialog)
            self.result = True
            self.dialog.destroy()
        else:
            messagebox.showerror("失败", "授权码无效，请检查后重试", parent=self.dialog)

    def _quit(self):
        self.result = False
        self.dialog.destroy()


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("腾讯会议签到工具")
        root.attributes('-topmost', True)

        # 窗口位置：左下方
        win_width = 400
        win_height = 450
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = 20
        y = screen_height - win_height - 120
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
        self.root.after(0, self._append_log, message)

    def _append_log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

        max_lines = 500
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
        comtypes.CoInitialize()
        try:
            self.log(f"文件路径: {self.file_path.get()}")
            self.log(f"参数: {self.param.get()}")
            self.log("开始处理...")

            import time
            while True:
                start_time = time.time()
                IS_TEST_MODE = True
                # find_and_click('checkin', self.log, confidence_threshold=0.55)
                run_time = time.time() - start_time
                self.log(f"单次运行耗时: {run_time:.4f} 秒\n")
                time.sleep(5)

        except Exception as e:
            error_msg = str(e)
            self.log(f"❌ 出错: {error_msg}")
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
            # set_volume(0.9, self.log)
            # for i in range(2):
                # play_mp3("music/close.mp3", self.log, duration=2)
            # set_volume(0.2, self.log)
        finally:
            # set_volume(0.9, self.log)
            # for i in range(2):
                # play_mp3("music/close.mp3", self.log, duration=2)
            # set_volume(0.2, self.log)
            self.root.after(0, lambda: self.btn_run.configure(state="normal"))
            self.root.after(0, self.progress.stop)
            comtypes.CoUninitialize()


if __name__ == "__main__":
    root = tk.Tk()

    # ===== 授权验证 =====
    is_licensed, machine_code = check_license()
    if not is_licensed:
        root.withdraw()  # 先隐藏主窗口
        dialog = LicenseDialog(root, machine_code)
        root.wait_window(dialog.dialog)
        if not dialog.result:
            root.destroy()
            exit()
        root.deiconify()  # 授权成功，显示主窗口

    app = App(root)
    root.mainloop()