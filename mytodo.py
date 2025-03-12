import csv
import tkinter as tk
from tkinter import ttk, messagebox
from ttkbootstrap import Style
import requests
import os
import ctypes
from datetime import datetime
import random
# 设置样式
style = Style(theme='morph')

# DPI适配
ctypes.windll.shcore.SetProcessDpiAwareness(1)
ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)


class TodoApp:
    def __init__(self, root):
        self.root = root
        self.csv_file = "todos.csv"
        self.base_height = 700
        self.setup_ui()
        self.load_data()
        self.update_time()

    def setup_ui(self):
        self.root.tk.call('tk', 'scaling', ScaleFactor / 75)
        self.root.title("智能待办事项")

        # 初始窗口位置计算
        screen_width = self.root.winfo_screenwidth()
        window_width = 400
        self.pos_x = 1500#screen_width - window_width - 20  # 右边距20像素
        self.pos_y = 20  # 上边距20像素

        self.root.geometry(f"400x{self.base_height}+{self.pos_x}+{self.pos_y}")
        self.root.overrideredirect(True)

        # 自定义字体
        self.normal_font = ('Microsoft YaHei', 11)
        self.strike_font = ('Microsoft YaHei', 11, 'overstrike')

        # 主容器
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 时间显示
        self.time_label = ttk.Label(main_frame, font=('Microsoft YaHei', 12))
        self.time_label.pack(pady=5)

        # 每日一言
        self.yiyan_label = ttk.Label(main_frame, text=self.get_yiyan(),
                                     wraplength=380, justify='center')
        self.yiyan_label.pack(pady=10)

        # 待办事项容器
        self.canvas = tk.Canvas(main_frame, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(main_frame, orient="vertical",
                                       command=self.canvas.yview)
        self.scroll_frame = ttk.Frame(self.canvas)

        # 滚动区域配置
        self.scroll_frame.bind("<Configure>", self.on_scroll_frame_configure)
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # 鼠标滚轮支持
        self.scroll_frame.bind("<Enter>", self._bound_to_mousewheel)
        self.scroll_frame.bind("<Leave>", self._unbound_to_mousewheel)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="新建事项", command=self.new_todo)
        self.context_menu.add_command(label="删除选中", command=self.delete_selected)
        self.context_menu.add_command(label="刷新一言", command=self.refresh_yiyan)
        self.context_menu.add_command(label="保存更改", command=self.save_data)
        self.context_menu.add_command(label="退出", command=self.root.quit)
        self.root.bind("<Button-3>", self.show_context_menu)

    def on_scroll_frame_configure(self, event):
        """自适应窗口高度"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.adjust_window_height()

    def adjust_window_height(self):
        """调整窗口高度并保持右上角位置"""
        content_height = self.scroll_frame.winfo_reqheight()
        max_height = int(self.root.winfo_screenheight() * 0.8)
        new_height = min(content_height + 200, max_height)

        self.root.geometry(f"400x{new_height}+{self.pos_x}+{self.pos_y}")
        self.canvas.configure(height=new_height - 200)

    def update_time(self):
        """更新时间显示"""
        now = datetime.now()
        self.time_label.config(text=now.strftime("%Y-%m-%d %H:%M:%S"))
        self.root.after(1000, self.update_time)

    def _bound_to_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def load_data(self):
        """加载待办事项"""
        self.todos = []
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["completed", "content"])

        try:
            with open(self.csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.todos.append({
                        'completed': row['completed'].lower() == 'true',
                        'content': row['content']
                    })
            self.create_todo_items()
        except Exception as e:
            messagebox.showerror("错误", f"加载失败: {str(e)}")

    def create_todo_items(self):
        """创建事项条目"""
        self.check_vars = []
        self.labels = []

        for todo in self.todos:
            self._create_todo_row(todo)
        self.adjust_window_height()

    def _create_todo_row(self, todo):
        """创建单行事项"""
        frame = ttk.Frame(self.scroll_frame)
        frame.pack(fill='x', pady=2, ipady=3)

        # 复选框
        var = tk.BooleanVar(value=todo['completed'])
        check = ttk.Checkbutton(frame, variable=var,
                                command=lambda v=var: self.toggle_style(v))
        check.pack(side='left', padx=5)
        self.check_vars.append(var)

        # 文本标签
        label = tk.Label(frame, text=todo['content'],
                         font=self.strike_font if var.get() else self.normal_font,
                         anchor='w',
                         fg='#666666' if var.get() else 'black',
                         wraplength=300)
        label.pack(side='left', fill='x', expand=True, padx=5)
        label.bind("<Double-Button-1>", lambda e, l=label: self.edit_label(l))
        self.labels.append(label)

    def toggle_style(self, var):
        """切换删除线样式"""
        index = self.check_vars.index(var)
        label = self.labels[index]
        if var.get():
            label.config(font=self.strike_font, fg='#666666')
        else:
            label.config(font=self.normal_font, fg='black')

    def edit_label(self, label):
        """编辑条目内容"""
        index = self.labels.index(label)
        original_text = label.cget("text")

        entry = ttk.Entry(label.master, font=self.normal_font)
        entry.insert(0, original_text)
        entry.pack(side='left', fill='x', expand=True, padx=5)
        entry.focus_set()

        label.pack_forget()

        def save_edit(event=None):
            new_text = entry.get().strip()
            if new_text:
                label.config(text=new_text)
            entry.destroy()
            label.pack(side='left', fill='x', expand=True, padx=5)
            self.toggle_style(self.check_vars[index])

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", save_edit)

    def get_yiyan(self):
        """获取每日一言"""
        try:
            response = requests.get("https://www.wniui.com/api/yiyan/index.php", timeout=3)
            data = response.json()
            return f"{data['data']}"
        except:
            return "专注当下，成就未来"

    def refresh_yiyan(self):
        self.yiyan_label.config(text=self.get_yiyan())

    def save_data(self, event=None):
        """保存数据到CSV"""
        try:
            with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["completed", "content"])
                for var, label in zip(self.check_vars, self.labels):
                    writer.writerow([str(var.get()).lower(), label.cget("text")])
            messagebox.showinfo("成功", "数据已保存！")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")

    def new_todo(self):
        """新建待办事项"""
        new_todo = {'completed': False, 'content': "新事项"}
        self.todos.append(new_todo)
        self._create_todo_row(new_todo)
        self.canvas.yview_moveto(1)
        self.adjust_window_height()

    def delete_selected(self):
        """删除选中事项"""
        to_delete = [i for i, var in enumerate(self.check_vars) if var.get()]
        for i in reversed(to_delete):
            self.labels[i].master.destroy()
            del self.check_vars[i]
            del self.labels[i]
            del self.todos[i]
        self.save_data()
        self.adjust_window_height()

    def show_context_menu(self, event):
        self.context_menu.tk_popup(event.x_root, event.y_root)


if __name__ == "__main__":
    root = style.master
    app = TodoApp(root)
    root.mainloop()