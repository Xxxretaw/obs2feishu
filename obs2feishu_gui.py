"""
obs2feishu GUI — Obsidian Markdown → 飞书 HTML 可视化转换工具
"""
import ctypes
import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
from pathlib import Path

# ── Windows 高 DPI 适配（必须在创建任何窗口之前调用）──
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from obs2feishu import md_to_html


# ─────────────────────────── 颜色 / 常量 ───────────────────────────
BG        = "#f4f4f4"
PANEL     = "#ffffff"
ACCENT    = "#5c7a9e"
ACCENT_HV = "#7294b8"
FG        = "#2c2c2c"
FG_DIM    = "#9e9e9e"
FG_LABEL  = "#555555"
SUCCESS   = "#4e7e4e"
WARNING   = "#8f6a20"
ERROR     = "#9e3a3a"
BORDER    = "#e0e0e0"
GREEN     = "#4e7e4e"
GREEN_HV  = "#5f985f"
LOG_BG    = "#fafafa"
LOG_FG    = "#333333"
FONT_UI   = ("Segoe UI", 11)
FONT_MONO = ("Consolas", 10)


class DirRow(tk.Frame):
    """目录选择行：标签 + 输入框 + 浏览按钮"""
    def __init__(self, parent, label: str, **kw):
        super().__init__(parent, bg=PANEL, **kw)

        tk.Label(self, text=label, font=FONT_UI, bg=PANEL, fg=FG_LABEL,
                 width=14, anchor="w").pack(side="left")

        self.var = tk.StringVar()
        tk.Entry(self, textvariable=self.var, font=FONT_UI,
                 bg=BG, fg=FG, insertbackground=FG,
                 relief="flat", bd=0, highlightthickness=1,
                 highlightbackground=BORDER,
                 highlightcolor=ACCENT).pack(side="left", fill="x",
                                             expand=True, ipady=5)

        tk.Button(self, text="浏览…", font=FONT_UI,
                  bg=ACCENT, fg="white", relief="flat",
                  activebackground=ACCENT_HV, activeforeground="white",
                  cursor="hand2", padx=10,
                  command=self._browse).pack(side="left", padx=(6, 0))

    def _browse(self):
        path = filedialog.askdirectory(title="选择文件夹")
        if path:
            self.var.set(path)

    def get(self) -> str:
        return self.var.get().strip()

    def set(self, value: str):
        self.var.set(value)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("obs2feishu — Obsidian → 飞书转换工具")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(800, 600)
        self._selected_files: list[Path] = []
        self._last_outputs:   list[Path] = []
        self._build_ui()
        self._center()

    # ─────────────────────── 布局构建 ───────────────────────
    def _build_ui(self):
        # ── 顶部标题栏 ──
        header = tk.Frame(self, bg=ACCENT, padx=24, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="obs2feishu", font=("Segoe UI", 16, "bold"),
                 bg=ACCENT, fg="white").pack(side="left")
        tk.Label(header, text="Obsidian Markdown → 飞书 HTML",
                 font=("Segoe UI", 11), bg=ACCENT, fg="#c8d8e8").pack(
                     side="left", padx=(14, 0))

        # ── 主体区域 ──
        body = tk.Frame(self, bg=BG, padx=24, pady=18)
        body.pack(fill="both", expand=True)

        # ── 路径设置区 ──
        paths_frame = tk.LabelFrame(body, text="  路径设置  ", font=FONT_UI,
                                    bg=PANEL, fg=FG_DIM, bd=1,
                                    relief="solid", padx=18, pady=14)
        paths_frame.pack(fill="x", pady=(0, 14))

        # 输入文件行（支持多选）
        file_row = tk.Frame(paths_frame, bg=PANEL)
        file_row.pack(fill="x", pady=(0, 10))

        tk.Label(file_row, text="输入文件:", font=FONT_UI, bg=PANEL,
                 fg=FG_LABEL, width=14, anchor="w").pack(side="left")

        self.file_label_var = tk.StringVar(value="未选择")
        tk.Label(file_row, textvariable=self.file_label_var,
                 font=FONT_UI, bg=BG, fg=FG,
                 anchor="w", padx=8,
                 highlightthickness=1, highlightbackground=BORDER).pack(
                     side="left", fill="x", expand=True, ipady=5)

        tk.Button(file_row, text="选择文件…", font=FONT_UI,
                  bg=ACCENT, fg="white", relief="flat",
                  activebackground=ACCENT_HV, activeforeground="white",
                  cursor="hand2", padx=10,
                  command=self._pick_files).pack(side="left", padx=(6, 0))

        self.vault_row = DirRow(paths_frame, "Vault 根目录:")
        self.vault_row.set(r"D:\Note_obsidian")
        self.vault_row.pack(fill="x", pady=(0, 10))

        self.output_row = DirRow(paths_frame, "输出目录:")
        self.output_row.pack(fill="x")

        # ── 转换按钮 + 进度条 ──
        ctrl_frame = tk.Frame(body, bg=BG)
        ctrl_frame.pack(fill="x", pady=(0, 10))

        self.convert_btn = tk.Button(
            ctrl_frame, text="▶  开始转换", font=("Segoe UI", 12, "bold"),
            bg=ACCENT, fg="white", relief="flat",
            activebackground=ACCENT_HV, activeforeground="white",
            cursor="hand2", padx=22, pady=8,
            command=self._start_convert)
        self.convert_btn.pack(side="left")

        self.progress = ttk.Progressbar(ctrl_frame, mode="indeterminate",
                                        length=200)
        self.progress.pack(side="left", padx=(16, 0))

        self.status_var = tk.StringVar(value="就绪")
        tk.Label(ctrl_frame, textvariable=self.status_var, font=FONT_UI,
                 bg=BG, fg=FG_DIM).pack(side="left", padx=(14, 0))

        # ── 转换完成后的操作按钮（始终占位，内容隐藏/显示）──
        self.result_frame = tk.Frame(body, bg=BG)
        # 先不 pack，转换完成后插入到 log_frame 之前

        tk.Label(self.result_frame, text="转换完成：",
                 font=FONT_UI, bg=BG, fg=FG_DIM).pack(side="left")

        self.open_file_btn = tk.Button(
            self.result_frame, text="📄 打开文件",
            font=FONT_UI, bg=GREEN, fg="white", relief="flat",
            activebackground=GREEN_HV, activeforeground="white",
            cursor="hand2", padx=14, pady=5,
            command=self._open_files)
        self.open_file_btn.pack(side="left", padx=(8, 6))

        tk.Button(
            self.result_frame, text="📁 打开所在目录",
            font=FONT_UI, bg="#595959", fg="white", relief="flat",
            activebackground="#7a7a7a", activeforeground="white",
            cursor="hand2", padx=14, pady=5,
            command=self._open_folder).pack(side="left")

        # ── 日志区域 ──
        self.log_frame = tk.LabelFrame(body, text="  转换日志  ", font=FONT_UI,
                                       bg=PANEL, fg=FG_DIM, bd=1, relief="solid")
        self.log_frame.pack(fill="both", expand=True)

        self.log = scrolledtext.ScrolledText(
            self.log_frame, font=FONT_MONO, bg=LOG_BG, fg=LOG_FG,
            insertbackground=FG, relief="flat", bd=0,
            wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True, padx=2, pady=2)

        self.log.tag_config("success", foreground=SUCCESS)
        self.log.tag_config("warning", foreground=WARNING)
        self.log.tag_config("error",   foreground=ERROR)
        self.log.tag_config("dim",     foreground=FG_DIM)
        self.log.tag_config("accent",  foreground=ACCENT)

    # ─────────────────────── 逻辑 ───────────────────────
    def _center(self):
        self.update_idletasks()
        w, h = 920, 680
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _pick_files(self):
        paths = filedialog.askopenfilenames(
            title="选择 Markdown 文件（可多选）",
            filetypes=[("Markdown 文件", "*.md"), ("所有文件", "*.*")])
        if not paths:
            return
        self._selected_files = [Path(p) for p in paths]
        count = len(self._selected_files)
        if count == 1:
            self.file_label_var.set(self._selected_files[0].name)
        else:
            self.file_label_var.set(f"已选择 {count} 个文件")
        self._hide_result_buttons()

    def _log(self, msg: str, tag: str = ""):
        self.log.after(0, self._append_log, msg, tag)

    def _append_log(self, msg: str, tag: str):
        self.log.config(state="normal")
        if tag:
            self.log.insert("end", msg + "\n", tag)
        else:
            self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def _set_status(self, text: str):
        self.after(0, self.status_var.set, text)

    def _show_result_buttons(self, outputs: list):
        self._last_outputs = [Path(p) for p in outputs if p]
        if not self._last_outputs:
            return
        self.result_frame.pack(fill="x", pady=(0, 8),
                               before=self.log_frame)

    def _hide_result_buttons(self):
        self.result_frame.pack_forget()
        self._last_outputs = []

    def _open_files(self):
        for p in self._last_outputs:
            os.startfile(str(p))

    def _open_folder(self):
        if not self._last_outputs:
            return
        subprocess.Popen(["explorer", str(self._last_outputs[0].parent)])

    def _start_convert(self):
        if not self._selected_files:
            self._log("❌ 请先选择要转换的 Markdown 文件。", "error")
            return
        vault_root = self.vault_row.get()
        if not vault_root:
            self._log("❌ 请先选择 Vault 根目录。", "error")
            return
        output_dir = self.output_row.get() or None

        self._hide_result_buttons()
        self.convert_btn.config(state="disabled")
        self.progress.start(12)
        self._set_status("转换中…")

        threading.Thread(
            target=self._run_convert,
            args=(list(self._selected_files), vault_root, output_dir),
            daemon=True).start()

    def _run_convert(self, files: list, vault_root: str, output_dir):
        outputs = []
        try:
            self._log(f"\n{'─'*52}", "dim")
            self._log(f"开始转换，共 {len(files)} 个文件", "accent")
            self._log(f"Vault 根目录: {vault_root}", "dim")
            if output_dir:
                self._log(f"输出目录: {output_dir}", "dim")
            self._log(f"{'─'*52}\n", "dim")

            success, failed = 0, 0
            log_fn = self._make_log_fn()
            for f in files:
                result = md_to_html(f, vault_root,
                                    output_dir=output_dir,
                                    log_fn=log_fn)
                if result:
                    outputs.append(result)
                    success += 1
                else:
                    failed += 1

            self._log(f"\n{'─'*52}", "dim")
            if failed:
                self._log(f"完成！成功 {success} 个，失败 {failed} 个", "warning")
            else:
                self._log(f"完成！成功 {success} 个", "success")
            self._log(f"{'─'*52}\n", "dim")
            self._set_status(f"完成 ({success}/{success+failed})")

        except Exception as e:
            self._log(f"\n❌ 发生错误: {e}", "error")
            self._set_status("出错")
        finally:
            self.after(0, self._reset_ui, outputs)

    def _make_log_fn(self):
        def log_fn(msg: str):
            if "✅" in msg:
                tag = "success"
            elif "⚠️" in msg:
                tag = "warning"
            elif "❌" in msg:
                tag = "error"
            elif msg.startswith("  "):
                tag = "dim"
            else:
                tag = ""
            self._log(msg, tag)
        return log_fn

    def _reset_ui(self, outputs: list):
        self.progress.stop()
        self.convert_btn.config(state="normal")
        if outputs:
            self._show_result_buttons(outputs)


if __name__ == "__main__":
    app = App()
    app.mainloop()
