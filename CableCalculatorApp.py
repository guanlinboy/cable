import tkinter as tk
from tkinter import ttk, messagebox
import math


class CableCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("电缆装盘长度计算器")
        self.root.geometry("500x450")

        # 输入参数配置
        self.params = {
            "d1": {"label": "侧板直径 (d1/mm)", "default": "2000"},
            "d2": {"label": "筒体直径 (d2/mm)", "default": "1000"},
            "l2": {"label": "内宽 (l2/mm)", "default": "500"},
            "D": {"label": "线缆外径 (D/mm)", "default": "50"},
            "t": {"label": "装盘余量 (t/mm)", "default": "1"}
        }

        # 创建界面组件
        self.create_widgets()

    def create_widgets(self):
        # 输入区域
        input_frame = ttk.LabelFrame(self.root, text="参数输入")
        input_frame.pack(pady=10, padx=15, fill="x")

        self.entries = {}
        for i, (key, config) in enumerate(self.params.items()):
            ttk.Label(input_frame, text=config["label"]).grid(row=i, column=0, padx=5, pady=5, sticky="w")
            entry = ttk.Entry(input_frame)
            entry.insert(0, config["default"])
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            self.entries[key] = entry

        # 按钮区域
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="计算", command=self.calculate).pack(side=tk.LEFT, padx=5)

        # 结果显示
        result_frame = ttk.LabelFrame(self.root, text="计算结果")
        result_frame.pack(pady=10, padx=15, fill="x")

        self.results = {
            "P": {"label": "卷缆层数 (P):", "row": 0},
            "n": {"label": "每层圈数 (n):", "row": 1},
            "L": {"label": "装盘长度 (L):", "row": 2}
        }

        for key, config in self.results.items():
            ttk.Label(result_frame, text=config["label"]).grid(
                row=config["row"], column=0, padx=5, pady=5, sticky="w")
            label = ttk.Label(result_frame, text="", foreground="blue")
            label.grid(row=config["row"], column=1, padx=5, pady=5, sticky="e")
            self.results[key]["widget"] = label

    def get_float_input(self, key):
        """安全获取浮点数值"""
        try:
            return float(self.entries[key].get())
        except ValueError:
            messagebox.showerror("输入错误", f"{self.params[key]['label']} 必须为数字")
            self.entries[key].focus_set()
            raise

    def calculate(self):
        try:
            # 获取输入值
            d1 = self.get_float_input("d1")
            d2 = self.get_float_input("d2")
            l2 = self.get_float_input("l2")
            D = self.get_float_input("D")
            t = self.get_float_input("t")

            # 参数验证
            if any(v <= 0 for v in [d1, d2, l2, D, t]):
                raise ValueError("所有参数必须为正数")
            if d1 <= d2:
                raise ValueError("侧板直径(d1)必须大于筒体直径(d2)")

            # 计算卷缆层数
            P_numerator = d1 - d2 - 2 * t - 0.2 * D
            if P_numerator < 0:
                raise ValueError("有效空间不足，无法缠绕电缆")
            P = math.floor(P_numerator / (1.8 * D))
            if P <= 0:
                raise ValueError("无法缠绕至少一层电缆")

            # 计算每层圈数
            n = math.floor(0.95 * l2 / D)

            # 计算总长度
            avg_diameter = d2 + 0.1 * D + 0.9 * D * P
            L = (math.pi * P * n * avg_diameter) / 1000

            # 显示结果
            self.results["P"]["widget"].config(text=f"{P} 层")
            self.results["n"]["widget"].config(text=f"{n} 圈")
            self.results["L"]["widget"].config(text=f"{round(L, 2)} 米")

        except ValueError as e:
            messagebox.showerror("计算错误", str(e))
        except Exception as e:
            messagebox.showerror("系统错误", f"发生意外错误: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CableCalculatorApp(root)
    root.mainloop()
