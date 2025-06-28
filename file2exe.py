import os
import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import random
import string
import subprocess
import threading
import time
import ctypes

def resource_path(relative_path):
    """Get absolute path to resource (for dev and for PyInstaller)"""
    try:
        base_path = sys._MEIPASS  # PyInstaller sets this in a temp dir
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

DEFAULT_ICON_PATH = resource_path(os.path.join("files", "icon.ico"))

def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

class DarkModeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("File to Executable Converter")
        self.geometry("580x340")  # slightly increased height
        self.resizable(False, False)

        # Set dark titlebar (Windows only)
        self.after(10, self.set_dark_titlebar)

        if os.path.isfile(DEFAULT_ICON_PATH):
            try:
                self.iconbitmap(DEFAULT_ICON_PATH)
            except Exception:
                pass

        self.bg_color = "#1e1e1e"
        self.fg_color = "#dddddd"
        self.entry_bg = "#2d2d2d"
        self.btn_bg = "#3a3a3a"
        self.btn_fg = "#e0e0e0"
        self.highlight = "#7158e2"

        self.configure(bg=self.bg_color)

        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TLabel", background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 10))
        style.configure("TButton", background=self.btn_bg, foreground=self.btn_fg, font=("Segoe UI", 10), borderwidth=0, padding=6)
        style.map("TButton", background=[("active", self.highlight)])
        style.configure("TEntry", fieldbackground=self.entry_bg, foreground=self.fg_color, bordercolor=self.highlight, padding=5, font=("Segoe UI", 10))

        padx = 15
        pady = 8

        ttk.Label(self, text="Select file to embed:").grid(row=0, column=0, sticky="w", padx=padx, pady=(pady, 0))
        self.entry_file = ttk.Entry(self, width=50)
        self.entry_file.grid(row=1, column=0, columnspan=2, padx=padx, pady=(0, pady), sticky="ew")
        ttk.Button(self, text="Browse File", command=self.select_file).grid(row=1, column=2, padx=padx, pady=(0, pady))

        ttk.Label(self, text="Select .ico file for EXE icon (optional):").grid(row=2, column=0, sticky="w", padx=padx, pady=(pady, 0))
        self.entry_icon = ttk.Entry(self, width=50)
        self.entry_icon.grid(row=3, column=0, columnspan=2, padx=padx, pady=(0, pady), sticky="ew")
        ttk.Button(self, text="Browse Icon", command=self.select_icon).grid(row=3, column=2, padx=padx, pady=(0, pady))

        ttk.Label(self, text="Output EXE name (without extension):").grid(row=4, column=0, sticky="w", padx=padx, pady=(pady, 0))
        self.entry_name = ttk.Entry(self, width=50)
        self.entry_name.grid(row=5, column=0, columnspan=3, padx=padx, pady=(0, pady*1.5), sticky="ew")

        self.btn_convert = ttk.Button(self, text="Convert to EXE", command=self.start_conversion)
        self.btn_convert.grid(row=6, column=0, columnspan=3, pady=(pady, pady*2))

        self.status_label = ttk.Label(self, text="")
        self.status_label.grid(row=7, column=0, columnspan=3, pady=(0, pady))

        self.grid_columnconfigure(1, weight=1)

        self.anim_running = False

    def set_dark_titlebar(self):
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value))
        except Exception:
            pass

    def select_file(self):
        path = filedialog.askopenfilename(title="Select file to embed")
        if path:
            self.entry_file.delete(0, tk.END)
            self.entry_file.insert(0, path)

    def select_icon(self):
        path = filedialog.askopenfilename(title="Select .ico file", filetypes=[("ICO files", "*.ico")])
        if path:
            self.entry_icon.delete(0, tk.END)
            self.entry_icon.insert(0, path)

    def start_conversion(self):
        self.btn_convert.config(state=tk.DISABLED)
        self.anim_running = True
        threading.Thread(target=self.animate_status, daemon=True).start()
        threading.Thread(target=self.convert_to_exe, daemon=True).start()

    def animate_status(self):
        dots = ""
        while self.anim_running:
            dots = dots + "." if len(dots) < 3 else ""
            if len(dots) > 3:
                dots = ""
            self.status_label.config(text=f"Generating EXE{dots}")
            time.sleep(0.5)

    def convert_to_exe(self):
        file_path = self.entry_file.get().strip()
        icon_path = self.entry_icon.get().strip()
        output_name = self.entry_name.get().strip()

        if not file_path or not os.path.isfile(file_path):
            self.show_error("Please select a valid file to embed.")
            return

        if not icon_path or not os.path.isfile(icon_path) or not icon_path.lower().endswith('.ico'):
            if not os.path.isfile(DEFAULT_ICON_PATH):
                self.show_error(f"Default icon not found at {DEFAULT_ICON_PATH}")
                return
            icon_path = DEFAULT_ICON_PATH

        if not output_name:
            output_name = "output"

        build_dir = "build_dir"
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
        os.mkdir(build_dir)

        with open(file_path, "rb") as f:
            file_bytes = repr(f.read())

        with open(icon_path, "rb") as f:
            icon_bytes = repr(f.read())

        stub_code = f'''
import os
import tempfile
import random
import string
import subprocess
import sys

def random_foldername(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def main():
    temp_dir = tempfile.gettempdir()
    folder = os.path.join(temp_dir, random_foldername())
    os.makedirs(folder, exist_ok=True)

    embedded_file_path = os.path.join(folder, "{os.path.basename(file_path)}")
    file_data = {file_bytes}
    with open(embedded_file_path, "wb") as f:
        f.write(file_data)

    icon_path = os.path.join(folder, "icon.ico")
    icon_data = {icon_bytes}
    with open(icon_path, "wb") as f:
        f.write(icon_data)

    if embedded_file_path.endswith(".py"):
        subprocess.Popen([sys.executable, embedded_file_path])
    else:
        subprocess.Popen([embedded_file_path])

if __name__ == "__main__":
    main()
'''

        stub_path = os.path.join(build_dir, "stub.py")
        with open(stub_path, "w", encoding="utf-8") as f:
            f.write(stub_code)

        command = [
            "pyinstaller",
            "--onefile",
            f"--icon={icon_path}",
            f"--name={output_name}",
            stub_path
        ]

        try:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                self.show_error(f"PyInstaller error:\n{result.stderr}")
                return
        except Exception as e:
            self.show_error(str(e))
            return

        dist_path = os.path.join("dist", output_name + ".exe")
        output_folder = "output"
        os.makedirs(output_folder, exist_ok=True)
        shutil.move(dist_path, os.path.join(output_folder, output_name + ".exe"))

        for folder in ["build", "dist", build_dir]:
            if os.path.exists(folder):
                shutil.rmtree(folder)
        spec_file = output_name + ".spec"
        if os.path.exists(spec_file):
            os.remove(spec_file)

        self.anim_running = False
        self.status_label.config(text="Generation complete!")
        self.btn_convert.config(state=tk.NORMAL)
        messagebox.showinfo("Success", f"EXE created in the '{output_folder}' folder.")

    def show_error(self, msg):
        self.anim_running = False
        self.status_label.config(text="")
        self.btn_convert.config(state=tk.NORMAL)
        messagebox.showerror("Error", msg)

if __name__ == "__main__":
    app = DarkModeApp()
    app.mainloop()
