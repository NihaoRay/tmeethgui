import tkinter as tk
from tkinter import ttk, messagebox
import threading
from PIL import Image, ImageTk
# import numpy as np
from real_handle_onnx import find_and_click, play_mp3, set_volume
from license_manager import check_license, save_license, verify_license, get_machine_code
import sys

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

        # --- 图像显示区域（替代原输入区域）---
        frame_image = ttk.LabelFrame(root, text="识别画面", padding=5)
        frame_image.pack(fill="x", padx=10, pady=(10, 5))

        self.image_label = tk.Label(frame_image, bg="#2d2d2d")
        self.image_label.pack()

        # 初始占位图（深灰色）
        placeholder = Image.new('RGB', (370, 160), color=(45, 45, 45))
        self._photo = ImageTk.PhotoImage(placeholder)
        self.image_label.configure(image=self._photo)

        # --- 按钮区域 ---
        frame_btn = ttk.Frame(root)
        frame_btn.pack(fill="x", padx=10, pady=5)

        self.btn_run = ttk.Button(frame_btn, text="开始执行", command=self.run_task)
        self.btn_run.pack(side="left", padx=(0, 10))

        self.progress = ttk.Progressbar(frame_btn, mode="indeterminate", length=200)
        self.progress.pack(side="left", fill="x", expand=True)

        # ✅ 声明放这里，在主内容区之前，用 side="bottom"
        frame_notice = ttk.Frame(root)
        frame_notice.pack(side="bottom", fill="x", padx=10, pady=(0, 8))
        notice_text = (
            "声明:本工具仅进行本地图像识别，绝不传输或收集任何用户数据。"
        )
        ttk.Label(
            frame_notice,
            text=notice_text,
            foreground="red",
            font=("Microsoft YaHei", 8),
            anchor="center",
            wraplength=600
        ).pack(fill="x")

        # --- 输出区域 ---
        frame_output = ttk.LabelFrame(root, text="运行日志", padding=10)
        frame_output.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self.log_text = tk.Text(frame_output, height=8, state="disabled", wrap="word")
        scrollbar = ttk.Scrollbar(frame_output, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.running = False
        root.protocol("WM_DELETE_WINDOW", self._on_close)


    def update_image(self, img_np):
        """线程安全地更新识别画面（从子线程调用）"""
        if not self.running:
            return
        self.root.after(0, self._set_image, img_np)

    def _set_image(self, img_np):
        """在主线程中将 numpy 数组转为 PhotoImage 并显示"""
        pil_img = Image.fromarray(img_np)

        # 等比缩放，最大 370x160
        max_w, max_h = 370, 160
        ratio = min(max_w / pil_img.width, max_h / pil_img.height)
        new_w = int(pil_img.width * ratio)
        new_h = int(pil_img.height * ratio)
        pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)

        new_photo = ImageTk.PhotoImage(pil_img)
        self.image_label.configure(image=new_photo)
        self._photo = new_photo  # 旧引用自然被替换，由 GC 回收
        pil_img.close()

    def log(self, message):
        if not self.running:
            return
        self.root.after(0, self._append_log, message)

    def _append_log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

        max_lines = 50 #最大日志缓存数量
        current_lines = int(self.log_text.index("end-1c").split(".")[0])
        if current_lines > max_lines:
            self.log_text.delete("1.0", f"{current_lines - max_lines}.0")

        self.log_text.configure(state="disabled")

    def run_task(self):
        self.running = True  # 加这行
        self.btn_run.configure(state="disabled")
        self.progress.start()
        thread = threading.Thread(target=self._do_work, daemon=True)
        thread.start()

    def _on_close(self):
        self.running = False
        self.root.after(500, self.root.destroy)

    def _do_work(self):
        import comtypes
        comtypes.CoInitialize()
        try:
            self.log("开始处理...")

            import time
            while True:
                start_time = time.time()
                find_and_click({'jiaru', 'checkin'}, self.log, confidence_threshold=0.55,
                               img_callback=self.update_image)
                run_time = time.time() - start_time
                self.log(f"单次运行耗时: {run_time:.4f} 秒\n")
                time.sleep(5)

        except Exception as e:
            error_msg = str(e)
            self.log(f"❌ 出错: {error_msg}")
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
            set_volume(0.9, self.log)
            for i in range(2):
                play_mp3("music/close.mp3", self.log, duration=2)
            set_volume(0.2, self.log)
        finally:
            self.running = False
            self.root.after(0, lambda: self.btn_run.configure(state="normal"))
            self.root.after(0, self.progress.stop)

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
            sys.exit()
        root.deiconify()  # 授权成功，显示主窗口

    app = App(root)
    root.mainloop()